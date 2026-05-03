from app.domains.markets.adapters.base import (
    MarketVenueAdapter,
    NormalizedMarketOption,
    NormalizedMarketResult,
    Venue,
)


def get_adapter_for_url(url: str) -> MarketVenueAdapter:
    from app.domains.markets.adapters.registry import get_adapter_for_url as _get_adapter_for_url

    return _get_adapter_for_url(url)


def registered_adapters() -> list[MarketVenueAdapter]:
    from app.domains.markets.adapters.registry import registered_adapters as _registered_adapters

    return _registered_adapters()

__all__ = [
    "MarketVenueAdapter",
    "NormalizedMarketOption",
    "NormalizedMarketResult",
    "Venue",
    "get_adapter_for_url",
    "registered_adapters",
]
