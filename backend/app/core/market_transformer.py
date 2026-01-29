"""Market data transformation utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.core.logging_config import get_logger
from app.core.polymarket_utils import parse_end_date, parse_prices_from_market

logger = get_logger(__name__)


def build_market_options(markets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build market options list for UI selection.

    Args:
        markets: List of market dictionaries from Polymarket API

    Returns:
        List of market option dictionaries with normalized fields
    """
    return [
        {
            "slug": m.get("slug"),
            "question": m.get("question") or m.get("title"),
            "group_item_title": m.get("groupItemTitle"),
            "liquidity": m.get("liquidity"),
            "best_bid": m.get("bestBid"),
            "best_ask": m.get("bestAsk"),
            "image": m.get("image") or m.get("icon"),
        }
        for m in markets
    ]


def _extract_question(
    market: dict[str, Any],
    api_data: dict[str, Any],
    api_market_record: Optional[dict[str, Any]],
    slug: str,
) -> str:
    """Extract the market question from available sources."""
    if api_market_record and api_market_record.get("question"):
        return api_market_record["question"]
    return (
        market.get("question")
        or api_data.get("question")
        or api_data.get("title")
        or f"Will {slug.replace('-', ' ')} resolve to Yes?"
    )


def _extract_prices(
    api_data: dict[str, Any], state: dict[str, Any]
) -> tuple[float, float]:
    """Extract yes/no prices from API data with fallback to state."""
    yes_price, no_price = parse_prices_from_market(api_data)

    if yes_price is None or no_price is None:
        baseline_yes = state.get("market_snapshot", {}).get("yes_price", 0.02)
        yes_price = round(min(max(baseline_yes, 0.01), 0.99), 4)
        no_price = round(1.0 - yes_price, 4)
    else:
        yes_price = round(float(yes_price), 4)
        no_price = round(float(no_price), 4)

    return yes_price, no_price


def _extract_bid_ask(
    api_data: dict[str, Any],
    order_book: dict[str, Any],
    yes_price: float,
) -> tuple[float, float]:
    """Extract best bid/ask from API or order book with calculated fallback."""
    best_bid = api_data.get("bestBid") or api_data.get("best_bid")
    best_ask = api_data.get("bestAsk") or api_data.get("best_ask")

    if order_book:
        if order_book.get("best_bid") is not None:
            best_bid = order_book["best_bid"]
        if order_book.get("best_ask") is not None:
            best_ask = order_book["best_ask"]

    if best_bid is None:
        best_bid = round(max(0.0, yes_price - 0.001), 4)
    else:
        best_bid = round(float(best_bid), 4)

    if best_ask is None:
        best_ask = round(min(1.0, yes_price + 0.001), 4)
    else:
        best_ask = round(float(best_ask), 4)

    return best_bid, best_ask


def _extract_end_date(api_data: dict[str, Any], state: dict[str, Any]) -> str:
    """Extract and format end date from API data or state."""
    end_date = parse_end_date(api_data.get("endDate") or api_data.get("end_date"))

    if not end_date:
        end_date_str = (
            state.get("market_snapshot", {}).get("end_date")
            or state.get("event", {}).get("end_date")
        )
        if end_date_str:
            end_date = parse_end_date(end_date_str)

    if not end_date:
        end_date = datetime.now(timezone.utc).replace(microsecond=0)

    if isinstance(end_date, datetime):
        return end_date.isoformat().replace("+00:00", "Z")
    return str(end_date)


