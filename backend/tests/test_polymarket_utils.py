"""Tests for Polymarket Utilities."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from app.core.polymarket_utils import (
    _get_series_comment_count,
    extract_slug_from_url,
    fetch_json_async,
    fetch_order_book_async,
    get_event_and_markets_by_slug,
    normalize_number,
    parse_end_date,
    parse_prices_from_market,
)


def test_get_series_comment_count_valid():
    """Test _get_series_comment_count with valid series data."""
    event_data = {
        "series": [
            {
                "commentCount": 10,
            }
        ]
    }

    result = _get_series_comment_count(event_data)
    assert result == 10


def test_get_series_comment_count_missing():
    """Test _get_series_comment_count with missing/invalid series."""
    event_data = {}
    result = _get_series_comment_count(event_data)
    assert result is None

    event_data2 = {"series": []}
    result2 = _get_series_comment_count(event_data2)
    assert result2 is None


def test_extract_slug_from_url():
    """Test extract_slug_from_url with various URL formats."""
    # Standard URL
    assert extract_slug_from_url("https://polymarket.com/event/fed-decision") == "fed-decision"

    # URL with query params
    assert (
        extract_slug_from_url("https://polymarket.com/event/fed-decision?tid=abc") == "fed-decision"
    )

    # URL with fragment
    assert (
        extract_slug_from_url("https://polymarket.com/event/fed-decision#section") == "fed-decision"
    )

    # Market URL
    assert extract_slug_from_url("https://polymarket.com/market/test-market") == "test-market"


def test_extract_slug_from_url_missing_invalid():
    """Test extract_slug_from_url with missing/invalid URLs."""
    assert extract_slug_from_url(None) is None
    assert extract_slug_from_url("") is None
    assert extract_slug_from_url("invalid") is None


@pytest.mark.anyio(backend="asyncio")
async def test_get_event_and_markets_by_slug_events_endpoint():
    """Test get_event_and_markets_by_slug with events endpoint success."""
    mock_event = {
        "slug": "test-event",
        "title": "Test Event",
        "commentCount": 10,
    }

    with patch("app.core.polymarket_utils.fetch_json_async") as mock_fetch:
        mock_fetch.return_value = [mock_event]

        with patch("app.core.polymarket_utils.polymarket_cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set = MagicMock()

            event, markets = await get_event_and_markets_by_slug("test-event")

            # Should return event and markets
            assert event is not None or markets is not None


@pytest.mark.anyio(backend="asyncio")
async def test_get_event_and_markets_by_slug_caching():
    """Test get_event_and_markets_by_slug caching behavior."""
    with patch("app.core.polymarket_utils.polymarket_cache") as mock_cache:
        cached_data = ({"slug": "test"}, [{"slug": "market-1"}])
        mock_cache.get.return_value = cached_data

        event, markets = await get_event_and_markets_by_slug("test-event")

        # Should use cache
        assert mock_cache.get.called


def test_parse_prices_from_market():
    """Test parse_prices_from_market with valid price data."""
    market = {
        "outcomePrices": [0.6, 0.4],
    }

    yes_price, no_price = parse_prices_from_market(market)
    assert yes_price == 0.6
    assert no_price == 0.4


def test_parse_prices_from_market_missing():
    """Test parse_prices_from_market with missing prices."""
    market = {}
    yes_price, no_price = parse_prices_from_market(market)
    assert yes_price is None
    assert no_price is None


def test_normalize_number():
    """Test normalize_number with various number types."""
    assert normalize_number(10) == 10.0
    assert normalize_number(10.5) == 10.5
    assert normalize_number("10") == 10.0
    assert normalize_number("10.5") == 10.5
    assert normalize_number(None) is None
    assert normalize_number("invalid") is None


def test_parse_end_date():
    """Test parse_end_date with valid date strings."""
    date_str = "2025-12-31T00:00:00Z"
    result = parse_end_date(date_str)
    assert isinstance(result, datetime)


def test_parse_end_date_invalid():
    """Test parse_end_date with invalid formats."""
    assert parse_end_date("invalid") is None
    assert parse_end_date(None) is None


@pytest.mark.anyio(backend="asyncio")
async def test_fetch_json_async_success():
    """Test fetch_json_async with successful request."""
    mock_response = {"data": "test"}

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_get.return_value.__aenter__.return_value = mock_resp

        result = await fetch_json_async("https://example.com/api")

        assert result == mock_response


@pytest.mark.anyio(backend="asyncio")
async def test_fetch_json_async_error():
    """Test fetch_json_async with HTTP error."""

    # Patch the _fetch_json_impl to raise an exception
    async def mock_fetch_impl(url, params=None, timeout=10):
        # Simulate aiohttp raising a generic exception (ClientResponseError needs request_info)
        raise RuntimeError("Server Error (500)")

    # Ensure cache is empty and circuit breaker allows attempts
    with (
        patch("app.core.polymarket_utils.polymarket_cache.get", return_value=None),
        patch("app.core.polymarket_utils.polymarket_circuit.can_attempt", return_value=True),
        patch("app.core.polymarket_utils._fetch_json_impl", side_effect=mock_fetch_impl),
    ):
        with pytest.raises(RuntimeError, match="Server Error"):
            await fetch_json_async("https://example.com/api")


@pytest.mark.anyio(backend="asyncio")
async def test_fetch_order_book_async():
    """Test fetch_order_book_async."""
    mock_order_book = {
        "bids": [[0.48, 100]],
        "asks": [[0.52, 150]],
    }

    with patch("app.core.polymarket_utils.fetch_json_async") as mock_fetch:
        mock_fetch.return_value = mock_order_book

        with patch("app.core.polymarket_utils.polymarket_cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set = MagicMock()

            result = await fetch_order_book_async("token-123")

            assert "bids" in result or result == mock_order_book
