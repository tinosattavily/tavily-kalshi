from __future__ import annotations

from app.domains.markets.adapters.base import MarketVenueAdapter
from app.domains.markets.adapters.kalshi import KalshiAdapter
from app.domains.markets.adapters.polymarket import PolymarketAdapter

_REGISTRY: list[MarketVenueAdapter] = [KalshiAdapter(), PolymarketAdapter()]


def registered_adapters() -> list[MarketVenueAdapter]:
    return list(_REGISTRY)


def get_adapter_for_url(url: str) -> MarketVenueAdapter:
    for adapter in _REGISTRY:
        if adapter.matches(url):
            return adapter
    raise ValueError("Unsupported URL host. Paste a Kalshi or Polymarket URL.")
