# app/infrastructure/__init__.py
"""Infrastructure layer exports."""

# Database infrastructure
from app.infrastructure.database import (
    check_mongodb_health,
    close_async_client,
    ensure_indexes_async,
    ensure_object_id,
    events_collection_async,
    get_async_client,
    get_async_db,
    markets_collection_async,
    runs_collection_async,
    serialize_document,
    traces_collection_async,
    upsert_event_async,
    upsert_market_async,
)

# HTTP infrastructure
from app.infrastructure.http import (
    CLOB_API,
    GAMMA_API,
    TAVILY_API_KEY,
    TAVILY_API_URL,
    CircuitBreaker,
    CircuitState,
    RedisCache,
    TTLCache,
    cached,
    fetch_json_async,
    fetch_order_book_async,
    normalize_number,
    openai_cache,
    openai_circuit,
    polymarket_cache,
    polymarket_circuit,
    search_news,
    tavily_cache,
    tavily_circuit,
    with_async_retry,
    with_circuit_breaker,
    with_retry,
)

# LLM infrastructure
from app.infrastructure.llm import OpenAIClient, get_openai_client

__all__ = [
    # Database
    "check_mongodb_health",
    "close_async_client",
    "ensure_indexes_async",
    "ensure_object_id",
    "events_collection_async",
    "get_async_client",
    "get_async_db",
    "markets_collection_async",
    "runs_collection_async",
    "serialize_document",
    "traces_collection_async",
    "upsert_event_async",
    "upsert_market_async",
    # HTTP - Cache
    "RedisCache",
    "TTLCache",
    "cached",
    "openai_cache",
    "polymarket_cache",
    "tavily_cache",
    # HTTP - Polymarket
    "CLOB_API",
    "GAMMA_API",
    "fetch_json_async",
    "fetch_order_book_async",
    "normalize_number",
    # HTTP - Resilience
    "CircuitBreaker",
    "CircuitState",
    "openai_circuit",
    "polymarket_circuit",
    "tavily_circuit",
    "with_async_retry",
    "with_circuit_breaker",
    "with_retry",
    # HTTP - Tavily
    "TAVILY_API_KEY",
    "TAVILY_API_URL",
    "search_news",
    # LLM
    "OpenAIClient",
    "get_openai_client",
]
