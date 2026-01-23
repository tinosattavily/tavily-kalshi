"""Kalshi market data fetching."""

from __future__ import annotations

from typing import Optional, Tuple

from app.config import get_logger
from app.infrastructure.http.kalshi import get_market, get_markets, get_event
from app.domains.markets.kalshi_schemas import KalshiMarket, KalshiEvent
from app.shared.exceptions import KalshiEventNotFoundError

logger = get_logger(__name__)


async def get_kalshi_market_by_ticker(ticker: str) -> KalshiMarket:
    """Fetch single market by ticker."""
    data = await get_market(ticker)
    return KalshiMarket.model_validate(data)


async def get_kalshi_event_by_ticker(event_ticker: str) -> KalshiEvent:
    """Fetch event with its markets."""
    try:
        event_data = await get_event(event_ticker)
        event = KalshiEvent.model_validate(event_data)
    except Exception as e:
        raise KalshiEventNotFoundError(f"Event not found: {event_ticker}") from e

    # Fetch markets for this event
    markets_data = await get_markets(event_ticker=event_ticker)
    event.markets = [KalshiMarket.model_validate(m) for m in markets_data]

    return event


async def get_kalshi_event_and_market(
    ticker: Optional[str],
    event_ticker: Optional[str],
) -> Tuple[KalshiEvent, Optional[KalshiMarket]]:
    """Fetch event and optionally a specific market.

    If ticker provided, fetches that specific market.
    If only event_ticker, fetches event with all markets.
    """
    if ticker:
        market = await get_kalshi_market_by_ticker(ticker)
        event = await get_kalshi_event_by_ticker(market.event_ticker)
        return event, market

    if event_ticker:
        event = await get_kalshi_event_by_ticker(event_ticker)
        return event, None

    raise ValueError("Either ticker or event_ticker required")
