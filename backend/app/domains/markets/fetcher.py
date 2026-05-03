# app/domains/markets/fetcher.py
"""Polymarket event and market fetching with caching and error handling."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from aiohttp import ClientTimeout

from app.config import get_logger
from app.domains.markets.schemas import Event, Market

logger = get_logger(__name__)

# Polymarket API endpoints (keeping inline since PolymarketAPI class removed)
GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


async def _fetch_json(
    url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10
) -> Any:
    """Fetch JSON from URL with basic error handling."""
    logger.debug("Fetching JSON", url=url, params=params)
    timeout_obj = ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_obj) as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()


def _normalize_number(v: Any) -> Optional[float]:
    """Normalize a value to float."""
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        return float(str(v))
    except Exception:
        return None


async def fetch_order_book_async(token_id: str) -> Dict[str, Any]:
    """Fetch order book with basic error handling."""
    try:
        data = await _fetch_json(f"{CLOB_API}/book", params={"token_id": token_id})

        def map_levels(levels: List[Dict[str, Any]]) -> List[Dict[str, float]]:
            out: List[Dict[str, float]] = []
            for lvl in levels or []:
                p = _normalize_number(lvl.get("price"))
                s = _normalize_number(lvl.get("size"))
                if p is not None and s is not None:
                    out.append({"price": p, "size": s})
            return out

        bids = map_levels(data.get("bids", []))
        asks = map_levels(data.get("asks", []))
        best_bid = bids[0]["price"] if bids else None
        best_ask = asks[0]["price"] if asks else None
        return {"bids": bids, "asks": asks, "best_bid": best_bid, "best_ask": best_ask}
    except Exception as e:
        logger.warning("Failed to fetch order book", token_id=token_id, error=str(e))
        return {"bids": [], "asks": [], "best_bid": None, "best_ask": None}


def _extract_series_comment_count(event_data: Dict[str, Any]) -> Optional[int]:
    """Extract comment count from series data if available."""
    series = event_data.get("series")
    if isinstance(series, list) and series:
        first = series[0]
        if isinstance(first, dict):
            return first.get("commentCount")
    return None


async def get_event_and_markets_by_slug(
    slug: str,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Get event and markets by slug with caching and error handling (async).

    Always tries events endpoint first to get accurate event-level data like commentCount,
    then falls back to markets endpoint if needed.

    Uses Pydantic models for type-safe deserialization.
    """
    try:
        # Try events endpoint first - it has accurate event-level data like commentCount
        events_raw = await _fetch_json(f"{GAMMA_API}/events", params={"slug": slug})

        # Handle both array response and dict with "data" key
        if isinstance(events_raw, dict):
            events_list = events_raw.get("data", [])
        elif isinstance(events_raw, list):
            events_list = events_raw
        else:
            events_list = []

        # Log what we got from events endpoint
        logger.debug(
            "Events API response",
            slug=slug,
            events_type=type(events_raw).__name__,
            events_count=len(events_list) if isinstance(events_list, list) else 0,
            has_events=bool(events_list and len(events_list) > 0),
        )

        if events_list and len(events_list) > 0:
            event_raw = events_list[0] if isinstance(events_list[0], dict) else {}
            # Deserialize using Pydantic model for type safety and validation
            try:
                event_model = Event.model_validate(events_list[0])
                logger.debug("Pydantic validation succeeded", slug=slug)
            except Exception as e:
                logger.warning(
                    "Failed to deserialize event with Pydantic, using raw data",
                    slug=slug,
                    error=str(e),
                    error_type=type(e).__name__,
                    event_keys=(
                        list(events_list[0].keys())[:10]
                        if isinstance(events_list[0], dict)
                        else "not_dict"
                    ),
                    commentCount_in_raw=(
                        events_list[0].get("commentCount")
                        if isinstance(events_list[0], dict)
                        else None
                    ),
                )
                # Fallback to raw dict if Pydantic validation fails
                event_model = None

            if event_model:
                # Use validated Pydantic model
                event_markets = (
                    [m.model_dump() for m in event_model.markets] if event_model.markets else []
                )
                comment_count = event_model.commentCount
                series_comment_count = _extract_series_comment_count(event_raw)

                logger.info(
                    "Fetched event from /events endpoint (Pydantic validated)",
                    slug=slug,
                    commentCount=comment_count,
                    commentCount_type=(
                        type(comment_count).__name__ if comment_count is not None else "None"
                    ),
                    commentCount_is_none=comment_count is None,
                    commentCount_is_zero=comment_count == 0,
                    has_markets=bool(event_markets),
                    markets_count=len(event_markets),
                )

                # Build proper event dict with all event-level fields
                # IMPORTANT: Always include commentCount even if it's 0 (not None)
                event_dict = {
                    "title": event_model.title,
                    "image": event_model.image or event_model.icon,
                    "volume24hr": event_model.volume24hr,
                    # Include even if 0 - this is the accurate event-level value
                    "commentCount": comment_count,
                    "slug": event_model.slug or slug,
                    "seriesCommentCount": series_comment_count,
                }
                # CRITICAL: Only remove None values, but keep 0 values (especially for commentCount)
                # Use explicit check to preserve 0
                filtered_dict = {}
                for k, v in event_dict.items():
                    if v is not None:
                        filtered_dict[k] = v
                    elif k == "commentCount":
                        # Explicitly log if commentCount is None
                        logger.warning(
                            "commentCount is None in event_dict, this should not happen",
                            slug=slug,
                        )
                event_dict = filtered_dict
                logger.debug(
                    "Built event_dict",
                    event_dict_keys=list(event_dict.keys()),
                    commentCount_in_dict="commentCount" in event_dict,
                    commentCount_value=event_dict.get("commentCount"),
                )
                return event_dict, event_markets
            else:
                # Fallback to raw dict processing
                event_markets = event_raw.get("markets", [])
                comment_count = event_raw.get("commentCount")
                series_comment_count = _extract_series_comment_count(event_raw)

                logger.info(
                    "Fetched event from /events endpoint (raw dict fallback)",
                    slug=slug,
                    commentCount=comment_count,
                    commentCount_type=(
                        type(comment_count).__name__ if comment_count is not None else "None"
                    ),
                    commentCount_is_none=comment_count is None,
                    commentCount_is_zero=comment_count == 0,
                    has_markets=bool(event_markets),
                    markets_count=len(event_markets) if isinstance(event_markets, list) else 0,
                )

                event_dict = {
                    "title": event_raw.get("title"),
                    "image": event_raw.get("image") or event_raw.get("icon"),
                    "volume24hr": event_raw.get("volume24hr"),
                    "commentCount": comment_count,
                    "slug": event_raw.get("slug") or slug,
                    "seriesCommentCount": series_comment_count,
                }
                # CRITICAL: Only remove None values, but keep 0 values (especially for commentCount)
                filtered_dict = {}
                for k, v in event_dict.items():
                    if v is not None:
                        filtered_dict[k] = v
                    elif k == "commentCount":
                        logger.warning("commentCount is None in raw event_dict", slug=slug)
                event_dict = filtered_dict
                logger.debug(
                    "Built event_dict (raw)",
                    event_dict_keys=list(event_dict.keys()),
                    commentCount_in_dict="commentCount" in event_dict,
                    commentCount_value=event_dict.get("commentCount"),
                )
                return event_dict, event_markets

        # Fallback to markets endpoint if events endpoint returns nothing
        logger.debug("Events endpoint returned nothing, trying markets endpoint", slug=slug)
        markets_raw = await _fetch_json(f"{GAMMA_API}/markets", params={"slug": slug})
        if isinstance(markets_raw, dict):
            markets_list = markets_raw.get("data", [])
        elif isinstance(markets_raw, list):
            markets_list = markets_raw
        else:
            markets_list = []

        logger.debug(
            "Markets API response",
            slug=slug,
            markets_count=len(markets_list) if isinstance(markets_list, list) else 0,
            has_markets=bool(markets_list),
        )

        if markets_list:
            event = None
            try:
                # Try to deserialize with Pydantic for type safety
                try:
                    first_market_model = Market.model_validate(markets_list[0])
                    market_comment_count = None  # Markets don't typically have commentCount
                    logger.info(
                        "Fetched from /markets endpoint (Pydantic validated)",
                        slug=slug,
                        commentCount=market_comment_count,
                        markets_count=len(markets_list),
                    )
                    # Markets use question, not eventTitle
                    event = {
                        "title": first_market_model.question,
                        "image": first_market_model.image or first_market_model.icon,
                        "volume24hr": first_market_model.volume24hr,
                        "commentCount": market_comment_count,  # May be None for markets
                        "slug": slug,
                    }
                    # Convert all markets to dicts
                    markets = []
                    for m_raw in markets_list:
                        try:
                            m_model = Market.model_validate(m_raw)
                            markets.append(m_model.model_dump())
                        except Exception:
                            # Fallback to raw dict if validation fails
                            markets.append(m_raw)
                except Exception as e:
                    logger.debug(
                        "Failed to deserialize market with Pydantic, using raw data",
                        slug=slug,
                        error=str(e),
                    )
                    # Fallback to raw dict
                    first_market = markets_list[0]
                    market_comment_count = first_market.get("commentCount")
                    logger.info(
                        "Fetched from /markets endpoint (raw dict fallback)",
                        slug=slug,
                        commentCount=market_comment_count,
                        markets_count=len(markets_list),
                    )
                    event = {
                        "title": (
                            first_market.get("eventTitle")
                            or first_market.get("title")
                            or first_market.get("question")
                        ),
                        "image": first_market.get("image") or first_market.get("icon"),
                        "volume24hr": first_market.get("volume24hr"),
                        "commentCount": market_comment_count,  # May be None for markets
                        "slug": slug,
                    }
                    markets = markets_list

                # Remove None values
                event = {k: v for k, v in event.items() if v is not None}
            except Exception as e:
                logger.debug("Failed to extract event from markets", slug=slug, error=str(e))
                event = None
                markets = markets_list
            return event, markets

        # Both endpoints returned nothing
        return None, []
    except Exception as e:
        logger.warning("Failed to get event and markets", slug=slug, error=str(e))
        # Return empty results instead of crashing
        return None, []
