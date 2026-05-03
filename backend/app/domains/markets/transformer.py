# app/domains/markets/transformer.py
"""Market data transformation utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import get_logger
from app.domains.markets.parsing import parse_end_date, parse_prices_from_market

logger = get_logger(__name__)


def build_market_options(markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build market options list for UI selection.

    Args:
        markets: List of market dictionaries from Polymarket API

    Returns:
        List of market option dictionaries with normalized fields
    """
    market_options = []
    for m in markets:
        market_options.append(
            {
                "slug": m.get("slug"),
                "question": m.get("question") or m.get("title"),
                "group_item_title": m.get("groupItemTitle"),
                "liquidity": m.get("liquidity"),
                "best_bid": m.get("bestBid"),
                "best_ask": m.get("bestAsk"),
                "image": m.get("image") or m.get("icon"),
            }
        )
    return market_options


def build_market_snapshot(
    market: Dict[str, Any],
    market_url: str,
    order_book: Dict[str, Any],
    state: Dict[str, Any],
    slug: str,
    api_market_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
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
    # Use API market record if provided, otherwise use market dict
    api_data = api_market_record or market

    # Prioritize api_market_record question if provided, otherwise use market question
    question = (
        (api_market_record.get("question") if api_market_record else None)
        or market.get("question")
        or api_data.get("question")
        or api_data.get("title")
        or f"Will {slug.replace('-', ' ')} resolve to Yes?"
    )
    outcomes = market.get("outcomes") or api_data.get("outcomes") or ["Yes", "No"]
    yes_index = market.get("yes_index") or api_data.get("yes_index", 0)

    # Extract real prices from API data
    yes_price, no_price = parse_prices_from_market(api_data)

    # Fallback to calculated prices if API doesn't provide them
    if yes_price is None or no_price is None:
        baseline_yes = state.get("market_snapshot", {}).get("yes_price", 0.02)
        yes_price = round(min(max(baseline_yes, 0.01), 0.99), 4)
        no_price = round(1.0 - yes_price, 4)
    else:
        yes_price = round(float(yes_price), 4)
        no_price = round(float(no_price), 4)

    # Extract best bid/ask from API or order book
    best_bid = api_data.get("bestBid") or api_data.get("best_bid")
    best_ask = api_data.get("bestAsk") or api_data.get("best_ask")

    # Use order book if available
    if order_book and order_book.get("best_bid") is not None:
        best_bid = order_book.get("best_bid")
    if order_book and order_book.get("best_ask") is not None:
        best_ask = order_book.get("best_ask")

    # Fallback to calculated bid/ask if not available
    if best_bid is None:
        best_bid = round(max(0.0, yes_price - 0.001), 4)
    else:
        best_bid = round(float(best_bid), 4)

    if best_ask is None:
        best_ask = round(min(1.0, yes_price + 0.001), 4)
    else:
        best_ask = round(float(best_ask), 4)

    # Extract end date from API
    end_date = None
    if api_data.get("endDate"):
        end_date = parse_end_date(api_data.get("endDate"))
    elif api_data.get("end_date"):
        end_date = parse_end_date(api_data.get("end_date"))

    # Fallback to state or current time
    if not end_date:
        end_date_str = state.get("market_snapshot", {}).get("end_date") or state.get(
            "event", {}
        ).get("end_date")
        if end_date_str:
            end_date = parse_end_date(end_date_str)

    if not end_date:
        end_date = datetime.now(timezone.utc).replace(microsecond=0)

    # Format end_date as ISO string
    if isinstance(end_date, datetime):
        end_date_iso = end_date.isoformat().replace("+00:00", "Z")
    else:
        end_date_iso = str(end_date)

    # Extract volume and liquidity from API
    volume = (
        api_data.get("volume")
        or api_data.get("volume24hr")
        or state.get("market_snapshot", {}).get("volume", 0.0)
    )
    liquidity = api_data.get("liquidity") or state.get("market_snapshot", {}).get("liquidity", 0.0)
    volume24hr = api_data.get("volume24hr") or state.get("event", {}).get("volume24hr")

    # Extract comment counts (event + series + market fallback)
    event_comment_count = state.get("event", {}).get("commentCount")
    series_comment_count = state.get("event", {}).get("seriesCommentCount")
    comment_count = event_comment_count if event_comment_count is not None else series_comment_count

    if comment_count is not None:
        logger.debug(
            "Using commentCount from state",
            commentCount=comment_count,
            eventCommentCount=event_comment_count,
            seriesCommentCount=series_comment_count,
            slug=slug,
        )
    else:
        # Fallback to market-level commentCount if available
        if api_data:
            if "commentCount" in api_data and api_data["commentCount"] is not None:
                comment_count = api_data["commentCount"]
            elif "comment_count" in api_data and api_data["comment_count"] is not None:
                comment_count = api_data["comment_count"]

        if comment_count is not None:
            logger.debug(
                "Using commentCount from market record (state missing)",
                commentCount=comment_count,
                slug=slug,
            )

    # Format outcomes for frontend compatibility
    formatted_outcomes = [
        {"title": outcome, "price": yes_price if idx == yes_index else no_price}
        for idx, outcome in enumerate(outcomes)
    ]

    gamma_market_id = state.get("gamma_market_id") or api_data.get("id") or f"gamma-{slug}"
    group_item_title = api_data.get("groupItemTitle") or api_data.get("group_item_title")

    # Build order book structure for frontend
    if order_book and (order_book.get("bids") or order_book.get("asks")):
        order_book_data = {
            "bids": order_book.get("bids", []),
            "asks": order_book.get("asks", []),
        }
    else:
        # Return empty structure with bids/asks arrays when order_book is empty
        order_book_data = {
            "bids": [],
            "asks": [],
        }

    return {
        "slug": slug,
        "url": market_url,
        "question": question,
        "title": question,  # Frontend compatibility
        "outcomes": outcomes,
        "formatted_outcomes": formatted_outcomes,  # Frontend-friendly format
        "yes_index": yes_index,
        "yes_price": yes_price,
        "no_price": no_price,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "bestBid": best_bid,  # Frontend compatibility (camelCase)
        "bestAsk": best_ask,  # Frontend compatibility (camelCase)
        "last_trade_price": yes_price,
        "volume": float(volume) if volume else 0.0,
        "volume24hr": float(volume24hr) if volume24hr else None,
        "liquidity": float(liquidity) if liquidity else 0.0,
        "end_date": end_date_iso,
        "endDate": end_date_iso,  # Frontend compatibility (camelCase)
        "market_id": gamma_market_id,  # Frontend compatibility
        "group_item_title": group_item_title,
        "groupItemTitle": group_item_title,  # Frontend compatibility (camelCase)
        "order_book": order_book_data,
        "orderBook": order_book_data,  # Frontend compatibility (camelCase)
        "comment_count": comment_count,
        "commentCount": comment_count,  # Frontend compatibility (camelCase)
        "event_comment_count": event_comment_count,
        "eventCommentCount": event_comment_count,
        "series_comment_count": series_comment_count,
        "seriesCommentCount": series_comment_count,
    }


def transform_market(market: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a single market dict to normalized format.

    Args:
        market: Raw market dictionary from Polymarket API

    Returns:
        Normalized market dictionary
    """
    yes_price, no_price = parse_prices_from_market(market)
    return {
        "slug": market.get("slug"),
        "question": market.get("question") or market.get("title"),
        "yes_price": yes_price,
        "no_price": no_price,
        "liquidity": market.get("liquidity"),
        "volume": market.get("volume"),
        "end_date": market.get("endDate") or market.get("end_date"),
    }
