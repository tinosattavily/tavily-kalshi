# app/infrastructure/http/__init__.py
"""HTTP infrastructure exports."""

from app.infrastructure.http.cache import (
    RedisCache,
    TTLCache,
    cached,
    openai_cache,
    polymarket_cache,
    tavily_cache,
)
from app.infrastructure.http.polymarket import (
    CLOB_API,
    GAMMA_API,
    fetch_json_async,
    fetch_order_book_async,
    normalize_number,
)
from app.infrastructure.http.resilience import (
    CircuitBreaker,
    CircuitState,
    openai_circuit,
    polymarket_circuit,
    tavily_circuit,
    with_async_retry,
    with_circuit_breaker,
    with_retry,
)
from app.infrastructure.http.tavily import (
    TAVILY_API_KEY,
    TAVILY_API_URL,
    search_news,
)

__all__ = [
    # Cache
    "RedisCache",
    "TTLCache",
    "cached",
    "openai_cache",
    "polymarket_cache",
    "tavily_cache",
    # Polymarket
    "CLOB_API",
    "GAMMA_API",
    "fetch_json_async",
    "fetch_order_book_async",
    "normalize_number",
    # Resilience
    "CircuitBreaker",
    "CircuitState",
    "openai_circuit",
    "polymarket_circuit",
    "tavily_circuit",
    "with_async_retry",
    "with_circuit_breaker",
    "with_retry",
    # Tavily
    "TAVILY_API_KEY",
    "TAVILY_API_URL",
    "search_news",
]
