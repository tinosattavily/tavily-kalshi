"""Tests for Kalshi market fetcher."""

from unittest.mock import AsyncMock, patch

import pytest


class TestGetKalshiMarketByTicker:
    """Tests for get_kalshi_market_by_ticker function."""

    @pytest.mark.asyncio
    async def test_returns_kalshi_market_model(self):
        """Should return a KalshiMarket instance."""
        mock_response = {
            "ticker": "TEST-123",
            "event_ticker": "TEST",
            "title": "Test Market",
            "status": "open",
            "yes_bid": 45,
        }

        with patch("app.domains.markets.kalshi_fetcher.get_market") as mock_get:
            mock_get.return_value = mock_response

            from app.domains.markets.kalshi_fetcher import get_kalshi_market_by_ticker
            from app.domains.markets.kalshi_schemas import KalshiMarket

            result = await get_kalshi_market_by_ticker("TEST-123")

            assert isinstance(result, KalshiMarket)
            assert result.ticker == "TEST-123"
            assert result.yes_bid == 45


class TestGetKalshiEventByTicker:
    """Tests for get_kalshi_event_by_ticker function."""

    @pytest.mark.asyncio
    async def test_returns_event_with_markets(self):
        """Should return event with populated markets list."""
        mock_event = {
            "event_ticker": "TEST",
            "title": "Test Event",
            "category": "Test",
        }
        mock_markets = [
            {"ticker": "TEST-A", "event_ticker": "TEST", "title": "A", "status": "open"},
            {"ticker": "TEST-B", "event_ticker": "TEST", "title": "B", "status": "open"},
        ]

        with patch("app.domains.markets.kalshi_fetcher.get_event") as mock_get_event:
            mock_get_event.return_value = mock_event
            with patch("app.domains.markets.kalshi_fetcher.get_markets") as mock_get_markets:
                mock_get_markets.return_value = mock_markets

                from app.domains.markets.kalshi_fetcher import get_kalshi_event_by_ticker

                result = await get_kalshi_event_by_ticker("TEST")

                assert result.event_ticker == "TEST"
                assert len(result.markets) == 2
