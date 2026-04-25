from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Literal, TypedDict

Venue = Literal["kalshi", "polymarket"]


class NormalizedMarketOption(TypedDict, total=False):
    venue: Venue
    market_id: str
    label: str
    subtitle: str
    yes_price: float
    best_bid: float
    best_ask: float
    volume: float
    volume_24h: float
    liquidity: float
    close_time: str
    raw: dict[str, Any]


class NormalizedMarketResult(TypedDict, total=False):
    venue: Venue
    raw_url: str
    canonical_url: str
    market_id: str
    event_id: str
    selected_market_id: str
    requires_market_selection: bool
    market_options: list[NormalizedMarketOption]
    market: dict[str, Any]
    event: dict[str, Any]
    market_snapshot: dict[str, Any]
    event_context: dict[str, Any]
    raw: dict[str, Any]


class MarketVenueAdapter(ABC):
    venue: ClassVar[Venue]

    @abstractmethod
    def matches(self, url: str) -> bool:
        """Return True when this adapter owns the URL."""

    @abstractmethod
    async def fetch(
        self,
        url: str,
        selected_market_id: str | None = None,
    ) -> NormalizedMarketResult:
        """Fetch and normalize a market or selection result."""
