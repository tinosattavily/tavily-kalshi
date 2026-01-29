"""Market selection utilities."""

from __future__ import annotations

from typing import Any


def _get_market_slug(market: dict[str, Any]) -> str:
    """Extract slug from market, falling back to id if slug is missing."""
    return market.get("slug") or str(market.get("id", ""))


def _matches_exact(market: dict[str, Any], slug: str) -> bool:
    """Check if market matches the given slug exactly (by slug or id)."""
    return (market.get("slug") or "") == slug or str(market.get("id")) == slug


def _matches_fuzzy(market: dict[str, Any], search_slug: str) -> bool:
    """Check if market matches the given slug via fuzzy matching.

    Matches if the search slug is contained in the market slug,
    or if the market slug ends with the search slug,
    or if the search slug matches the market id exactly.
    """
    slug_val = (market.get("slug") or "").strip().lower()
    id_val = str(market.get("id") or "").strip().lower()

    if not slug_val and not id_val:
        return False

    search_lower = search_slug.strip().lower()
    return (
        search_lower in slug_val
        or slug_val.endswith(search_lower)
        or search_lower == id_val
    )


def _find_by_exact_match(
    markets: list[dict[str, Any]], slug: str
) -> dict[str, Any] | None:
    """Find a market by exact slug or id match."""
    for market in markets:
        if _matches_exact(market, slug):
            return market
    return None


def _find_by_fuzzy_match(
    markets: list[dict[str, Any]], slug: str
) -> dict[str, Any] | None:
    """Find a market by fuzzy matching on slug or id."""
    for market in markets:
        if _matches_fuzzy(market, slug):
            return market
    return None


def _find_by_url_slug_suffix(
    markets: list[dict[str, Any]], url_slug: str
) -> dict[str, Any] | None:
    """Find a market whose slug ends with the given URL slug."""
    for market in markets:
        if (market.get("slug") or "").endswith(url_slug):
            return market
    return None


def select_market_from_options(
    markets: list[dict[str, Any]],
    selected_slug: str | None,
    url_slug: str,
) -> tuple[dict[str, Any] | None, str | None, bool]:
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

    if len(markets) == 1:
        market = markets[0]
        return market, _get_market_slug(market), False

    if selected_slug:
        # Try exact match first
        market = _find_by_exact_match(markets, selected_slug)
        if market:
            return market, _get_market_slug(market), False

        # Try fuzzy match
        market = _find_by_fuzzy_match(markets, selected_slug)
        if market:
            return market, _get_market_slug(market), False

        # Fall back to first market if selection didn't match
        market = markets[0]
        return market, _get_market_slug(market), False

    # Try to match by URL slug suffix
    market = _find_by_url_slug_suffix(markets, url_slug)
    if market:
        return market, _get_market_slug(market), False

    # Multiple markets and no selection - requires user selection
    return None, None, True


def find_market_by_slug(
    markets: list[dict[str, Any]], slug: str | None
) -> dict[str, Any] | None:
    """Find a market in the list by slug or id."""
    if not slug or not markets:
        return None

    return _find_by_exact_match(markets, slug)
