"""Tests for URL parsing utilities."""

import pytest


class TestIsKalshiUrl:
    """Tests for is_kalshi_url function."""

    def test_returns_true_for_kalshi_com(self):
        """Should return True for kalshi.com URLs."""
        from app.domains.markets.parsing import is_kalshi_url

        assert is_kalshi_url("https://kalshi.com/markets/INXD-25JAN17-B24999") is True
        assert is_kalshi_url("https://www.kalshi.com/events/INXD-25JAN17") is True

    def test_returns_true_for_kalshi_co(self):
        """Should return True for kalshi.co URLs (demo)."""
        from app.domains.markets.parsing import is_kalshi_url

        assert is_kalshi_url("https://demo.kalshi.co/markets/TEST") is True

    def test_returns_false_for_other_urls(self):
        """Should return False for non-Kalshi URLs."""
        from app.domains.markets.parsing import is_kalshi_url

        assert is_kalshi_url("https://polymarket.com/event/test") is False
        assert is_kalshi_url("https://google.com") is False


class TestExtractKalshiTicker:
    """Tests for extract_kalshi_ticker_from_url function."""

    def test_extracts_ticker_from_market_url(self):
        """Should extract ticker from market URL."""
        from app.domains.markets.parsing import extract_kalshi_ticker_from_url

        url = "https://kalshi.com/markets/INXD-25JAN17-B24999"
        assert extract_kalshi_ticker_from_url(url) == "INXD-25JAN17-B24999"

    def test_returns_none_for_non_market_url(self):
        """Should return None if no market pattern found."""
        from app.domains.markets.parsing import extract_kalshi_ticker_from_url

        assert extract_kalshi_ticker_from_url("https://kalshi.com/events/TEST") is None


class TestExtractKalshiEventTicker:
    """Tests for extract_kalshi_event_ticker_from_url function."""

    def test_extracts_event_ticker(self):
        """Should extract event ticker from event URL."""
        from app.domains.markets.parsing import extract_kalshi_event_ticker_from_url

        url = "https://kalshi.com/events/INXD-25JAN17"
        assert extract_kalshi_event_ticker_from_url(url) == "INXD-25JAN17"


class TestParseKalshiUrl:
    """Tests for parse_kalshi_url function."""

    def test_parses_market_url(self):
        """Should parse market URL and return ticker and type."""
        from app.domains.markets.parsing import parse_kalshi_url

        ticker, event_ticker, url_type = parse_kalshi_url(
            "https://kalshi.com/markets/INXD-25JAN17-B24999"
        )

        assert ticker == "INXD-25JAN17-B24999"
        assert event_ticker == "INXD-25JAN17"
        assert url_type == "market"

    def test_parses_event_url(self):
        """Should parse event URL and return event ticker."""
        from app.domains.markets.parsing import parse_kalshi_url

        ticker, event_ticker, url_type = parse_kalshi_url(
            "https://kalshi.com/events/INXD-25JAN17"
        )

        assert ticker is None
        assert event_ticker == "INXD-25JAN17"
        assert url_type == "event"

    def test_returns_unknown_for_invalid_url(self):
        """Should return unknown type for invalid URLs."""
        from app.domains.markets.parsing import parse_kalshi_url

        ticker, event_ticker, url_type = parse_kalshi_url("https://kalshi.com/about")

        assert ticker is None
        assert event_ticker is None
        assert url_type == "unknown"
