"""Tests for EventService Kalshi methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGetKalshiEventContext:
    """Tests for get_kalshi_event_context method."""

    @pytest.mark.asyncio
    async def test_returns_event_context_with_markets(self):
        """Should return event context with market list."""
        mock_event = MagicMock()
        mock_event.event_ticker = "TEST-EVENT"
        mock_event.title = "Test Event"
        mock_event.category = "Economics"

        mock_market1 = MagicMock()
        mock_market1.ticker = "TEST-EVENT-A"
        mock_market1.title = "Option A"
        mock_market1.subtitle = None
        mock_market1.yes_bid = 45
        mock_market1.yes_ask = 47
        mock_market1.last_price = None
        mock_market1.status = "open"

        mock_market2 = MagicMock()
        mock_market2.ticker = "TEST-EVENT-B"
        mock_market2.title = "Option B"
        mock_market2.subtitle = None
        mock_market2.yes_bid = 30
        mock_market2.yes_ask = 32
        mock_market2.last_price = None
        mock_market2.status = "open"

        mock_event.markets = [mock_market1, mock_market2]

        with patch("app.domains.markets.event_service.get_kalshi_event_by_ticker") as mock_fetch:
            mock_fetch.return_value = mock_event

            from app.domains.markets.event_service import get_event_service

            service = get_event_service()
            result = await service.get_kalshi_event_context("TEST-EVENT")

            assert result["event_ticker"] == "TEST-EVENT"
            assert result["market_count"] == 2
            assert result["requires_selection"] is True
            assert len(result["markets"]) == 2


class TestGetKalshiEventContextFromUrl:
    """Tests for get_kalshi_event_context_from_url method."""

    @pytest.mark.asyncio
    async def test_extracts_event_from_market_url(self):
        """Should extract event ticker from market URL."""
        mock_event = MagicMock()
        mock_event.event_ticker = "INXD-25JAN17"
        mock_event.title = "S&P 500"
        mock_event.category = "Economics"
        mock_event.markets = []

        with patch("app.domains.markets.event_service.get_kalshi_event_by_ticker") as mock_fetch:
            mock_fetch.return_value = mock_event

            from app.domains.markets.event_service import get_event_service

            service = get_event_service()
            result = await service.get_kalshi_event_context_from_url(
                "https://kalshi.com/markets/INXD-25JAN17-B24999"
            )

            assert result["event_ticker"] == "INXD-25JAN17"
            mock_fetch.assert_called_once_with("INXD-25JAN17")


class TestRequiresKalshiMarketSelection:
    """Tests for requires_kalshi_market_selection method."""

    def test_returns_true_for_multiple_markets(self):
        """Should return True when event has multiple markets."""
        from app.domains.markets.event_service import get_event_service

        service = get_event_service()
        context = {"market_count": 5, "requires_selection": True}

        assert service.requires_kalshi_market_selection(context) is True

    def test_returns_false_for_single_market(self):
        """Should return False when event has single market."""
        from app.domains.markets.event_service import get_event_service

        service = get_event_service()
        context = {"market_count": 1, "requires_selection": False}

        assert service.requires_kalshi_market_selection(context) is False


class TestGetKalshiMarketOptions:
    """Tests for get_kalshi_market_options method."""

    def test_returns_markets_list(self):
        """Should return list of market options."""
        from app.domains.markets.event_service import get_event_service

        service = get_event_service()
        context = {
            "markets": [
                {"ticker": "A", "title": "Option A", "yes_price": 45},
                {"ticker": "B", "title": "Option B", "yes_price": 55},
            ]
        }

        options = service.get_kalshi_market_options(context)

        assert len(options) == 2
        assert options[0]["ticker"] == "A"
