"""Market resolution checking service.

Checks Polymarket API for market resolution status and updates run documents.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.core.logging_config import get_logger
from app.core.polymarket_utils import fetch_json_async, GAMMA_API
from app.db.async_repositories import (
    get_run_async,
    get_runs_pending_resolution,
    update_run_resolution,
)
from app.db.models import Resolution

logger = get_logger(__name__)


def _utc_now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_outcome_prices(outcome_prices: Any) -> tuple[float, float] | None:
    """Parse outcomePrices from Polymarket API response.
    
    Returns (yes_price, no_price) tuple or None if parsing fails.
    """
    if not outcome_prices:
        return None
    
    # Handle list format
    if isinstance(outcome_prices, list) and len(outcome_prices) >= 2:
        try:
            return float(outcome_prices[0]), float(outcome_prices[1])
        except (ValueError, TypeError):
            return None
    
    # Handle JSON string format
    if isinstance(outcome_prices, str):
        try:
            arr = json.loads(outcome_prices)
            if isinstance(arr, list) and len(arr) >= 2:
                return float(arr[0]), float(arr[1])
        except (json.JSONDecodeError, ValueError, TypeError):
            return None
    
    return None


def _determine_resolution_status(
    closed: bool,
    yes_price: float,
    no_price: float,
) -> tuple[str, str | None]:
    """Determine resolution status and winning outcome from prices.
    
    Returns (status, winning_outcome) tuple.
    """
    if not closed:
        return "pending", None
    
    # Check for clear resolution (1.0 and 0.0 prices)
    if yes_price >= 0.99 and no_price <= 0.01:
        return "resolved_yes", "Yes"
    elif no_price >= 0.99 and yes_price <= 0.01:
        return "resolved_no", "No"
    elif yes_price < 0.01 and no_price < 0.01:
        # Both prices near zero might indicate voided market
        return "voided", None
    else:
        # Market closed but prices don't indicate clear resolution
        return "unknown", None


async def _fetch_market_data(slug: str, market_question: str | None = None) -> dict[str, Any] | None:
    """Try to fetch market data, first from markets endpoint, then from events endpoint."""
    # Try markets endpoint first
    markets_raw = await fetch_json_async(f"{GAMMA_API}/markets", params={"slug": slug})
    
    if markets_raw:
        if isinstance(markets_raw, list) and markets_raw:
            return markets_raw[0]
        elif isinstance(markets_raw, dict):
            return markets_raw
    
    # Try events endpoint (for event slugs that contain markets)
    events_raw = await fetch_json_async(f"{GAMMA_API}/events", params={"slug": slug})
    
    if events_raw:
        if isinstance(events_raw, list) and events_raw:
            event = events_raw[0]
            markets = event.get("markets", [])
            if markets:
                return _find_matching_market(markets, market_question)
        elif isinstance(events_raw, dict):
            markets = events_raw.get("markets", [])
            if markets:
                return _find_matching_market(markets, market_question)
    
    return None


def _find_matching_market(markets: list[dict], market_question: str | None) -> dict[str, Any] | None:
    """Find the best matching market from a list of markets.
    
    If market_question is provided, try to match by question.
    Otherwise, return the first closed market, or first market if none closed.
    """
    if not markets:
        return None
    
    # If we have a question, try to find a matching market
    if market_question:
        question_lower = market_question.lower()
        for m in markets:
            m_question = (m.get("question") or m.get("groupItemTitle") or "").lower()
            if question_lower in m_question or m_question in question_lower:
                return m
    
    # Fallback: return the first closed market, or first market
    for m in markets:
        if m.get("closed"):
            return m
    return markets[0]


async def fetch_market_resolution(slug: str, market_question: str | None = None) -> Resolution | None:
    """Fetch current market status from Polymarket and determine resolution.
    
    Args:
        slug: Market or event slug to check
        market_question: Optional question to match specific market in multi-market events
        
    Returns:
        Resolution dict if market data found, None otherwise
    """
    try:
        market = await _fetch_market_data(slug, market_question)
        
        if not market:
            logger.warning("No market data returned", slug=slug)
            return None
        
        # Extract fields
        closed = market.get("closed", False)
        outcome_prices = market.get("outcomePrices")
        
        prices = _parse_outcome_prices(outcome_prices)
        if prices is None:
            logger.warning("Could not parse outcome prices", slug=slug, outcome_prices=outcome_prices)
            # Return pending if we can't determine prices
            return {
                "status": "pending" if not closed else "unknown",
                "checked_at": _utc_now_iso(),
            }
        
        yes_price, no_price = prices
        status, winning_outcome = _determine_resolution_status(closed, yes_price, no_price)
        
        resolution: Resolution = {
            "status": status,
            "final_yes_price": yes_price,
            "final_no_price": no_price,
            "checked_at": _utc_now_iso(),
        }
        
        if winning_outcome:
            resolution["winning_outcome"] = winning_outcome
        
        if status in ("resolved_yes", "resolved_no", "voided"):
            resolution["resolved_at"] = _utc_now_iso()
        
        logger.info(
            "Market resolution fetched",
            slug=slug,
            status=status,
            winning_outcome=winning_outcome,
            yes_price=yes_price,
            no_price=no_price,
        )
        
        return resolution
        
    except Exception as e:
        logger.error("Failed to fetch market resolution", slug=slug, error=str(e), exc_info=True)
        return None


async def check_and_update_run_resolution(run_id: str) -> Resolution | None:
    """Check resolution for a single run and update database.
    
    Args:
        run_id: Run ID to check
        
    Returns:
        Resolution dict if updated, None if run not found or already resolved
    """
    # Get run from DB
    run = await get_run_async(run_id)
    if not run:
        logger.warning("Run not found for resolution check", run_id=run_id)
        return None
    
    # Check if already resolved
    existing_resolution = run.get("resolution", {})
    existing_status = existing_resolution.get("status")
    if existing_status in ("resolved_yes", "resolved_no", "voided"):
        logger.debug("Run already resolved, skipping", run_id=run_id, status=existing_status)
        return existing_resolution
    
    # Get slug from run - prefer selected_market_slug for multi-market events
    # The run.slug might be the event slug, but we need the specific market slug
    slug = (
        run.get("selected_market_slug")
        or run.get("market_snapshot", {}).get("slug")
        or run.get("slug")
    )
    if not slug or slug == "pending":
        logger.warning("Run has no valid slug", run_id=run_id, slug=slug)
        return None
    
    # Get market question to help identify correct market in multi-market events
    market_question = run.get("market_snapshot", {}).get("question")
    
    logger.debug("Checking resolution for slug", run_id=run_id, slug=slug, question=market_question)
    
    # Fetch resolution from Polymarket
    resolution = await fetch_market_resolution(slug, market_question=market_question)
    if not resolution:
        return None
    
    # Update run document
    success = await update_run_resolution(run_id, resolution)
    if success:
        logger.info("Run resolution updated", run_id=run_id, status=resolution.get("status"))
        return resolution
    else:
        logger.warning("Failed to update run resolution", run_id=run_id)
        return None


async def check_pending_resolutions(limit: int = 50) -> dict[str, Any]:
    """Check resolutions for runs that are past their end_date but not resolved.
    
    Args:
        limit: Maximum number of runs to check
        
    Returns:
        Summary dict with checked count and updated count
    """
    # Get runs needing resolution check
    pending_runs = await get_runs_pending_resolution(limit=limit)
    
    checked = 0
    updated = 0
    errors = 0
    
    for run in pending_runs:
        run_id = run.get("run_id")
        if not run_id:
            continue
        
        checked += 1
        try:
            resolution = await check_and_update_run_resolution(run_id)
            if resolution and resolution.get("status") in ("resolved_yes", "resolved_no", "voided"):
                updated += 1
        except Exception as e:
            logger.error("Error checking resolution", run_id=run_id, error=str(e))
            errors += 1
    
    logger.info(
        "Resolution check complete",
        checked=checked,
        updated=updated,
        errors=errors,
    )
    
    return {
        "checked": checked,
        "updated": updated,
        "errors": errors,
    }
