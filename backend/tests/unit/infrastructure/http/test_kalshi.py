"""Tests for Kalshi HTTP client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestFetchKalshi:
    """Tests for fetch_kalshi function."""

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_not_configured(self):
        """Should raise KalshiAuthenticationError when auth not available."""
        with patch("app.infrastructure.http.kalshi.is_kalshi_auth_available") as mock_auth:
            mock_auth.return_value = False

            from app.infrastructure.http.kalshi import fetch_kalshi
            from app.shared.exceptions import KalshiAuthenticationError

            with pytest.raises(KalshiAuthenticationError):
                await fetch_kalshi("GET", "/markets/TEST", require_auth=True)

    @pytest.mark.asyncio
    async def test_fetch_kalshi_public_get_does_not_require_auth(self, monkeypatch):
        monkeypatch.setattr(
            "app.infrastructure.http.kalshi.is_kalshi_auth_available",
            lambda: False,
        )

        class Response:
            status_code = 200
            text = "{}"

            def json(self):
                return {"market": {"ticker": "TEST"}}

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def request(self, **kwargs):
                assert "KALSHI-ACCESS-KEY" not in kwargs["headers"]
                return Response()

        from app.infrastructure.http.kalshi import fetch_kalshi

        monkeypatch.setattr("httpx.AsyncClient", lambda timeout: Client())
        result = await fetch_kalshi("GET", "/markets/TEST", use_cache=False)
        assert result["market"]["ticker"] == "TEST"

    @pytest.mark.asyncio
    async def test_returns_cached_response_on_cache_hit(self):
        """Should return cached response for GET requests."""
        cached_data = {"market": {"ticker": "TEST"}}

        with patch("app.infrastructure.http.kalshi.is_kalshi_auth_available") as mock_auth:
            mock_auth.return_value = True
            with patch("app.infrastructure.http.kalshi.kalshi_cache") as mock_cache:
                mock_cache.get.return_value = cached_data

                from app.infrastructure.http.kalshi import fetch_kalshi

                result = await fetch_kalshi("GET", "/markets/TEST")

                assert result == cached_data
                mock_cache.get.assert_called_once()


class TestGetMarket:
    """Tests for get_market function."""

    @pytest.mark.asyncio
    async def test_extracts_market_from_response(self):
        """Should extract market object from response."""
        response_data = {"market": {"ticker": "TEST-123", "title": "Test Market"}}

        with patch("app.infrastructure.http.kalshi.fetch_kalshi") as mock_fetch:
            mock_fetch.return_value = response_data

            from app.infrastructure.http.kalshi import get_market

            result = await get_market("TEST-123")

            assert result["ticker"] == "TEST-123"
            mock_fetch.assert_called_once_with("GET", "/markets/TEST-123")


class TestGetMarkets:
    """Tests for get_markets function."""

    @pytest.mark.asyncio
    async def test_returns_markets_list(self):
        """Should return list of markets."""
        response_data = {"markets": [{"ticker": "A"}, {"ticker": "B"}]}

        with patch("app.infrastructure.http.kalshi.fetch_kalshi") as mock_fetch:
            mock_fetch.return_value = response_data

            from app.infrastructure.http.kalshi import get_markets

            result = await get_markets(event_ticker="EVENT-1")

            assert len(result) == 2
            assert result[0]["ticker"] == "A"


class TestGetEvent:
    """Tests for get_event function."""

    @pytest.mark.asyncio
    async def test_extracts_event_from_response(self):
        """Should extract event object from response."""
        response_data = {"event": {"event_ticker": "EVENT-1", "title": "Test Event"}}

        with patch("app.infrastructure.http.kalshi.fetch_kalshi") as mock_fetch:
            mock_fetch.return_value = response_data

            from app.infrastructure.http.kalshi import get_event

            result = await get_event("EVENT-1")

            assert result["event_ticker"] == "EVENT-1"
