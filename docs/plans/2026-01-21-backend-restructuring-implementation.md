# Backend Restructuring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure the backend into a domain-driven architecture for improved maintainability, readability, and scalability.

**Architecture:** Business logic organized into domains (markets, news, analysis, reports), with thin agent wrappers in orchestration layer, isolated infrastructure (DB, HTTP, LLM), and clean API layer. Config consolidated in one place.

**Tech Stack:** Python 3.11, FastAPI, LangGraph, MongoDB (Motor), aiohttp, OpenAI SDK, pytest

**Reference:** See `docs/plans/2026-01-21-backend-restructuring-design.md` for complete file mapping.

---

## Phase 1: Create Directory Structure

### Task 1.1: Create all new directories

**Files:**
- Create: All new directory structure with `__init__.py` files

**Step 1: Create directory structure**

```bash
cd /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets/backend

# Config
mkdir -p app/config

# Domains
mkdir -p app/domains/markets
mkdir -p app/domains/news/sentiment
mkdir -p app/domains/analysis
mkdir -p app/domains/reports

# Orchestration
mkdir -p app/orchestration/agents

# Infrastructure
mkdir -p app/infrastructure/database
mkdir -p app/infrastructure/http
mkdir -p app/infrastructure/llm

# API
mkdir -p app/api/routes
mkdir -p app/api/schemas

# Shared
mkdir -p app/shared

# Tests
mkdir -p tests/unit/domains/markets
mkdir -p tests/unit/domains/news
mkdir -p tests/unit/domains/analysis
mkdir -p tests/unit/domains/reports
mkdir -p tests/unit/orchestration
mkdir -p tests/unit/infrastructure
mkdir -p tests/unit/api
mkdir -p tests/integration
```

**Step 2: Create all `__init__.py` files**

```bash
# Config
touch app/config/__init__.py

# Domains
touch app/domains/__init__.py
touch app/domains/markets/__init__.py
touch app/domains/news/__init__.py
touch app/domains/news/sentiment/__init__.py
touch app/domains/analysis/__init__.py
touch app/domains/reports/__init__.py

# Orchestration
touch app/orchestration/__init__.py
touch app/orchestration/agents/__init__.py

# Infrastructure
touch app/infrastructure/__init__.py
touch app/infrastructure/database/__init__.py
touch app/infrastructure/http/__init__.py
touch app/infrastructure/llm/__init__.py

# API
touch app/api/__init__.py
touch app/api/routes/__init__.py
touch app/api/schemas/__init__.py

# Shared
touch app/shared/__init__.py

# Tests
touch tests/unit/__init__.py
touch tests/unit/domains/__init__.py
touch tests/unit/domains/markets/__init__.py
touch tests/unit/domains/news/__init__.py
touch tests/unit/domains/analysis/__init__.py
touch tests/unit/domains/reports/__init__.py
touch tests/unit/orchestration/__init__.py
touch tests/unit/infrastructure/__init__.py
touch tests/unit/api/__init__.py
touch tests/integration/__init__.py
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: create new directory structure for domain-driven architecture"
```

---

## Phase 2: Config Module

### Task 2.1: Create config/settings.py

**Files:**
- Create: `app/config/settings.py`
- Source: `app/config.py` lines 1-41

**Step 1: Create settings.py**

```python
# app/config/settings.py
"""Environment variable configuration."""

import os
from dataclasses import dataclass
from pathlib import Path

# Load .env file if it exists (before reading environment variables)
try:
    from dotenv import load_dotenv

    # Load .env from project root (one level up from backend/)
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass


def _get_env(name: str) -> str | None:
    """Get environment variable, stripping whitespace."""
    value = os.getenv(name)
    return value.strip() if value else None


@dataclass
class Settings:
    """Central place to read environment variables for the backend."""

    openai_api_key: str | None = _get_env("OPENAI_API_KEY")
    tavily_api_key: str | None = _get_env("TAVILY_API_KEY")
    mongodb_uri: str | None = _get_env("MONGODB_URI")
    # Redis configuration
    redis_url: str | None = _get_env("REDIS_URL")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: str | None = _get_env("REDIS_PASSWORD")
    # Cache configuration
    use_redis_cache: bool = os.getenv("USE_REDIS_CACHE", "false").lower() in ("true", "1", "yes")


settings = Settings()
```

**Step 2: Run existing config tests to establish baseline**

```bash
pytest tests/test_config.py -v
```
Expected: All tests PASS

**Step 3: Commit**

```bash
git add app/config/settings.py
git commit -m "feat(config): add settings.py with environment variables"
```

### Task 2.2: Create config/constants.py

**Files:**
- Create: `app/config/constants.py`
- Source: `app/config.py` lines 44-52

**Step 1: Create constants.py**

```python
# app/config/constants.py
"""API endpoints and application constants."""


class PolymarketAPI:
    """Polymarket API endpoint constants."""

    GAMMA_API = "https://gamma-api.polymarket.com"
    CLOB_API = "https://clob.polymarket.com"
```

**Step 2: Commit**

```bash
git add app/config/constants.py
git commit -m "feat(config): add constants.py with API endpoints"
```

### Task 2.3: Create config/logging.py

**Files:**
- Create: `app/config/logging.py`
- Source: `app/core/logging_config.py` (entire file)

**Step 1: Copy logging_config.py to new location**

```bash
cp app/core/logging_config.py app/config/logging.py
```

**Step 2: Commit**

```bash
git add app/config/logging.py
git commit -m "feat(config): add logging.py configuration"
```

### Task 2.4: Create config/__init__.py exports

**Files:**
- Modify: `app/config/__init__.py`

**Step 1: Add exports**

```python
# app/config/__init__.py
"""Configuration module exports."""

from app.config.constants import PolymarketAPI
from app.config.logging import get_logger
from app.config.settings import Settings, _get_env, settings

__all__ = [
    "PolymarketAPI",
    "Settings",
    "_get_env",
    "get_logger",
    "settings",
]
```

**Step 2: Commit**

```bash
git add app/config/__init__.py
git commit -m "feat(config): add module exports"
```

---

## Phase 3: Shared Types

### Task 3.1: Create shared/types.py

**Files:**
- Create: `app/shared/types.py`
- Source: `app/db/models.py` (entire file)

**Step 1: Copy models.py to types.py**

```bash
cp app/db/models.py app/shared/types.py
```

**Step 2: Commit**

```bash
git add app/shared/types.py
git commit -m "feat(shared): add types.py with TypedDict definitions"
```

### Task 3.2: Create shared/exceptions.py

**Files:**
- Create: `app/shared/exceptions.py`

