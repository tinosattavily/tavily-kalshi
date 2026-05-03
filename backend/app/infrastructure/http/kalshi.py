"""Kalshi API HTTP client."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from app.config import get_logger, settings
from app.infrastructure.http.kalshi_auth import get_auth_headers, is_kalshi_auth_available
from app.infrastructure.http.cache import kalshi_cache
from app.infrastructure.http.resilience import kalshi_circuit
from app.shared.exceptions import (
    KalshiAPIError,
    KalshiAuthenticationError,
    KalshiMarketNotFoundError,
)

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 10.0


async def fetch_kalshi(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,
    cache_ttl: int = 60,
    require_auth: bool = False,
) -> Dict[str, Any]:
    """Make request to Kalshi API, authenticating only when required.

    Args:
        method: HTTP method
        path: API path (e.g., "/markets/TICKER")
        params: Query parameters
        use_cache: Whether to use response cache (GET only)
        cache_ttl: Cache TTL in seconds
        require_auth: Whether to sign the request with Kalshi credentials

    Returns:
        Parsed JSON response

    Raises:
        KalshiAuthenticationError: If auth not configured or fails
        KalshiAPIError: For other API errors
    """
    full_path = f"/trade-api/v2{path}"
    base_url = (
        settings.kalshi_authenticated_base_url
        if require_auth
        else settings.kalshi_public_base_url
    )
    url = f"{base_url}{path}"

    # Check cache for GET requests
    cache_key = f"kalshi:{method}:{path}:{params}:auth={require_auth}"
    if method == "GET" and use_cache:
        cached = kalshi_cache.get(cache_key)
        if cached is not None:
            logger.debug("Kalshi cache hit", path=path)
            return cached

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if require_auth:
        if not is_kalshi_auth_available():
            raise KalshiAuthenticationError("Kalshi API credentials not configured")
        # Sign with full path, no query params.
        headers.update(get_auth_headers(method, full_path))

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
            )
    except httpx.TimeoutException as e:
        logger.error("Kalshi request timeout", path=path, error=str(e))
        kalshi_circuit.record_failure()
        raise KalshiAPIError(f"Request timeout: {e}") from e
    except httpx.RequestError as e:
        logger.error("Kalshi request failed", path=path, error=str(e))
        kalshi_circuit.record_failure()
        raise KalshiAPIError(f"Request failed: {e}") from e

    if response.status_code == 401:
        raise KalshiAuthenticationError("Invalid Kalshi credentials")

    if response.status_code == 404:
        raise KalshiMarketNotFoundError(f"Not found: {path}")

    if response.status_code >= 400:
        raise KalshiAPIError(f"API error {response.status_code}: {response.text}")

    kalshi_circuit.record_success()
    data = response.json()

    # Cache successful GET responses
    if method == "GET" and use_cache:
        kalshi_cache.set(cache_key, data)

    return data


async def get_market(ticker: str) -> Dict[str, Any]:
    """Fetch a single market by ticker."""
    response = await fetch_kalshi("GET", f"/markets/{ticker}")
    return response.get("market", response)


async def get_markets(
    event_ticker: Optional[str] = None,
    status: str = "open",
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Fetch markets, optionally filtered by event."""
    params: Dict[str, Any] = {"status": status, "limit": limit}
    if event_ticker:
        params["event_ticker"] = event_ticker

    response = await fetch_kalshi("GET", "/markets", params=params)
    return response.get("markets", [])


async def get_event(event_ticker: str) -> Dict[str, Any]:
    """Fetch event details by event ticker."""
    response = await fetch_kalshi("GET", f"/events/{event_ticker}")
    return response.get("event", response)


async def get_orderbook(ticker: str, depth: int = 10) -> Dict[str, Any]:
    """Fetch orderbook for a market."""
    response = await fetch_kalshi(
        "GET",
        f"/markets/{ticker}/orderbook",
        params={"depth": depth},
    )
    return response
