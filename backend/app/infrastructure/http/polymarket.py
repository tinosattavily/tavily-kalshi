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