**Step 1: Create exceptions.py**

```python
# app/shared/exceptions.py
"""Custom exceptions for the application."""


class ProphilyError(Exception):
    """Base exception for all application errors."""

    pass


class ConfigurationError(ProphilyError):
    """Raised when configuration is invalid or missing."""

    pass


class ExternalAPIError(ProphilyError):
    """Raised when an external API call fails."""

    pass


class PolymarketAPIError(ExternalAPIError):
    """Raised when Polymarket API call fails."""

    pass


class TavilyAPIError(ExternalAPIError):
    """Raised when Tavily API call fails."""

    pass


class OpenAIAPIError(ExternalAPIError):
    """Raised when OpenAI API call fails."""

    pass


class DatabaseError(ProphilyError):
    """Raised when database operation fails."""

    pass


class ValidationError(ProphilyError):
    """Raised when data validation fails."""

    pass


class MarketSelectionRequiredError(ProphilyError):
    """Raised when user must select a market from multiple options."""

    def __init__(self, market_options: list, event_context: dict):
        self.market_options = market_options
        self.event_context = event_context
        super().__init__("Market selection required")
```

**Step 2: Commit**

```bash
git add app/shared/exceptions.py
git commit -m "feat(shared): add custom exceptions"
```

### Task 3.3: Create shared/__init__.py exports

**Files:**
- Modify: `app/shared/__init__.py`

**Step 1: Add exports**

```python
# app/shared/__init__.py
"""Shared module exports."""

from app.shared.exceptions import (
    ConfigurationError,
    DatabaseError,
    ExternalAPIError,
    MarketSelectionRequiredError,
    OpenAIAPIError,
    PolymarketAPIError,
    ProphilyError,
    TavilyAPIError,
    ValidationError,
)
from app.shared.types import (
    ConfidenceLevel,
    Decision,
    DecisionAction,
    EventContext,
    EventDocument,
    Horizon,
    MarketDocument,
    MarketSnapshot,
    NewsArticle,
    NewsContext,
    ReportBlock,
    RunDocument,
    RunEnvMetadata,
    RunStatus,
    Signal,
    SignalDirection,
    StrategyParams,
    StrategyPreset,
    TraceDocument,
)

__all__ = [
    # Exceptions
    "ConfigurationError",
    "DatabaseError",
    "ExternalAPIError",
    "MarketSelectionRequiredError",
    "OpenAIAPIError",
    "PolymarketAPIError",
    "ProphilyError",
    "TavilyAPIError",
    "ValidationError",
    # Types
    "ConfidenceLevel",
    "Decision",
    "DecisionAction",
    "EventContext",
    "EventDocument",
    "Horizon",
    "MarketDocument",
    "MarketSnapshot",
    "NewsArticle",
    "NewsContext",
    "ReportBlock",
    "RunDocument",
    "RunEnvMetadata",
    "RunStatus",
    "Signal",
    "SignalDirection",
    "StrategyParams",
    "StrategyPreset",
    "TraceDocument",
]
```

**Step 2: Commit**

```bash
git add app/shared/__init__.py
git commit -m "feat(shared): add module exports"
```

---

## Phase 4: Infrastructure Layer

### Task 4.1: Create infrastructure/database/client.py

**Files:**
- Create: `app/infrastructure/database/client.py`
- Source: `app/db/async_client.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/db/async_client.py app/infrastructure/database/client.py
```

**Step 2: Update imports in the new file**

Replace:
```python
from app.config import settings
from app.core.logging_config import get_logger
```

With:
```python
from app.config import get_logger, settings
```

**Step 3: Commit**

```bash
git add app/infrastructure/database/client.py
git commit -m "feat(infrastructure): add database client"
```

### Task 4.2: Create infrastructure/database/repositories.py

**Files:**
- Create: `app/infrastructure/database/repositories.py`
- Source: `app/db/async_repositories.py` (entire file)

**Step 1: Copy file**

```bash
cp app/db/async_repositories.py app/infrastructure/database/repositories.py
```

**Step 2: Update imports in the new file**

Replace:
```python
from app.core.logging_config import get_logger
from app.db.async_client import get_async_db
from app.db.models import ...
```

With:
```python
from app.config import get_logger
from app.infrastructure.database.client import get_async_db
from app.shared.types import ...
```

**Step 3: Commit**

```bash
git add app/infrastructure/database/repositories.py
git commit -m "feat(infrastructure): add database repositories"
```

### Task 4.3: Create infrastructure/database/utils.py

**Files:**
- Create: `app/infrastructure/database/utils.py`
- Source: `app/db/utils.py` (entire file)

**Step 1: Copy file**

```bash
cp app/db/utils.py app/infrastructure/database/utils.py
```

**Step 2: Commit**

```bash
git add app/infrastructure/database/utils.py
git commit -m "feat(infrastructure): add database utils"
```

### Task 4.4: Create infrastructure/database/__init__.py exports

**Files:**
- Modify: `app/infrastructure/database/__init__.py`

**Step 1: Add exports**

```python
# app/infrastructure/database/__init__.py
"""Database infrastructure exports."""

from app.infrastructure.database.client import get_async_db
from app.infrastructure.database.repositories import (
    EventRepository,
    MarketRepository,
    RunRepository,
    TraceRepository,
)
from app.infrastructure.database.utils import ensure_object_id, serialize_doc

__all__ = [
    "EventRepository",
    "MarketRepository",
    "RunRepository",
    "TraceRepository",
    "ensure_object_id",
    "get_async_db",
    "serialize_doc",
]
```

**Step 2: Commit**

```bash
git add app/infrastructure/database/__init__.py
git commit -m "feat(infrastructure): add database module exports"
```

### Task 4.5: Create infrastructure/http/cache.py

**Files:**
- Create: `app/infrastructure/http/cache.py`
- Source: `app/core/cache.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/core/cache.py app/infrastructure/http/cache.py
```

**Step 2: Update imports in the new file**

Replace:
```python
from app.config import settings
from app.core.logging_config import get_logger
```

With:
```python
from app.config import get_logger, settings
```

**Step 3: Commit**

```bash
git add app/infrastructure/http/cache.py
git commit -m "feat(infrastructure): add HTTP cache layer"
```

### Task 4.6: Create infrastructure/http/resilience.py

**Files:**
- Create: `app/infrastructure/http/resilience.py`
- Source: `app/core/resilience.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/core/resilience.py app/infrastructure/http/resilience.py
```

**Step 2: Update imports in the new file**

Replace:
```python
from app.core.logging_config import get_logger
```

With:
```python
from app.config import get_logger
```

**Step 3: Commit**

