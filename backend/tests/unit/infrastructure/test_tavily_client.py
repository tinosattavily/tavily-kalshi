"""Tests for Tavily Client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.http.tavily import _search_news_impl_async, search_news


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_impl_async_success():
    """Test _search_news_impl_async successful search."""
    mock_response = {
        "answer": "Test answer",
        "results": [
            {
                "title": "Article 1",
                "url": "https://example.com/1",
                "content": "Content 1",
            }
        ],
    }

    with (
        patch("app.infrastructure.http.tavily.TAVILY_API_KEY", "test-key"),
        patch("aiohttp.ClientSession.post") as mock_post,
    ):
        mock_resp = AsyncMock()
        mock_resp.ok = True
        mock_resp.status = 200
        mock_resp.text = AsyncMock(return_value=json.dumps(mock_response))
        mock_post.return_value.__aenter__.return_value = mock_resp

        result = await _search_news_impl_async("test query", max_results=5)

        assert result == mock_response


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_impl_async_api_error():
    """Test _search_news_impl_async with API errors."""
    with (
        patch("app.infrastructure.http.tavily.TAVILY_API_KEY", "test-key"),
        patch("aiohttp.ClientSession.post") as mock_post,
    ):
        mock_resp = AsyncMock()
        mock_resp.ok = False
        mock_resp.status = 500
        mock_resp.text = AsyncMock(return_value="{}")
        mock_resp.raise_for_status = MagicMock(side_effect=RuntimeError("API Error"))
        mock_post.return_value.__aenter__.return_value = mock_resp

        with pytest.raises(RuntimeError):
            await _search_news_impl_async("test query")


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_impl_async_missing_key():
    """Test _search_news_impl_async with missing API key."""
    with patch("app.infrastructure.http.tavily.TAVILY_API_KEY", None):
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            await _search_news_impl_async("test query")


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_caching():
    """Test search_news caching behavior."""
    mock_result = {
        "answer": "Cached answer",
        "articles": [{"title": "Cached article"}],
    }

    with patch("app.infrastructure.http.tavily.tavily_cache") as mock_cache:
        mock_cache.get.return_value = mock_result

        result = await search_news("test query")

        assert mock_cache.get.called
        assert result["answer"] == "Cached answer"


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_circuit_breaker():
    """Test search_news with circuit breaker integration."""
    with patch("app.infrastructure.http.tavily.tavily_circuit") as mock_circuit:
        mock_circuit.can_attempt.return_value = False

        result = await search_news("test query")

        assert result == {"answer": "", "articles": []}


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_error_handling():
    """Test search_news error handling."""
    with patch("app.infrastructure.http.tavily._search_news_impl_async") as mock_search:
        mock_search.side_effect = Exception("API Error")

        with patch("app.infrastructure.http.tavily.tavily_circuit") as mock_circuit:
            mock_circuit.can_attempt.return_value = True
            mock_circuit.record_failure = MagicMock()

            result = await search_news("test query")

            assert result == {"answer": "", "articles": []}
            assert mock_circuit.record_failure.called


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_missing_key():
    """Test search_news with missing API key."""
    with patch("app.infrastructure.http.tavily.TAVILY_API_KEY", None):
        result = await search_news("test query")

        assert result == {"answer": "", "articles": []}


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_retry_logic():
    """Test search_news retry logic."""
    call_count = 0

    async def flaky_search(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Temporary error")
        return {
            "answer": "Success",
            "results": [],
        }

    with patch("app.infrastructure.http.tavily._search_news_impl_async", side_effect=flaky_search):
        with patch("app.infrastructure.http.tavily.tavily_circuit") as mock_circuit:
            mock_circuit.can_attempt.return_value = True
            mock_circuit.record_success = MagicMock()

            with patch("app.infrastructure.http.tavily.tavily_cache") as mock_cache:
                mock_cache.get.return_value = None
                mock_cache.set = MagicMock()

                await search_news("test query")

                # Should retry and succeed
                assert call_count == 2
