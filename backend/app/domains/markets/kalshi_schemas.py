"""Kalshi API response schemas. All prices in cents (1-99)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class KalshiMarket(BaseModel):
    """Single Kalshi market. Prices in cents."""

    model_config = ConfigDict(extra="ignore")

    ticker: str
    event_ticker: str
    title: str
    subtitle: Optional[str] = None
    status: str  # "open", "closed", "settled"

    # Prices in cents (1-99)
    yes_bid: Optional[int] = None
    yes_ask: Optional[int] = None
    no_bid: Optional[int] = None
    no_ask: Optional[int] = None
    last_price: Optional[int] = None

    # Volume
    volume: Optional[int] = None
    volume_24h: Optional[int] = None
    open_interest: Optional[int] = None

    # Timing
    open_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    expiration_time: Optional[datetime] = None

    # Settlement
    result: Optional[str] = None  # "yes", "no", null if not settled


class KalshiEvent(BaseModel):
    """Kalshi event containing multiple markets."""

    model_config = ConfigDict(extra="ignore")

    event_ticker: str
    title: str
    category: Optional[str] = None
    sub_title: Optional[str] = None

    # Nested markets (if included in response)
    markets: List[KalshiMarket] = Field(default_factory=list)


class KalshiOrderbookLevel(BaseModel):
    """Single level in orderbook."""

    price: int  # Cents
    quantity: int  # Number of contracts


class KalshiOrderbook(BaseModel):
    """Orderbook for a market."""

    model_config = ConfigDict(extra="ignore")

    ticker: str
    yes_bids: List[KalshiOrderbookLevel] = Field(default_factory=list)
    yes_asks: List[KalshiOrderbookLevel] = Field(default_factory=list)
    no_bids: List[KalshiOrderbookLevel] = Field(default_factory=list)
    no_asks: List[KalshiOrderbookLevel] = Field(default_factory=list)


# Response wrappers
class MarketResponse(BaseModel):
    """Wrapper for single market response."""

    market: KalshiMarket


class MarketsResponse(BaseModel):
    """Wrapper for markets list response."""

    markets: List[KalshiMarket]
    cursor: Optional[str] = None


class EventResponse(BaseModel):
    """Wrapper for event response."""

    event: KalshiEvent
