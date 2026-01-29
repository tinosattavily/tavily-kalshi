"""Tests for Tavily Client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.tavily_client import _search_news_impl, search_news


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_impl_success():
    """Test _search_news_impl successful search via search_news public API."""
    mock_search_result = {
        "answer": "Test answer",
        "results": [
            {
                "title": "Article 1",
                "url": "https://example.com/1",
                "content": "Content 1",
            }
        ],
    }

    async def mock_impl(*args, **kwargs):
        return mock_search_result

    with patch("app.services.tavily_client.TAVILY_API_KEY", "test-key"):
        with patch("app.services.tavily_client._search_news_impl", side_effect=mock_impl):
            with patch("app.services.tavily_client.tavily_cache") as mock_cache:
                mock_cache.get.return_value = None
                with patch("app.services.tavily_client.tavily_circuit") as mock_circuit:
                    mock_circuit.can_attempt.return_value = True

                    result = await search_news("test query", max_results=5)

                    assert "answer" in result


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_impl_api_error():
    """Test _search_news_impl with API errors via search_news public API."""
    with patch("app.services.tavily_client.TAVILY_API_KEY", "test-key"):
        with patch("app.services.tavily_client._search_news_impl") as mock_impl:
            mock_impl.side_effect = Exception("API Error")

            with patch("app.services.tavily_client.tavily_cache") as mock_cache:
                mock_cache.get.return_value = None
                with patch("app.services.tavily_client.tavily_circuit") as mock_circuit:
                    mock_circuit.can_attempt.return_value = True
                    mock_circuit.record_failure = MagicMock()

                    # Should return empty result (graceful degradation)
                    result = await search_news("test query")
                    assert result == {"answer": "", "articles": []}


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_impl_missing_key():
    """Test _search_news_impl with missing API key."""
    with patch("app.services.tavily_client.TAVILY_API_KEY", None):
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            await _search_news_impl("test query")


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_caching():
    """Test search_news caching behavior."""
    mock_result = {
        "answer": "Cached answer",
        "articles": [{"title": "Cached article"}],
    }

    with patch("app.services.tavily_client.TAVILY_API_KEY", "test-key"):
        with patch("app.services.tavily_client.tavily_cache") as mock_cache:
            mock_cache.get.return_value = mock_result

            result = await search_news("test query")

            assert mock_cache.get.called
            assert result["answer"] == "Cached answer"


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_circuit_breaker():
    """Test search_news with circuit breaker integration."""
    with patch("app.services.tavily_client.TAVILY_API_KEY", "test-key"):
        with patch("app.services.tavily_client.tavily_cache") as mock_cache:
            mock_cache.get.return_value = None
            with patch("app.services.tavily_client.tavily_circuit") as mock_circuit:
                mock_circuit.can_attempt.return_value = False

                result = await search_news("test query")

                assert result == {"answer": "", "articles": []}


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_error_handling():
    """Test search_news error handling."""
    with patch("app.services.tavily_client.TAVILY_API_KEY", "test-key"):
        with patch("app.services.tavily_client.tavily_cache") as mock_cache:
            mock_cache.get.return_value = None
            with patch("app.services.tavily_client._search_news_impl") as mock_search:
                mock_search.side_effect = Exception("API Error")

                with patch("app.services.tavily_client.tavily_circuit") as mock_circuit:
                    mock_circuit.can_attempt.return_value = True
                    mock_circuit.record_failure = MagicMock()

                    result = await search_news("test query")

                    assert result == {"answer": "", "articles": []}
                    assert mock_circuit.record_failure.called


@pytest.mark.anyio(backend="asyncio")
async def test_search_news_missing_key():
    """Test search_news with missing API key."""
    with patch("app.services.tavily_client.TAVILY_API_KEY", None):
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

    with patch("app.services.tavily_client.TAVILY_API_KEY", "test-key"):
        with patch("app.services.tavily_client._search_news_impl", side_effect=flaky_search):
            with patch("app.services.tavily_client.tavily_circuit") as mock_circuit:
                mock_circuit.can_attempt.return_value = True
                mock_circuit.record_success = MagicMock()

                with patch("app.services.tavily_client.tavily_cache") as mock_cache:
                    mock_cache.get.return_value = None
                    mock_cache.set = MagicMock()

                    await search_news("test query")

                    # Should retry and succeed
                    assert call_count == 2
