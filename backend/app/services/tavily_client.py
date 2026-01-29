"""Tavily API client with caching and retry logic."""

from __future__ import annotations

import json
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

from app.config import settings
from app.core.cache import tavily_cache
from app.core.logging_config import get_logger
from app.core.resilience import tavily_circuit, with_async_retry
from app.schemas.tavily import TavilySearchResult

logger = get_logger(__name__)

TAVILY_API_URL = "https://api.tavily.com/search"
TAVILY_API_KEY = settings.tavily_api_key

EMPTY_RESULT: dict[str, Any] = {"answer": "", "articles": []}


def _extract_error_message(error_details: dict[str, Any]) -> str:
    """Extract error message from API error response."""
    return (
        error_details.get("error")
        or error_details.get("message")
        or error_details.get("detail")
        or "Unknown error"
    )


def _parse_json_safely(text: str) -> dict[str, Any]:
    """Parse JSON text, returning empty dict on failure."""
    if not text:
        return {}
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {"raw_response": text[:500]}


async def _search_news_impl(query: str, max_results: int = 5) -> dict[str, Any]:
    """Internal async implementation of search_news with aiohttp."""
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY is not configured")

    logger.debug("Searching Tavily", query=query, max_results=max_results)

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "include_answer": True,
        "include_raw_content": False,
    }

    timeout = ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            TAVILY_API_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
        ) as response:
            response_text = await response.text()

            if not response.ok:
                error_details = _parse_json_safely(response_text)
                logger.error(
                    "Tavily API error",
                    status=response.status,
                    error_details=error_details,
                    query=query,
                )

                if response.status == 432:
                    error_msg = _extract_error_message(error_details)
                    raise ValueError(
                        f"Tavily API error 432: {error_msg}. "
                        "This usually indicates an invalid API key, expired subscription, "
                        "rate limit exceeded, or account issue."
                    )

                response.raise_for_status()

            return _parse_json_safely(response_text)


def _result_to_dict(result: TavilySearchResult) -> dict[str, Any]:
    """Convert TavilySearchResult to dict format."""
    return {
        "answer": result.answer,
        "articles": [article.model_dump() for article in result.articles],
    }


def _convert_cached_result(cached_result: Any) -> dict[str, Any]:
    """Convert cached result to dict format for backward compatibility."""
    if isinstance(cached_result, dict):
        return cached_result

    if isinstance(cached_result, TavilySearchResult):
        return _result_to_dict(cached_result)

    # Handle legacy cached objects with model_dump
    if hasattr(cached_result, "model_dump") and hasattr(cached_result, "articles"):
        return {
            "answer": getattr(cached_result, "answer", ""),
            "articles": [
                a.model_dump() if hasattr(a, "model_dump") else a
                for a in cached_result.articles
            ],
        }

    return EMPTY_RESULT


async def search_news(query: str, max_results: int = 5) -> dict[str, Any]:
    """Call Tavily's search API with caching, retry, and circuit breaker protection.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)

    Returns:
        Dictionary with answer and articles
    """
    if not TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not configured - returning empty results", query=query)
        return EMPTY_RESULT

    cache_key = f"tavily:{query}:{max_results}"

    cached_result = tavily_cache.get(cache_key)
    if cached_result is not None:
        logger.debug("Cache hit for Tavily", query=query)
        return _convert_cached_result(cached_result)

    if not tavily_circuit.can_attempt():
        logger.warning("Circuit breaker open for Tavily", query=query)
        return EMPTY_RESULT

    try:
        data = await with_async_retry(
            _search_news_impl,
            max_attempts=3,
            base_delay=1.0,
            max_delay=20.0,
            query=query,
            max_results=max_results,
        )

        result = TavilySearchResult.from_api_response(data)
        tavily_cache.set(cache_key, result)
        tavily_circuit.record_success()

        logger.debug(
            "Cache miss - fetched and cached",
            query=query,
            articles_count=len(result.articles),
        )

        return _result_to_dict(result)

    except Exception as e:
        tavily_circuit.record_failure()
        logger.warning("Failed to search Tavily", query=query, error=str(e), exc_info=True)
        return EMPTY_RESULT