```bash
git add app/infrastructure/http/resilience.py
git commit -m "feat(infrastructure): add HTTP resilience (circuit breaker, retry)"
```

### Task 4.7: Create infrastructure/http/polymarket.py

**Files:**
- Create: `app/infrastructure/http/polymarket.py`
- Source: `app/core/polymarket_utils.py` lines 349-429 (async HTTP functions)
- Source: `app/services/polymarket_client.py` (entire file)

**Step 1: Create polymarket.py with HTTP functions**

```python
# app/infrastructure/http/polymarket.py
"""Polymarket HTTP client with caching and resilience."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientTimeout

from app.config import PolymarketAPI, get_logger
from app.infrastructure.http.cache import polymarket_cache
from app.infrastructure.http.resilience import polymarket_circuit, with_async_retry

logger = get_logger(__name__)

GAMMA_API = PolymarketAPI.GAMMA_API
CLOB_API = PolymarketAPI.CLOB_API


async def _fetch_json_impl_async(
    url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10
) -> Any:
    """Internal async implementation of fetch_json with aiohttp."""
    logger.debug("Fetching JSON (async)", url=url, params=params)
    timeout_obj = ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_obj) as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()


async def fetch_json_async(
    url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10
) -> Any:
    """Fetch JSON from URL with caching, retry, and circuit breaker protection (async)."""
    # Create cache key
    cache_key = f"polymarket:{url}:{hash(str(params))}"

    # Try cache first
    cached_result = polymarket_cache.get(cache_key)
    if cached_result is not None:
        logger.debug("Cache hit for Polymarket API (async)", url=url)
        return cached_result

    # Check circuit breaker
    if not polymarket_circuit.can_attempt():
        logger.warning("Circuit breaker open for Polymarket (async)", url=url)
        raise RuntimeError("Circuit breaker is OPEN for Polymarket API")

    # Cache miss - fetch with retry and circuit breaker
    try:
        result = await with_async_retry(
            _fetch_json_impl_async,
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            url=url,
            params=params,
            timeout=timeout,
        )
        # Cache successful result
        polymarket_cache.set(cache_key, result)
        polymarket_circuit.record_success()
        logger.debug("Cache miss - fetched and cached (async)", url=url)
        return result
    except Exception as e:
        polymarket_circuit.record_failure()
        logger.warning("Failed to fetch from Polymarket API (async)", url=url, error=str(e))
        raise


def normalize_number(v: Any) -> Optional[float]:
    """Normalize a value to float."""
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        return float(str(v))
    except Exception:
        return None


async def fetch_order_book_async(token_id: str) -> Dict[str, Any]:
    """Fetch order book with caching and error handling (async)."""
    try:
        data = await fetch_json_async(f"{CLOB_API}/book", params={"token_id": token_id})

        def map_levels(levels: List[Dict[str, Any]]) -> List[Dict[str, float]]:
            out: List[Dict[str, float]] = []
            for lvl in levels or []:
                p = normalize_number(lvl.get("price"))
                s = normalize_number(lvl.get("size"))
                if p is not None and s is not None:
                    out.append({"price": p, "size": s})
            return out

        bids = map_levels(data.get("bids", []))
        asks = map_levels(data.get("asks", []))
        best_bid = bids[0]["price"] if bids else None
        best_ask = asks[0]["price"] if asks else None
        return {"bids": bids, "asks": asks, "best_bid": best_bid, "best_ask": best_ask}
    except Exception as e:
        logger.warning("Failed to fetch order book (async)", token_id=token_id, error=str(e))
        # Return empty order book instead of crashing
        return {"bids": [], "asks": [], "best_bid": None, "best_ask": None}
```

**Step 2: Commit**

```bash
git add app/infrastructure/http/polymarket.py
git commit -m "feat(infrastructure): add Polymarket HTTP client"
```

### Task 4.8: Create infrastructure/http/tavily.py

**Files:**
- Create: `app/infrastructure/http/tavily.py`
- Source: `app/services/tavily_client.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/services/tavily_client.py app/infrastructure/http/tavily.py
```

**Step 2: Update imports in the new file**

Replace:
```python
from app.config import settings
from app.core.logging_config import get_logger
from app.core.cache import tavily_cache
from app.core.resilience import ...
```

With:
```python
from app.config import get_logger, settings
from app.infrastructure.http.cache import tavily_cache
from app.infrastructure.http.resilience import ...
```

**Step 3: Commit**

```bash
git add app/infrastructure/http/tavily.py
git commit -m "feat(infrastructure): add Tavily HTTP client"
```

### Task 4.9: Create infrastructure/http/__init__.py exports

**Files:**
- Modify: `app/infrastructure/http/__init__.py`

**Step 1: Add exports**

```python
# app/infrastructure/http/__init__.py
"""HTTP infrastructure exports."""

from app.infrastructure.http.cache import (
    CacheBackend,
    InMemoryCache,
    RedisCache,
    polymarket_cache,
    tavily_cache,
)
from app.infrastructure.http.polymarket import (
    fetch_json_async,
    fetch_order_book_async,
    normalize_number,
)
from app.infrastructure.http.resilience import (
    CircuitBreaker,
    openai_circuit,
    polymarket_circuit,
    tavily_circuit,
    with_async_retry,
)
from app.infrastructure.http.tavily import TavilyClient

__all__ = [
    "CacheBackend",
    "CircuitBreaker",
    "InMemoryCache",
    "RedisCache",
    "TavilyClient",
    "fetch_json_async",
    "fetch_order_book_async",
    "normalize_number",
    "openai_circuit",
    "polymarket_cache",
    "polymarket_circuit",
    "tavily_cache",
    "tavily_circuit",
    "with_async_retry",
]
```

**Step 2: Commit**

```bash
git add app/infrastructure/http/__init__.py
git commit -m "feat(infrastructure): add HTTP module exports"
```

### Task 4.10: Create infrastructure/llm/client.py

**Files:**
- Create: `app/infrastructure/llm/client.py`
- Source: `app/services/openai_client.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/services/openai_client.py app/infrastructure/llm/client.py
```

**Step 2: Update imports in the new file**

Replace:
```python
from app.config import settings
from app.core.logging_config import get_logger
from app.core.resilience import openai_circuit
```

With:
```python
from app.config import get_logger, settings
from app.infrastructure.http.resilience import openai_circuit
```

**Step 3: Commit**

```bash
git add app/infrastructure/llm/client.py
git commit -m "feat(infrastructure): add OpenAI LLM client"
```

### Task 4.11: Create infrastructure/llm/__init__.py exports

**Files:**
- Modify: `app/infrastructure/llm/__init__.py`

**Step 1: Add exports**

