"""Tests for MarketService Kalshi methods."""

from unittest.mock import AsyncMock, patch

import pytest


class TestGetKalshiMarketFromUrl:
    """Tests for get_kalshi_market_from_url method."""

    @pytest.mark.asyncio
    async def test_returns_snapshot_for_market_url(self):
        """Should return market snapshot for valid market URL."""
        mock_market = {
            "ticker": "TEST-123",
            "event_ticker": "TEST",
            "title": "Test Market",
            "status": "open",
            "yes_bid": 45,
            "yes_ask": 47,
        }

        with patch("app.domains.markets.service.get_kalshi_market_by_ticker") as mock_fetch:
            mock_fetch.return_value = AsyncMock()
            mock_fetch.return_value.ticker = "TEST-123"
            mock_fetch.return_value.event_ticker = "TEST"
            mock_fetch.return_value.title = "Test Market"
            mock_fetch.return_value.status = "open"
            mock_fetch.return_value.yes_bid = 45
            mock_fetch.return_value.yes_ask = 47
            mock_fetch.return_value.subtitle = None
            mock_fetch.return_value.no_bid = None
            mock_fetch.return_value.no_ask = None
            mock_fetch.return_value.last_price = None
            mock_fetch.return_value.volume = None
            mock_fetch.return_value.volume_24h = None
            mock_fetch.return_value.open_interest = None
            mock_fetch.return_value.close_time = None

            from app.domains.markets.service import get_market_service

            service = get_market_service()
            result = await service.get_kalshi_market_from_url(
                "https://kalshi.com/markets/TEST-123"
            )

            assert result["ticker"] == "TEST-123"
            assert result["yes_price"] == 46  # mid of 45 and 47

    @pytest.mark.asyncio
    async def test_raises_for_event_url(self):
        """Should raise ValueError for event URLs requiring selection."""
        from app.domains.markets.service import get_market_service

        service = get_market_service()

        with pytest.raises(ValueError, match="Event URL requires market selection"):
            await service.get_kalshi_market_from_url(
                "https://kalshi.com/events/TEST-EVENT"
            )


class TestGetKalshiMarketByTicker:
    """Tests for get_kalshi_market_by_ticker method."""

    @pytest.mark.asyncio
    async def test_returns_snapshot_for_ticker(self):
        """Should return market snapshot for valid ticker."""
        from unittest.mock import MagicMock

        mock_market = MagicMock()
        mock_market.ticker = "TEST-123"
        mock_market.event_ticker = "TEST"
        mock_market.title = "Test Market"
        mock_market.status = "open"
        mock_market.yes_bid = 50
        mock_market.yes_ask = None
        mock_market.subtitle = None
        mock_market.no_bid = None
        mock_market.no_ask = None
        mock_market.last_price = None
        mock_market.volume = 1000
        mock_market.volume_24h = None
        mock_market.open_interest = None
        mock_market.close_time = None

        with patch("app.domains.markets.service.get_kalshi_market_by_ticker") as mock_fetch:
            mock_fetch.return_value = mock_market

            from app.domains.markets.service import get_market_service

            service = get_market_service()
            result = await service.get_kalshi_market_by_ticker_snapshot("TEST-123")

            assert result["ticker"] == "TEST-123"
            assert result["yes_price"] == 50
            assert result["volume"] == 1000
