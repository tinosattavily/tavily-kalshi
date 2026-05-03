"""Tests for Kalshi API schemas."""

import pytest
from pydantic import ValidationError


class TestKalshiMarket:
    """Tests for KalshiMarket schema."""

    def test_parses_valid_market_response(self):
        """Should parse a valid market response."""
        from app.domains.markets.kalshi_schemas import KalshiMarket

        data = {
            "ticker": "INXD-25JAN17-B24999",
            "event_ticker": "INXD-25JAN17",
            "title": "S&P 500 above 24999?",
            "status": "open",
            "yes_bid": 45,
            "yes_ask": 47,
        }

        market = KalshiMarket.model_validate(data)

        assert market.ticker == "INXD-25JAN17-B24999"
        assert market.event_ticker == "INXD-25JAN17"
        assert market.yes_bid == 45

    def test_ignores_unknown_fields(self):
        """Should ignore unknown fields from API."""
        from app.domains.markets.kalshi_schemas import KalshiMarket

        data = {
            "ticker": "TEST",
            "event_ticker": "TEST-EVENT",
            "title": "Test",
            "status": "open",
            "unknown_field": "should be ignored",
            "another_unknown": 123,
        }

        market = KalshiMarket.model_validate(data)
        assert market.ticker == "TEST"

    def test_optional_fields_default_to_none(self):
        """Optional fields should default to None."""
        from app.domains.markets.kalshi_schemas import KalshiMarket

        data = {
            "ticker": "TEST",
            "event_ticker": "TEST-EVENT",
            "title": "Test",
            "status": "open",
        }

        market = KalshiMarket.model_validate(data)
        assert market.yes_bid is None
        assert market.volume is None


class TestKalshiEvent:
    """Tests for KalshiEvent schema."""

    def test_parses_valid_event_response(self):
        """Should parse a valid event response."""
        from app.domains.markets.kalshi_schemas import KalshiEvent

        data = {
            "event_ticker": "INXD-25JAN17",
            "title": "S&P 500 Index",
            "category": "Economics",
        }

        event = KalshiEvent.model_validate(data)

        assert event.event_ticker == "INXD-25JAN17"
        assert event.category == "Economics"

    def test_markets_default_to_empty_list(self):
        """Markets list should default to empty."""
        from app.domains.markets.kalshi_schemas import KalshiEvent

        data = {
            "event_ticker": "TEST",
            "title": "Test Event",
        }

        event = KalshiEvent.model_validate(data)
        assert event.markets == []


class TestKalshiOrderbook:
    """Tests for KalshiOrderbook schema."""

    def test_parses_orderbook_with_levels(self):
        """Should parse orderbook with bid/ask levels."""
        from app.domains.markets.kalshi_schemas import KalshiOrderbook

        data = {
            "ticker": "TEST",
            "yes_bids": [{"price": 45, "quantity": 100}],
            "yes_asks": [{"price": 47, "quantity": 50}],
        }

        orderbook = KalshiOrderbook.model_validate(data)

        assert orderbook.ticker == "TEST"
        assert len(orderbook.yes_bids) == 1
        assert orderbook.yes_bids[0].price == 45