```python
# app/infrastructure/llm/__init__.py
"""LLM infrastructure exports."""

from app.infrastructure.llm.client import OpenAIClient, get_openai_client

__all__ = [
    "OpenAIClient",
    "get_openai_client",
]
```

**Step 2: Commit**

```bash
git add app/infrastructure/llm/__init__.py
git commit -m "feat(infrastructure): add LLM module exports"
```

### Task 4.12: Create infrastructure/__init__.py exports

**Files:**
- Modify: `app/infrastructure/__init__.py`

**Step 1: Add exports**

```python
# app/infrastructure/__init__.py
"""Infrastructure layer exports."""

from app.infrastructure.database import (
    EventRepository,
    MarketRepository,
    RunRepository,
    TraceRepository,
    get_async_db,
)
from app.infrastructure.http import (
    TavilyClient,
    fetch_json_async,
    fetch_order_book_async,
    polymarket_cache,
    polymarket_circuit,
    tavily_cache,
    tavily_circuit,
)
from app.infrastructure.llm import OpenAIClient, get_openai_client

__all__ = [
    # Database
    "EventRepository",
    "MarketRepository",
    "RunRepository",
    "TraceRepository",
    "get_async_db",
    # HTTP
    "TavilyClient",
    "fetch_json_async",
    "fetch_order_book_async",
    "polymarket_cache",
    "polymarket_circuit",
    "tavily_cache",
    "tavily_circuit",
    # LLM
    "OpenAIClient",
    "get_openai_client",
]
```

**Step 2: Commit**

```bash
git add app/infrastructure/__init__.py
git commit -m "feat(infrastructure): add top-level module exports"
```

---

## Phase 5: Markets Domain

### Task 5.1: Create domains/markets/schemas.py

**Files:**
- Create: `app/domains/markets/schemas.py`
- Source: `app/schemas/polymarket.py` (entire file)

**Step 1: Copy file**

```bash
cp app/schemas/polymarket.py app/domains/markets/schemas.py
```

**Step 2: Commit**

```bash
git add app/domains/markets/schemas.py
git commit -m "feat(markets): add Pydantic schemas"
```

### Task 5.2: Create domains/markets/parsing.py

**Files:**
- Create: `app/domains/markets/parsing.py`
- Source: `app/core/polymarket_utils.py` (URL parsing, price parsing functions)

**Step 1: Create parsing.py**

```python
# app/domains/markets/parsing.py
"""URL and price parsing utilities for Polymarket."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


def extract_slug_from_url(url: str | None) -> Optional[str]:
    """Extract market/event slug from Polymarket URL."""
    if not url:
        return None
    try:
        # Basic validation: URL should contain "://" or "/" to be considered a URL
        if "://" not in url and "/" not in url and not url.startswith("http"):
            return None
        url_no_scheme = re.sub(r"^https?://", "", url)
        url_no_qf = re.split(r"[?#]", url_no_scheme)[0]
        path = url_no_qf.split("/", 1)[-1]
        parts = [p for p in path.split("/") if p]
        if not parts:
            return None
        return parts[-1]
    except Exception:
        return None


def parse_prices_from_market(market: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """Parse YES/NO prices from market data."""
    yes_price = market.get("yes_price")
    no_price = market.get("no_price")
    if isinstance(yes_price, (int, float)) and isinstance(no_price, (int, float)):
        return float(yes_price), float(no_price)

    outcome_prices = market.get("outcomePrices")
    if outcome_prices:
        # Handle list format directly
        if isinstance(outcome_prices, list) and len(outcome_prices) >= 2:
            try:
                yes = float(outcome_prices[0])
                no = float(outcome_prices[1])
                return yes, no
            except (ValueError, TypeError):
                pass
        # Handle JSON string format
        elif isinstance(outcome_prices, str) and outcome_prices.startswith("["):
            try:
                arr = json.loads(outcome_prices)
                if isinstance(arr, list) and len(arr) >= 2:
                    yes = float(arr[0])
                    no = float(arr[1])
                    return yes, no
            except Exception:
                pass

    return None, None


def normalize_number(v: Any) -> Optional[float]:
    """Normalize a value to float."""
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        return float(str(v))
    except Exception:
        return None


def parse_end_date(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO date string to datetime."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except Exception:
        return None
```

**Step 2: Commit**

```bash
git add app/domains/markets/parsing.py
git commit -m "feat(markets): add URL and price parsing utilities"
```

### Task 5.3: Create domains/markets/fetcher.py

**Files:**
- Create: `app/domains/markets/fetcher.py`
- Source: `app/core/polymarket_utils.py` (get_event_and_markets_by_slug function)

**Step 1: Create fetcher.py with the main fetching logic**

Copy the `get_event_and_markets_by_slug` function and `_extract_series_comment_count` helper from `app/core/polymarket_utils.py` (lines 25-293).

Update imports to:
```python
from app.config import PolymarketAPI, get_logger
from app.domains.markets.schemas import Event, Market
from app.infrastructure.http import fetch_json_async
```

**Step 2: Commit**

```bash
git add app/domains/markets/fetcher.py
git commit -m "feat(markets): add market/event fetcher"
```

### Task 5.4: Create domains/markets/transformer.py

**Files:**
- Create: `app/domains/markets/transformer.py`
- Source: `app/core/market_transformer.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/core/market_transformer.py app/domains/markets/transformer.py
```

**Step 2: Update imports**

Replace old imports with:
```python
from app.config import get_logger
from app.domains.markets.parsing import normalize_number, parse_end_date, parse_prices_from_market
from app.shared.types import MarketDocument, MarketSnapshot
```

**Step 3: Commit**

```bash
git add app/domains/markets/transformer.py
git commit -m "feat(markets): add market data transformer"
```

### Task 5.5: Create domains/markets/selector.py

**Files:**
- Create: `app/domains/markets/selector.py`
- Source: `app/core/market_selector.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/core/market_selector.py app/domains/markets/selector.py
```

**Step 2: Update imports**

Replace old imports with:
```python
from app.config import get_logger
```

**Step 3: Commit**

```bash
git add app/domains/markets/selector.py
git commit -m "feat(markets): add market selector"
```

### Task 5.6: Create domains/markets/service.py

**Files:**
- Create: `app/domains/markets/service.py`
- Source: `app/agents/market_agent.py` (business logic, not agent wrapper)

**Step 1: Extract business logic from market_agent.py into a MarketService class**

Create a `MarketService` class that contains the core logic for:
- Fetching market data
- Building market snapshots
- Handling market selection

**Step 2: Commit**

```bash
git add app/domains/markets/service.py
git commit -m "feat(markets): add MarketService"
```

