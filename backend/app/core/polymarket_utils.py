"""Polymarket API utilities with caching and retry logic."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

from app.config import PolymarketAPI
from app.core.cache import polymarket_cache
from app.core.logging_config import get_logger
from app.core.resilience import polymarket_circuit, with_async_retry
from app.schemas.polymarket import Event, Market

logger = get_logger(__name__)

GAMMA_API = PolymarketAPI.GAMMA_API
CLOB_API = PolymarketAPI.CLOB_API


def _get_series_comment_count(event_data: dict[str, Any]) -> int | None:
    """Extract comment count from the first series entry if available."""
    series = event_data.get("series")
    if isinstance(series, list) and series and isinstance(series[0], dict):
        return series[0].get("commentCount")
    return None


def _filter_none_values(data: dict[str, Any]) -> dict[str, Any]:
    """Remove keys with None values from a dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def _build_event_dict(
    title: str | None,
    image: str | None,
    icon: str | None,
    volume24hr: float | None,
    comment_count: int | None,
    slug: str,
    series_comment_count: int | None = None,
) -> dict[str, Any]:
    """Build a standardized event dictionary from extracted fields."""
    event_dict = {
        "title": title,
        "image": image or icon,
        "volume24hr": volume24hr,
        "commentCount": comment_count,
        "slug": slug,
        "seriesCommentCount": series_comment_count,
    }
    return _filter_none_values(event_dict)


def extract_slug_from_url(url: str | None) -> str | None:
    """Extract the last path segment (slug) from a URL."""
    if not url:
        return None

    if "://" not in url and "/" not in url and not url.startswith("http"):
        return None

    try:
        url_no_scheme = re.sub(r"^https?://", "", url)
        url_no_query = re.split(r"[?#]", url_no_scheme)[0]
        path = url_no_query.split("/", 1)[-1]
        parts = [p for p in path.split("/") if p]
        return parts[-1] if parts else None
    except Exception:
        return None


async def get_event_and_markets_by_slug(
    slug: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Get event and markets by slug with caching and error handling.

    Tries events endpoint first for accurate event-level data (commentCount),
    then falls back to markets endpoint if needed.
    """
    try:
        event_result = await _fetch_from_events_endpoint(slug)
        if event_result:
            return event_result

        logger.debug("Events endpoint returned nothing, trying markets endpoint", slug=slug)
        return await _fetch_from_markets_endpoint(slug)
    except Exception as e:
        logger.warning("Failed to get event and markets", slug=slug, error=str(e))
        return None, []


async def _fetch_from_events_endpoint(
    slug: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    """Fetch event data from the events endpoint."""
    events_raw = await fetch_json_async(f"{GAMMA_API}/events", params={"slug": slug})
    events_list = _normalize_api_response(events_raw)

    if not events_list:
        return None

    event_raw = events_list[0] if isinstance(events_list[0], dict) else {}
    series_comment_count = _get_series_comment_count(event_raw)

    try:
        event_model = Event.model_validate(events_list[0])
        event_markets = [m.model_dump() for m in event_model.markets] if event_model.markets else []

        logger.info(
            "Fetched event from /events endpoint",
            slug=slug,
            commentCount=event_model.commentCount,
            markets_count=len(event_markets),
        )

        event_dict = _build_event_dict(
            title=event_model.title,
            image=event_model.image,
            icon=event_model.icon,
            volume24hr=event_model.volume24hr,
            comment_count=event_model.commentCount,
            slug=event_model.slug or slug,
            series_comment_count=series_comment_count,
        )
        return event_dict, event_markets
    except Exception as e:
        logger.debug("Pydantic validation failed, using raw data", slug=slug, error=str(e))

    event_markets = event_raw.get("markets", [])
    logger.info(
        "Fetched event from /events endpoint (raw)",
        slug=slug,
        commentCount=event_raw.get("commentCount"),
        markets_count=len(event_markets) if isinstance(event_markets, list) else 0,
    )

    event_dict = _build_event_dict(
        title=event_raw.get("title"),
        image=event_raw.get("image"),
        icon=event_raw.get("icon"),
        volume24hr=event_raw.get("volume24hr"),
        comment_count=event_raw.get("commentCount"),
        slug=event_raw.get("slug") or slug,
        series_comment_count=series_comment_count,
    )
    return event_dict, event_markets


async def _fetch_from_markets_endpoint(
    slug: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Fetch market data from the markets endpoint as fallback."""
    markets_raw = await fetch_json_async(f"{GAMMA_API}/markets", params={"slug": slug})
    markets_list = _normalize_api_response(markets_raw)

    if not markets_list:
        return None, []

    first_market = markets_list[0]

    try:
        market_model = Market.model_validate(first_market)
        markets = []
        for m_raw in markets_list:
            try:
                markets.append(Market.model_validate(m_raw).model_dump())
            except Exception:
                markets.append(m_raw)

        logger.info("Fetched from /markets endpoint", slug=slug, markets_count=len(markets))

        event_dict = _build_event_dict(
            title=market_model.question,
            image=market_model.image,
            icon=market_model.icon,
            volume24hr=market_model.volume24hr,
            comment_count=None,
            slug=slug,
        )
        return event_dict, markets
    except Exception as e:
        logger.debug("Pydantic validation failed, using raw data", slug=slug, error=str(e))

    logger.info("Fetched from /markets endpoint (raw)", slug=slug, markets_count=len(markets_list))

    title = (
        first_market.get("eventTitle")
        or first_market.get("title")
        or first_market.get("question")
    )
    event_dict = _build_event_dict(
        title=title,
        image=first_market.get("image"),
        icon=first_market.get("icon"),
        volume24hr=first_market.get("volume24hr"),
        comment_count=first_market.get("commentCount"),
        slug=slug,
    )
    return event_dict, markets_list


def _normalize_api_response(response: Any) -> list[dict[str, Any]]:
    """Normalize API response to a list of dictionaries."""
    if isinstance(response, dict):
        return response.get("data", [])
    if isinstance(response, list):
        return response
    return []


def parse_prices_from_market(market: dict[str, Any]) -> tuple[float | None, float | None]:
    """Extract yes/no prices from a market dictionary."""
    yes_price = market.get("yes_price")
    no_price = market.get("no_price")
    if isinstance(yes_price, (int, float)) and isinstance(no_price, (int, float)):
        return float(yes_price), float(no_price)

    outcome_prices = market.get("outcomePrices")
    if not outcome_prices:
        return None, None

    if isinstance(outcome_prices, list) and len(outcome_prices) >= 2:
        try:
            return float(outcome_prices[0]), float(outcome_prices[1])
        except (ValueError, TypeError):
            return None, None

    if isinstance(outcome_prices, str) and outcome_prices.startswith("["):
        try:
            arr = json.loads(outcome_prices)
            if isinstance(arr, list) and len(arr) >= 2:
                return float(arr[0]), float(arr[1])
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return None, None


def normalize_number(value: Any) -> float | None:
    """Convert a value to float, returning None if conversion fails."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_end_date(value: str | None) -> datetime | None:
    """Parse an ISO date string to datetime."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


async def _fetch_json_impl(
    url: str, params: dict[str, Any] | None = None, timeout: int = 10
) -> Any:
    """Internal implementation of async JSON fetch."""
    logger.debug("Fetching JSON", url=url, params=params)
    timeout_obj = ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_obj) as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()


