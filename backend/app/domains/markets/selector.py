# app/domains/markets/selector.py
"""Market selection utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.config import get_logger

logger = get_logger(__name__)


def select_market_from_options(
    markets: List[Dict[str, Any]],
    selected_slug: Optional[str],
    url_slug: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str], bool]:
    """Select a market from available options.

    Args:
        markets: List of market dictionaries from Polymarket API
        selected_slug: User-selected market slug (if any)
        url_slug: Slug extracted from the URL

    Returns:
        Tuple of (chosen_market, chosen_market_slug, requires_selection)
        - chosen_market: The selected market dict or None
        - chosen_market_slug: The slug of the chosen market or None
        - requires_selection: True if user needs to select from multiple options
    """
    if not markets:
        return None, None, False

    # If only one market, auto-select it
    if len(markets) == 1:
        market = markets[0]
        slug = market.get("slug") or str(market.get("id", ""))
        return market, slug, False

    # If user provided a selection, try to find it
    if selected_slug:
        for m in markets:
            if (m.get("slug") or "") == selected_slug or str(m.get("id")) == selected_slug:
                slug = m.get("slug") or str(m.get("id", ""))
                return m, slug, False

        # Try fuzzy matching
        selected_slug_lower = selected_slug.strip().lower()
        for m in markets:
            slug_val = (m.get("slug") or "").strip().lower()
            id_val = str(m.get("id") or "").strip().lower()
            if not slug_val and not id_val:
                continue
            if selected_slug_lower and (
                selected_slug_lower in slug_val
                or slug_val.endswith(selected_slug_lower)
                or selected_slug_lower == id_val
            ):
                slug = m.get("slug") or str(m.get("id", ""))
                return m, slug, False

        # If still not found but we have markets, use first as fallback
        if markets:
            market = markets[0]
            slug = market.get("slug") or str(market.get("id", ""))
            return market, slug, False

    # Try to match by URL slug
    for m in markets:
        if (m.get("slug") or "").endswith(url_slug):
            slug = m.get("slug") or str(m.get("id", ""))
            return m, slug, False

    # Multiple markets and no selection - requires user selection
    return None, None, True


def find_market_by_slug(
    markets: List[Dict[str, Any]], slug: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Find a market in the list by slug or id."""
    if not slug or not markets:
        return None

    for m in markets:
        if (m.get("slug") or "") == slug or str(m.get("id")) == slug:
            return m
    return None


def select_market(
    markets: List[Dict[str, Any]],
    selected_slug: Optional[str] = None,
    url_slug: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str], bool]:
    """Select a market from available options.

    This is the main entry point for market selection logic.

    Args:
        markets: List of market dictionaries from Polymarket API
        selected_slug: User-selected market slug (if any)
        url_slug: Slug extracted from the URL (optional)

    Returns:
        Tuple of (chosen_market, chosen_market_slug, requires_selection)
    """
    return select_market_from_options(markets, selected_slug, url_slug or "")