### Task 5.7: Create domains/markets/event_service.py

**Files:**
- Create: `app/domains/markets/event_service.py`
- Source: `app/agents/event_agent.py` (business logic)

**Step 1: Extract business logic from event_agent.py into an EventService class**

**Step 2: Commit**

```bash
git add app/domains/markets/event_service.py
git commit -m "feat(markets): add EventService"
```

### Task 5.8: Create domains/markets/__init__.py exports

**Files:**
- Modify: `app/domains/markets/__init__.py`

**Step 1: Add exports**

```python
# app/domains/markets/__init__.py
"""Markets domain exports."""

from app.domains.markets.event_service import EventService
from app.domains.markets.fetcher import get_event_and_markets_by_slug
from app.domains.markets.parsing import (
    extract_slug_from_url,
    normalize_number,
    parse_end_date,
    parse_prices_from_market,
)
from app.domains.markets.schemas import Event, Market
from app.domains.markets.selector import select_market
from app.domains.markets.service import MarketService
from app.domains.markets.transformer import build_market_snapshot, transform_market

__all__ = [
    "Event",
    "EventService",
    "Market",
    "MarketService",
    "build_market_snapshot",
    "extract_slug_from_url",
    "get_event_and_markets_by_slug",
    "normalize_number",
    "parse_end_date",
    "parse_prices_from_market",
    "select_market",
    "transform_market",
]
```

**Step 2: Commit**

```bash
git add app/domains/markets/__init__.py
git commit -m "feat(markets): add domain exports"
```

---

## Phase 6: News Domain

### Task 6.1: Create domains/news/schemas.py

**Files:**
- Create: `app/domains/news/schemas.py`
- Source: `app/schemas/tavily.py` (entire file)

**Step 1: Copy file**

```bash
cp app/schemas/tavily.py app/domains/news/schemas.py
```

**Step 2: Commit**

```bash
git add app/domains/news/schemas.py
git commit -m "feat(news): add Pydantic schemas"
```

### Task 6.2: Create domains/news/sentiment/patterns.py

**Files:**
- Create: `app/domains/news/sentiment/patterns.py`
- Source: `app/core/sentiment_analyzer.py` (pattern lists)

**Step 1: Create patterns.py with keyword constants**

```python
# app/domains/news/sentiment/patterns.py
"""Sentiment analysis keyword patterns."""

# Bullish keywords (support YES outcome)
BULLISH_PATTERNS = [
    # Price/movement up
    "increase", "increased", "increasing", "rise", "rises", "rising", "rose",
    "up", "higher", "high", "grow", "growing", "grew", "gain", "gained", "gains",
    "surge", "surged", "surges", "rally", "rallied", "rallies", "soar", "soared",
    "jump", "jumped", "jumps", "climb", "climbed", "climbs", "boost", "boosted",
    # Positive sentiment
    "positive", "optimistic", "optimism", "strong", "strength", "stronger",
    "beat", "beats", "beaten", "exceed", "exceeded", "exceeds",
    "outperform", "outperformed", "outperforms", "success", "successful",
    "succeed", "succeeded",
    # Approval/support
    "approve", "approved", "approval", "pass", "passed", "passes",
    "support", "supported", "supports", "favor", "favored", "favors",
    "win", "won", "wins", "victory", "victories", "triumph", "triumphs",
    # Monetary policy (dovish = bullish for rate cut markets)
    "cut rates", "rate cut", "rate cuts", "lower rates", "dovish",
    "stimulus", "easing", "ease", "eased", "quantitative easing", "qe",
    "accommodative",
    # Market positive
    "bullish", "bull market", "rally", "breakthrough", "milestone", "record high",
]

# Bearish keywords (support NO outcome)
BEARISH_PATTERNS = [
    # Price/movement down
    "decrease", "decreased", "decreasing", "fall", "falls", "fell", "fallen",
    "down", "lower", "low", "decline", "declined", "declines",
    "drop", "dropped", "drops", "plunge", "plunged", "plunges",
    "crash", "crashed", "crashes", "collapse", "collapsed", "collapses",
    "sink", "sank", "sinks", "slump", "slumped", "slumps",
    "dip", "dipped", "dips", "slide", "slid", "slides",
    # Negative sentiment
    "negative", "negatively", "pessimistic", "pessimism",
    "weak", "weaker", "weakness", "miss", "missed", "misses",
    "underperform", "underperformed", "underperforms",
    "disappoint", "disappointed", "disappoints", "disappointment",
    "concern", "concerns", "concerned", "worry", "worries", "worried",
    # Rejection/failure
    "reject", "rejected", "rejects", "rejection",
    "fail", "failed", "fails", "failure",
    "oppose", "opposed", "opposes", "opposition", "against",
    "loss", "losses", "lost", "defeat", "defeated", "defeats",
    # Monetary policy (hawkish = bearish for rate cut markets)
    "raise rates", "rate hike", "rate hikes", "hike rates", "hawkish",
    "tighten", "tightened", "tightening", "restrictive", "restriction", "restrictions",
    # Market negative
    "bearish", "bear market", "correction", "corrections",
    "volatility", "uncertainty", "risk", "risks", "risky",
    "threat", "threats", "threaten", "threatened",
]

# Negation words that flip sentiment
NEGATION_WORDS = [
    "not", "no", "never", "neither", "nobody", "none", "nothing",
    "nowhere", "without", "lack", "lacks", "lacking",
]
```

**Step 2: Commit**

```bash
git add app/domains/news/sentiment/patterns.py
git commit -m "feat(news): add sentiment keyword patterns"
```

### Task 6.3: Create domains/news/sentiment/analyzer.py

**Files:**
- Create: `app/domains/news/sentiment/analyzer.py`
- Source: `app/core/sentiment_analyzer.py` (analysis functions)

**Step 1: Create analyzer.py with analysis logic**

Copy `analyze_article_sentiment` and `analyze_articles_sentiment` functions, updating imports to use patterns from `patterns.py`.

**Step 2: Commit**

```bash
git add app/domains/news/sentiment/analyzer.py
git commit -m "feat(news): add sentiment analyzer"
```

### Task 6.4: Create domains/news/sentiment/__init__.py exports

**Files:**
- Modify: `app/domains/news/sentiment/__init__.py`

**Step 1: Add exports**

```python
# app/domains/news/sentiment/__init__.py
"""Sentiment analysis exports."""

from app.domains.news.sentiment.analyzer import (
    analyze_article_sentiment,
    analyze_articles_sentiment,
)
from app.domains.news.sentiment.patterns import (
    BEARISH_PATTERNS,
    BULLISH_PATTERNS,
    NEGATION_WORDS,
)

__all__ = [
    "BEARISH_PATTERNS",
    "BULLISH_PATTERNS",
    "NEGATION_WORDS",
    "analyze_article_sentiment",
    "analyze_articles_sentiment",
]
```