async def fetch_json_async(
    url: str, params: dict[str, Any] | None = None, timeout: int = 10
) -> Any:
    """Fetch JSON from URL with caching, retry, and circuit breaker protection."""
    cache_key = f"polymarket:{url}:{hash(str(params))}"

    cached_result = polymarket_cache.get(cache_key)
    if cached_result is not None:
        logger.debug("Cache hit", url=url)
        return cached_result

    if not polymarket_circuit.can_attempt():
        logger.warning("Circuit breaker open", url=url)
        raise RuntimeError("Circuit breaker is OPEN for Polymarket API")

    try:
        result = await with_async_retry(
            _fetch_json_impl,
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            url=url,
            params=params,
            timeout=timeout,
        )
        polymarket_cache.set(cache_key, result)
        polymarket_circuit.record_success()
        logger.debug("Fetched and cached", url=url)
        return result
    except Exception as e:
        polymarket_circuit.record_failure()
        logger.warning("Fetch failed", url=url, error=str(e))
        raise


async def fetch_order_book_async(token_id: str) -> dict[str, Any]:
    """Fetch order book with caching and error handling."""
    try:
        data = await fetch_json_async(f"{CLOB_API}/book", params={"token_id": token_id})

        bids = _parse_order_levels(data.get("bids", []))
        asks = _parse_order_levels(data.get("asks", []))

        return {
            "bids": bids,
            "asks": asks,
            "best_bid": bids[0]["price"] if bids else None,
            "best_ask": asks[0]["price"] if asks else None,
        }
    except Exception as e:
        logger.warning("Failed to fetch order book", token_id=token_id, error=str(e))
        return {"bids": [], "asks": [], "best_bid": None, "best_ask": None}


def _parse_order_levels(levels: list[dict[str, Any]]) -> list[dict[str, float]]:
    """Parse order book levels, filtering out invalid entries."""
    result: list[dict[str, float]] = []
    for level in levels or []:
        price = normalize_number(level.get("price"))
        size = normalize_number(level.get("size"))
        if price is not None and size is not None:
            result.append({"price": price, "size": size})
    return result