def _extract_comment_counts(
    api_data: dict[str, Any], state: dict[str, Any], slug: str
) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """Extract comment counts from state or API data.

    Returns:
        Tuple of (comment_count, event_comment_count, series_comment_count)
    """
    event_data = state.get("event", {})
    event_comment_count = event_data.get("commentCount")
    series_comment_count = event_data.get("seriesCommentCount")

    if event_comment_count is not None:
        comment_count = event_comment_count
        logger.debug(
            "Using commentCount from state",
            commentCount=comment_count,
            eventCommentCount=event_comment_count,
            seriesCommentCount=series_comment_count,
            slug=slug,
        )
        return comment_count, event_comment_count, series_comment_count

    if series_comment_count is not None:
        logger.debug(
            "Using seriesCommentCount from state",
            commentCount=series_comment_count,
            seriesCommentCount=series_comment_count,
            slug=slug,
        )
        return series_comment_count, event_comment_count, series_comment_count

    # Fallback to market-level commentCount
    comment_count = api_data.get("commentCount") or api_data.get("comment_count")
    if comment_count is not None:
        logger.debug(
            "Using commentCount from market record (state missing)",
            commentCount=comment_count,
            slug=slug,
        )

    return comment_count, event_comment_count, series_comment_count


def _build_order_book_data(order_book: dict[str, Any]) -> dict[str, list]:
    """Build order book structure for frontend."""
    if order_book and (order_book.get("bids") or order_book.get("asks")):
        return {
            "bids": order_book.get("bids", []),
            "asks": order_book.get("asks", []),
        }
    return {"bids": [], "asks": []}


def build_market_snapshot(
    market: dict[str, Any],
    market_url: str,
    order_book: dict[str, Any],
    state: dict[str, Any],
    slug: str,
    api_market_record: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build market snapshot dictionary for frontend.

    Args:
        market: Market dictionary with question, outcomes, etc.
        market_url: The Polymarket URL for this market
        order_book: Order book data (bids/asks)
        state: Current agent state for fallback values
        slug: Market slug
        api_market_record: Raw market record from Polymarket API (optional)

    Returns:
        Market snapshot dictionary with all frontend-required fields
    """
    api_data = api_market_record or market

    question = _extract_question(market, api_data, api_market_record, slug)
    outcomes = market.get("outcomes") or api_data.get("outcomes") or ["Yes", "No"]
    yes_index = market.get("yes_index") or api_data.get("yes_index", 0)

    yes_price, no_price = _extract_prices(api_data, state)
    best_bid, best_ask = _extract_bid_ask(api_data, order_book, yes_price)
    end_date_iso = _extract_end_date(api_data, state)

    volume = (
        api_data.get("volume")
        or api_data.get("volume24hr")
        or state.get("market_snapshot", {}).get("volume", 0.0)
    )
    liquidity = (
        api_data.get("liquidity")
        or state.get("market_snapshot", {}).get("liquidity", 0.0)
    )
    volume24hr = api_data.get("volume24hr") or state.get("event", {}).get("volume24hr")

    comment_count, event_comment_count, series_comment_count = _extract_comment_counts(
        api_data, state, slug
    )

    formatted_outcomes = [
        {"title": outcome, "price": yes_price if idx == yes_index else no_price}
        for idx, outcome in enumerate(outcomes)
    ]

    gamma_market_id = (
        state.get("gamma_market_id") or api_data.get("id") or f"gamma-{slug}"
    )
    group_item_title = api_data.get("groupItemTitle") or api_data.get("group_item_title")
    order_book_data = _build_order_book_data(order_book)

    return {
        "slug": slug,
        "url": market_url,
        "question": question,
        "title": question,
        "outcomes": outcomes,
        "formatted_outcomes": formatted_outcomes,
        "yes_index": yes_index,
        "yes_price": yes_price,
        "no_price": no_price,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "bestBid": best_bid,
        "bestAsk": best_ask,
        "last_trade_price": yes_price,
        "volume": float(volume) if volume else 0.0,
        "volume24hr": float(volume24hr) if volume24hr else None,
        "liquidity": float(liquidity) if liquidity else 0.0,
        "end_date": end_date_iso,
        "endDate": end_date_iso,
        "market_id": gamma_market_id,
        "group_item_title": group_item_title,
        "groupItemTitle": group_item_title,
        "order_book": order_book_data,
        "orderBook": order_book_data,
        "comment_count": comment_count,
        "commentCount": comment_count,
        "event_comment_count": event_comment_count,
        "eventCommentCount": event_comment_count,
        "series_comment_count": series_comment_count,
        "seriesCommentCount": series_comment_count,
    }