**Step 2: Commit**

```bash
git add app/domains/news/sentiment/__init__.py
git commit -m "feat(news): add sentiment module exports"
```

### Task 6.5: Create domains/news/query_generator.py

**Files:**
- Create: `app/domains/news/query_generator.py`
- Source: `app/agents/tavily_prompt_agent.py` (query generation logic)

**Step 1: Extract query generation logic from tavily_prompt_agent.py**

**Step 2: Commit**

```bash
git add app/domains/news/query_generator.py
git commit -m "feat(news): add search query generator"
```

### Task 6.6: Create domains/news/fetcher.py

**Files:**
- Create: `app/domains/news/fetcher.py`
- Source: `app/agents/news_agent.py` (article fetching logic)

**Step 1: Extract article fetching and deduplication logic**

**Step 2: Commit**

```bash
git add app/domains/news/fetcher.py
git commit -m "feat(news): add article fetcher"
```

### Task 6.7: Create domains/news/summarizer.py

**Files:**
- Create: `app/domains/news/summarizer.py`
- Source: `app/agents/news_summary_agent.py` (summarization logic)

**Step 1: Extract summarization logic**

**Step 2: Commit**

```bash
git add app/domains/news/summarizer.py
git commit -m "feat(news): add news summarizer"
```

### Task 6.8: Create domains/news/service.py

**Files:**
- Create: `app/domains/news/service.py`
- Source: `app/agents/news_agent.py` (orchestration logic)

**Step 1: Create NewsService class orchestrating fetching, sentiment, summarization**

**Step 2: Commit**

```bash
git add app/domains/news/service.py
git commit -m "feat(news): add NewsService"
```

### Task 6.9: Create domains/news/__init__.py exports

**Files:**
- Modify: `app/domains/news/__init__.py`

**Step 1: Add exports**

```python
# app/domains/news/__init__.py
"""News domain exports."""

from app.domains.news.fetcher import fetch_articles
from app.domains.news.query_generator import generate_search_queries
from app.domains.news.schemas import TavilyQuerySpec, TavilyResponse
from app.domains.news.sentiment import analyze_article_sentiment, analyze_articles_sentiment
from app.domains.news.service import NewsService
from app.domains.news.summarizer import summarize_news

__all__ = [
    "NewsService",
    "TavilyQuerySpec",
    "TavilyResponse",
    "analyze_article_sentiment",
    "analyze_articles_sentiment",
    "fetch_articles",
    "generate_search_queries",
    "summarize_news",
]
```

**Step 2: Commit**

```bash
git add app/domains/news/__init__.py
git commit -m "feat(news): add domain exports"
```

---

## Phase 7: Analysis Domain

### Task 7.1: Create domains/analysis/schemas.py

**Files:**
- Create: `app/domains/analysis/schemas.py`
- Source: `app/schemas/api.py` (Signal, StrategyParamsModel)

**Step 1: Extract Signal and StrategyParamsModel from api.py**

**Step 2: Commit**

```bash
git add app/domains/analysis/schemas.py
git commit -m "feat(analysis): add Pydantic schemas"
```

### Task 7.2: Create domains/analysis/calculations.py

**Files:**
- Create: `app/domains/analysis/calculations.py`
- Source: `app/core/signal_utils.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/core/signal_utils.py app/domains/analysis/calculations.py
```

**Step 2: Update imports**

**Step 3: Commit**

```bash
git add app/domains/analysis/calculations.py
git commit -m "feat(analysis): add edge/Kelly calculations"
```

### Task 7.3: Create domains/analysis/presets.py

**Files:**
- Create: `app/domains/analysis/presets.py`
- Source: `app/agents/strategy_agent.py` (preset definitions)

**Step 1: Extract strategy preset constants**

```python
# app/domains/analysis/presets.py
"""Strategy preset configurations."""

from app.shared.types import StrategyParams

CAUTIOUS: StrategyParams = {
    "min_edge_pct": 0.08,
    "min_confidence": "high",
    "max_capital_pct": 0.08,
    "max_kelly_fraction": 0.15,
    "risk_off": False,
}

BALANCED: StrategyParams = {
    "min_edge_pct": 0.05,
    "min_confidence": "medium",
    "max_capital_pct": 0.15,
    "max_kelly_fraction": 0.25,
    "risk_off": False,
}

AGGRESSIVE: StrategyParams = {
    "min_edge_pct": 0.03,
    "min_confidence": "low",
    "max_capital_pct": 0.25,
    "max_kelly_fraction": 0.5,
    "risk_off": False,
}

PRESETS = {
    "Cautious": CAUTIOUS,
    "Balanced": BALANCED,
    "Aggressive": AGGRESSIVE,
}


def get_preset(name: str) -> StrategyParams:
    """Get strategy preset by name."""
    return PRESETS.get(name, BALANCED)
```

**Step 2: Commit**

```bash
git add app/domains/analysis/presets.py
git commit -m "feat(analysis): add strategy presets"
```

### Task 7.4: Create domains/analysis/sizing.py

**Files:**
- Create: `app/domains/analysis/sizing.py`
- Source: `app/agents/strategy_agent.py` (position sizing logic)

**Step 1: Extract position sizing functions**

**Step 2: Commit**

```bash
git add app/domains/analysis/sizing.py
git commit -m "feat(analysis): add position sizing"
```

### Task 7.5: Create domains/analysis/decision.py

**Files:**
- Create: `app/domains/analysis/decision.py`
- Source: `app/agents/strategy_agent.py` (decision rules)

**Step 1: Extract buy/sell/hold decision logic**

**Step 2: Commit**

```bash
git add app/domains/analysis/decision.py
git commit -m "feat(analysis): add trading decision logic"
```

### Task 7.6: Create domains/analysis/probability.py

**Files:**
- Create: `app/domains/analysis/probability.py`
- Source: `app/agents/prob_agent.py` (probability estimation logic)

**Step 1: Extract probability estimation logic**

**Step 2: Commit**

```bash
git add app/domains/analysis/probability.py
git commit -m "feat(analysis): add probability estimation"
```

### Task 7.7: Create domains/analysis/service.py

**Files:**
- Create: `app/domains/analysis/service.py`
- Source: `app/agents/strategy_agent.py` (orchestration)

**Step 1: Create AnalysisService class**

**Step 2: Commit**

```bash
git add app/domains/analysis/service.py
git commit -m "feat(analysis): add AnalysisService"
```

