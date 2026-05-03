# app/domains/markets/__init__.py
"""Markets domain exports."""

from app.domains.markets.event_service import EventService, get_event_service
from app.domains.markets.fetcher import get_event_and_markets_by_slug
from app.domains.markets.parsing import (
    extract_slug_from_url,
    normalize_number,
    parse_end_date,
    parse_prices_from_market,
)
from app.domains.markets.schemas import Event, Market
from app.domains.markets.selector import (
    find_market_by_slug,
    select_market,
    select_market_from_options,
)
from app.domains.markets.service import MarketService, get_market_service
from app.domains.markets.transformer import (
    build_market_options,
    build_market_snapshot,
    transform_market,
)

__all__ = [
    # Schemas
    "Event",
    "Market",
    # Services
    "EventService",
    "MarketService",
    "get_event_service",
    "get_market_service",
    # Fetcher
    "get_event_and_markets_by_slug",
    # Parsing
    "extract_slug_from_url",
    "normalize_number",
    "parse_end_date",
    "parse_prices_from_market",
    # Selector
    "find_market_by_slug",
    "select_market",
    "select_market_from_options",
    # Transformer
    "build_market_options",
    "build_market_snapshot",
    "transform_market",
]
