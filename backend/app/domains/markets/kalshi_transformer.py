"""Transform Kalshi API responses to internal domain types."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.config import get_logger
from app.domains.markets.kalshi_schemas import KalshiMarket, KalshiEvent

logger = get_logger(__name__)


def _validate_price(price: Optional[int], field_name: str) -> Optional[int]:
    """Validate price is in valid cents range (1-99).

    Returns None if None, clamps if out of range.
    """
    if price is None:
        return None

    if not isinstance(price, int):
        try:
            price = int(price)
        except (ValueError, TypeError):
            logger.warning(f"Price {field_name} is not an integer", value=price)
            return None

    if price < 1 or price > 99:
        logger.warning(f"Price {field_name} out of range, clamping", value=price)
        return max(1, min(99, price))

    return price


def _calculate_yes_price(market: KalshiMarket) -> Optional[int]:
    """Calculate best YES price estimate.

    Priority: mid of bid/ask > yes_bid > last_price
    """
    yes_bid = _validate_price(market.yes_bid, "yes_bid")
    yes_ask = _validate_price(market.yes_ask, "yes_ask")

    # Best: mid of bid/ask
    if yes_bid is not None and yes_ask is not None:
        return (yes_bid + yes_ask) // 2

    # Fallback: bid only
    if yes_bid is not None:
        return yes_bid

    # Fallback: last trade
    last_price = _validate_price(market.last_price, "last_price")
    if last_price is not None:
        return last_price

    # No price available
    logger.warning("No price available for market", ticker=market.ticker)
    return None


def build_kalshi_market_snapshot(market: KalshiMarket) -> Dict[str, Any]:
    """Convert KalshiMarket to internal MarketSnapshot dict.

    All prices in cents (1-99).
    """
    yes_price = _calculate_yes_price(market)

    return {
        "ticker": market.ticker,
        "event_ticker": market.event_ticker,
        "title": market.title,
        "subtitle": market.subtitle,
        "status": market.status,
        "yes_price": yes_price,
        "yes_bid": _validate_price(market.yes_bid, "yes_bid"),
        "yes_ask": _validate_price(market.yes_ask, "yes_ask"),
        "no_bid": _validate_price(market.no_bid, "no_bid"),
        "no_ask": _validate_price(market.no_ask, "no_ask"),
        "last_trade_price": _validate_price(market.last_price, "last_price"),
        "volume": market.volume,
        "volume_24h": market.volume_24h,
        "open_interest": market.open_interest,
        "close_time": market.close_time.isoformat() if market.close_time else None,
    }


def build_kalshi_event_context(event: KalshiEvent) -> Dict[str, Any]:
    """Build event context with all markets for multi-market events."""
    market_summaries: List[Dict[str, Any]] = []

    for market in event.markets:
        yes_price = _calculate_yes_price(market)
        market_summaries.append({
            "ticker": market.ticker,
            "title": market.title,
            "subtitle": market.subtitle,
            "yes_price": yes_price,
            "status": market.status,
        })

    return {
        "event_ticker": event.event_ticker,
        "event_title": event.title,
        "category": event.category,
        "market_count": len(event.markets),
        "markets": market_summaries,
        "requires_selection": len(event.markets) > 1,
    }