### Task 7.8: Create domains/analysis/__init__.py exports

**Files:**
- Modify: `app/domains/analysis/__init__.py`

**Step 1: Add exports**

**Step 2: Commit**

```bash
git add app/domains/analysis/__init__.py
git commit -m "feat(analysis): add domain exports"
```

---

## Phase 8: Reports Domain

### Task 8.1: Create domains/reports/schemas.py

**Files:**
- Create: `app/domains/reports/schemas.py`
- Source: `app/schemas/api.py` (ReportSection)

**Step 1: Extract ReportSection from api.py**

**Step 2: Commit**

```bash
git add app/domains/reports/schemas.py
git commit -m "feat(reports): add Pydantic schemas"
```

### Task 8.2: Create domains/reports/prompts.py

**Files:**
- Create: `app/domains/reports/prompts.py`
- Source: `app/agents/report_agent.py` (prompt strings)

**Step 1: Extract LLM prompt templates**

**Step 2: Commit**

```bash
git add app/domains/reports/prompts.py
git commit -m "feat(reports): add LLM prompts"
```

### Task 8.3: Create domains/reports/templates.py

**Files:**
- Create: `app/domains/reports/templates.py`
- Source: `app/agents/report_agent.py` (fallback templates)

**Step 1: Extract fallback template generation**

**Step 2: Commit**

```bash
git add app/domains/reports/templates.py
git commit -m "feat(reports): add fallback templates"
```

### Task 8.4: Create domains/reports/generator.py

**Files:**
- Create: `app/domains/reports/generator.py`
- Source: `app/agents/report_agent.py` (LLM generation)

**Step 1: Extract LLM report generation logic**

**Step 2: Commit**

```bash
git add app/domains/reports/generator.py
git commit -m "feat(reports): add LLM report generator"
```

### Task 8.5: Create domains/reports/formatter.py

**Files:**
- Create: `app/domains/reports/formatter.py`
- Source: `app/agents/report_agent.py` (formatting)

**Step 1: Extract markdown/output formatting**

**Step 2: Commit**

```bash
git add app/domains/reports/formatter.py
git commit -m "feat(reports): add report formatter"
```

### Task 8.6: Create domains/reports/service.py

**Files:**
- Create: `app/domains/reports/service.py`
- Source: `app/agents/report_agent.py` (orchestration)

**Step 1: Create ReportService class**

**Step 2: Commit**

```bash
git add app/domains/reports/service.py
git commit -m "feat(reports): add ReportService"
```

### Task 8.7: Create domains/reports/__init__.py exports

**Files:**
- Modify: `app/domains/reports/__init__.py`

**Step 1: Add exports**

**Step 2: Commit**

```bash
git add app/domains/reports/__init__.py
git commit -m "feat(reports): add domain exports"
```

---

## Phase 9: Orchestration Layer

### Task 9.1: Create orchestration/state.py

**Files:**
- Create: `app/orchestration/state.py`
- Source: `app/agents/state.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/agents/state.py app/orchestration/state.py
```

**Step 2: Update imports to use new paths**

**Step 3: Commit**

```bash
git add app/orchestration/state.py
git commit -m "feat(orchestration): add AgentState"
```

### Task 9.2: Create orchestration/agents/*.py (thin wrappers)

**Files:**
- Create: `app/orchestration/agents/market.py`
- Create: `app/orchestration/agents/event.py`
- Create: `app/orchestration/agents/search_planner.py`
- Create: `app/orchestration/agents/article_fetcher.py`
- Create: `app/orchestration/agents/summarizer.py`
- Create: `app/orchestration/agents/probability.py`
- Create: `app/orchestration/agents/strategy.py`
- Create: `app/orchestration/agents/report.py`

**Step 1: Create thin wrapper for each agent**

Example for market.py:
```python
# app/orchestration/agents/market.py
"""Market agent - thin wrapper calling MarketService."""

from app.config import get_logger
from app.domains.markets import MarketService
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_market_agent(state: AgentState) -> AgentState:
    """Execute market agent: fetch and build market snapshot."""
    logger.info("Running market agent", run_id=state.get("run_id"))

    service = MarketService()
    result = await service.process(state)

    return {**state, **result}
```

**Step 2: Commit each agent**

```bash
git add app/orchestration/agents/
git commit -m "feat(orchestration): add thin agent wrappers"
```

### Task 9.3: Create orchestration/graph.py

**Files:**
- Create: `app/orchestration/graph.py`
- Source: `app/agents/graph.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/agents/graph.py app/orchestration/graph.py
```

**Step 2: Update imports to use new agent paths**

**Step 3: Commit**

```bash
git add app/orchestration/graph.py
git commit -m "feat(orchestration): add LangGraph wiring"
```

### Task 9.4: Create orchestration/phased.py

**Files:**
- Create: `app/orchestration/phased.py`
- Source: `app/services/phased_analysis.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/services/phased_analysis.py app/orchestration/phased.py
```

**Step 2: Update imports**

**Step 3: Commit**

```bash
git add app/orchestration/phased.py
git commit -m "feat(orchestration): add phased analysis"
```

### Task 9.5: Create orchestration/snapshot.py

**Files:**
- Create: `app/orchestration/snapshot.py`
- Source: `app/services/run_snapshot.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/services/run_snapshot.py app/orchestration/snapshot.py
```

**Step 2: Update imports**

**Step 3: Commit**

```bash
git add app/orchestration/snapshot.py
git commit -m "feat(orchestration): add run snapshot persistence"
```

### Task 9.6: Create orchestration/__init__.py exports

**Files:**
- Modify: `app/orchestration/__init__.py`

**Step 1: Add exports**

**Step 2: Commit**

```bash
git add app/orchestration/__init__.py
git commit -m "feat(orchestration): add module exports"
```

---

## Phase 10: API Layer

### Task 10.1: Create api/schemas/requests.py

**Files:**
- Create: `app/api/schemas/requests.py`
- Source: `app/schemas/api.py` (AnalyzeRequest, AnalysisConfiguration)

**Step 1: Extract request schemas**

**Step 2: Commit**

```bash
git add app/api/schemas/requests.py
git commit -m "feat(api): add request schemas"
```

### Task 10.2: Create api/schemas/responses.py

**Files:**
- Create: `app/api/schemas/responses.py`
- Source: `app/schemas/api.py` (response models)

**Step 1: Extract response schemas**

**Step 2: Commit**

```bash
git add app/api/schemas/responses.py
git commit -m "feat(api): add response schemas"
```

### Task 10.3: Create api/schemas/common.py

**Files:**
- Create: `app/api/schemas/common.py`
- Source: `app/schemas/api.py` (HealthResponse, ErrorResponse)

**Step 1: Extract common schemas**

**Step 2: Commit**

```bash
git add app/api/schemas/common.py
git commit -m "feat(api): add common schemas"
```

### Task 10.4: Create api/dependencies.py

**Files:**
- Create: `app/api/dependencies.py`
- Source: `app/core/dependencies.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/core/dependencies.py app/api/dependencies.py
```

**Step 2: Commit**

```bash
git add app/api/dependencies.py
git commit -m "feat(api): add FastAPI dependencies"
```

### Task 10.5: Create api/routes/health.py

**Files:**
- Create: `app/api/routes/health.py`
- Source: `app/main.py` (health endpoints)

**Step 1: Extract health endpoints from main.py**

**Step 2: Commit**

```bash
git add app/api/routes/health.py
git commit -m "feat(api): add health routes"
```

### Task 10.6: Create api/routes/analyze.py

**Files:**
- Create: `app/api/routes/analyze.py`
- Source: `app/routes/analyze.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/routes/analyze.py app/api/routes/analyze.py
```

**Step 2: Update imports to new paths**

**Step 3: Commit**

```bash
git add app/api/routes/analyze.py
git commit -m "feat(api): add analyze routes"
```

### Task 10.7: Create api/routes/runs.py

**Files:**
- Create: `app/api/routes/runs.py`
- Source: `app/routes/runs.py` (entire file)

**Step 1: Copy and update imports**

```bash
cp app/routes/runs.py app/api/routes/runs.py
```

**Step 2: Update imports**

**Step 3: Commit**

```bash
git add app/api/routes/runs.py
git commit -m "feat(api): add runs routes"
```

### Task 10.8: Update main.py

**Files:**
- Modify: `app/main.py`

**Step 1: Slim down main.py to import routers from new locations**

**Step 2: Commit**

```bash
git add app/main.py
git commit -m "refactor(api): slim down main.py to use new routes"
```

---

## Phase 11: Cleanup

### Task 11.1: Run full test suite

**Step 1: Run all tests**

```bash
cd /Users/kanagn/Desktop/tavilyatkalshi/prophecy-pred-markets/backend
pytest tests/ -v
```

Expected: All tests PASS

### Task 11.2: Remove old directories

**Files:**
- Remove: `app/agents/` (entire directory)
- Remove: `app/core/` (entire directory)
- Remove: `app/db/` (entire directory)
- Remove: `app/routes/` (entire directory)
- Remove: `app/schemas/` (entire directory)
- Remove: `app/services/` (entire directory)

**Step 1: Remove old directories**

```bash
rm -rf app/agents app/core app/db app/routes app/schemas app/services
```

**Step 2: Run tests again**

```bash
pytest tests/ -v
```

Expected: All tests PASS

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove old directory structure"
```

### Task 11.3: Move test_tavily.py to scripts

**Files:**
- Move: `test_tavily.py` → `scripts/test_tavily.py`

**Step 1: Move file**

```bash
mv test_tavily.py scripts/test_tavily.py
```

**Step 2: Commit**

```bash
git add -A
git commit -m "chore: move test_tavily.py to scripts"
```

### Task 11.4: Final verification

**Step 1: Run full test suite**

```bash
pytest tests/ -v --cov=app
```

Expected: All tests PASS with good coverage

**Step 2: Start dev server and verify it runs**

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Expected: Server starts without errors

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: backend restructuring complete"
```

---

## Phase 12: Reorganize Tests

### Task 12.1: Move tests to new structure

Move each test file to match the new app structure:

| Old Location | New Location |
|--------------|--------------|
| `tests/test_config.py` | `tests/unit/test_config.py` |
| `tests/test_cache.py` | `tests/unit/infrastructure/test_cache.py` |
| `tests/test_resilience.py` | `tests/unit/infrastructure/test_resilience.py` |
| `tests/test_async_client.py` | `tests/unit/infrastructure/test_database_client.py` |
| `tests/test_async_repositories.py` | `tests/unit/infrastructure/test_repositories.py` |
| `tests/test_market_agent.py` | `tests/unit/domains/markets/test_service.py` |
| `tests/test_event_agent.py` | `tests/unit/domains/markets/test_event_service.py` |
| `tests/test_market_transformer.py` | `tests/unit/domains/markets/test_transformer.py` |
| `tests/test_market_selector.py` | `tests/unit/domains/markets/test_selector.py` |
| `tests/test_polymarket_utils.py` | `tests/unit/domains/markets/test_fetcher.py` |
| `tests/test_news_agent.py` | `tests/unit/domains/news/test_service.py` |
| `tests/test_news_summary_agent.py` | `tests/unit/domains/news/test_summarizer.py` |
| `tests/test_tavily_prompt_agent.py` | `tests/unit/domains/news/test_query_generator.py` |
| `tests/test_prob_agent.py` | `tests/unit/domains/analysis/test_probability.py` |
| `tests/test_strategy_agent.py` | `tests/unit/domains/analysis/test_service.py` |
| `tests/test_signal_utils.py` | `tests/unit/domains/analysis/test_calculations.py` |
| `tests/test_report_agent.py` | `tests/unit/domains/reports/test_service.py` |
| `tests/test_openai_client.py` | `tests/unit/infrastructure/test_llm_client.py` |
| `tests/test_graph.py` | `tests/unit/orchestration/test_graph.py` |
| `tests/test_phased_analysis.py` | `tests/unit/orchestration/test_phased.py` |
| `tests/test_run_snapshot.py` | `tests/unit/orchestration/test_snapshot.py` |
| `tests/test_analyze_routes.py` | `tests/unit/api/test_analyze_routes.py` |
| `tests/test_runs_routes.py` | `tests/unit/api/test_runs_routes.py` |
| `tests/test_health.py` | `tests/unit/api/test_health.py` |
| `tests/test_main.py` | `tests/unit/api/test_main.py` |
| `tests/test_db_utils.py` | `tests/unit/infrastructure/test_db_utils.py` |

**Step 1: Move each test file and update imports**

**Step 2: Run tests to verify**

```bash
pytest tests/ -v
```

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor(tests): reorganize tests to match new structure"
```

---

## Summary

**Total Tasks:** ~60 tasks across 12 phases
**Estimated Commits:** ~50 commits

**Key Checkpoints:**
1. After Phase 4 (Infrastructure): Run tests
2. After Phase 8 (Reports Domain): Run tests
3. After Phase 10 (API Layer): Run tests + verify server starts
4. After Phase 11 (Cleanup): Full verification
5. After Phase 12 (Tests): Final verification
