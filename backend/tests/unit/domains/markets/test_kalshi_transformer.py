"""Tests for Kalshi market transformer."""

import pytest


class TestValidatePrice:
    """Tests for _validate_price function."""

    def test_returns_valid_price_unchanged(self):
        """Should return valid price as-is."""
        from app.domains.markets.kalshi_transformer import _validate_price

        assert _validate_price(50, "test") == 50
        assert _validate_price(1, "test") == 1
        assert _validate_price(99, "test") == 99

    def test_clamps_out_of_range_prices(self):
        """Should clamp prices outside 1-99 range."""
        from app.domains.markets.kalshi_transformer import _validate_price

        assert _validate_price(0, "test") == 1
        assert _validate_price(100, "test") == 99
        assert _validate_price(-5, "test") == 1

    def test_returns_none_for_none(self):
        """Should return None for None input."""
        from app.domains.markets.kalshi_transformer import _validate_price

        assert _validate_price(None, "test") is None


class TestCalculateYesPrice:
    """Tests for _calculate_yes_price function."""

    def test_uses_mid_when_bid_ask_available(self):
        """Should calculate mid price when bid and ask available."""
        from app.domains.markets.kalshi_schemas import KalshiMarket
        from app.domains.markets.kalshi_transformer import _calculate_yes_price

        market = KalshiMarket(
            ticker="TEST",
            event_ticker="TEST",
            title="Test",
            status="open",
            yes_bid=44,
            yes_ask=48,
        )

        assert _calculate_yes_price(market) == 46  # (44 + 48) // 2

    def test_falls_back_to_bid(self):
        """Should use bid when ask not available."""
        from app.domains.markets.kalshi_schemas import KalshiMarket
        from app.domains.markets.kalshi_transformer import _calculate_yes_price

        market = KalshiMarket(
            ticker="TEST",
            event_ticker="TEST",
            title="Test",
            status="open",
            yes_bid=45,
        )

        assert _calculate_yes_price(market) == 45

    def test_falls_back_to_last_price(self):
        """Should use last_price when bid/ask not available."""
        from app.domains.markets.kalshi_schemas import KalshiMarket
        from app.domains.markets.kalshi_transformer import _calculate_yes_price

        market = KalshiMarket(
            ticker="TEST",
            event_ticker="TEST",
            title="Test",
            status="open",
            last_price=50,
        )

        assert _calculate_yes_price(market) == 50


class TestBuildKalshiMarketSnapshot:
    """Tests for build_kalshi_market_snapshot function."""

    def test_builds_snapshot_with_all_fields(self):
        """Should build snapshot with all market fields."""
        from app.domains.markets.kalshi_schemas import KalshiMarket
        from app.domains.markets.kalshi_transformer import build_kalshi_market_snapshot

        market = KalshiMarket(
            ticker="INXD-25JAN17-B24999",
            event_ticker="INXD-25JAN17",
            title="S&P above 24999?",
            subtitle="By close",
            status="open",
            yes_bid=45,
            yes_ask=47,
            volume=1000,
        )

        snapshot = build_kalshi_market_snapshot(market)

        assert snapshot["ticker"] == "INXD-25JAN17-B24999"
        assert snapshot["event_ticker"] == "INXD-25JAN17"
        assert snapshot["yes_price"] == 46  # mid
        assert snapshot["yes_bid"] == 45
        assert snapshot["volume"] == 1000


class TestBuildKalshiEventContext:
    """Tests for build_kalshi_event_context function."""

    def test_builds_context_with_markets(self):
        """Should build event context with market summaries."""
        from app.domains.markets.kalshi_schemas import KalshiEvent, KalshiMarket
        from app.domains.markets.kalshi_transformer import build_kalshi_event_context

        event = KalshiEvent(
            event_ticker="INXD-25JAN17",
            title="S&P 500 Index",
            category="Economics",
            markets=[
                KalshiMarket(
                    ticker="INXD-25JAN17-B24999",
                    event_ticker="INXD-25JAN17",
                    title="Above 24999?",
                    status="open",
                    yes_bid=45,
                ),
                KalshiMarket(
                    ticker="INXD-25JAN17-B25000",
                    event_ticker="INXD-25JAN17",
                    title="Above 25000?",
                    status="open",
                    yes_bid=40,
                ),
            ],
        )

        context = build_kalshi_event_context(event)

        assert context["event_ticker"] == "INXD-25JAN17"
        assert context["market_count"] == 2
        assert context["requires_selection"] is True
        assert len(context["markets"]) == 2


def _build_market(**overrides):
    """Helper: build a KalshiMarket with sensible defaults, override per test."""
    from app.domains.markets.kalshi_schemas import KalshiMarket

    defaults = dict(
        ticker="TEST-MKT-1",
        event_ticker="TEST-EVT",
        title="Test event title",
        subtitle="Test option",
        status="active",
        yes_bid=40,
        yes_ask=42,
        no_bid=58,
        no_ask=60,
        last_price=41,
        volume=1000,
        volume_24h=200,
        open_interest=300,
        close_time=None,
    )
    defaults.update(overrides)
    return KalshiMarket(**defaults)


def test_snapshot_includes_liquidity_field_mirroring_open_interest():
    """OPEN INTEREST is shown in the frontend under the `liquidity` field
    when venue=kalshi (per AnalysisResults.tsx → MarketCard mapping).
    The transformer must emit `liquidity` so the frontend's
    `market_snapshot.liquidity ?? 0` doesn't always evaluate to 0."""
    from app.domains.markets.kalshi_transformer import build_kalshi_market_snapshot

    market = _build_market(open_interest=300)
    snapshot = build_kalshi_market_snapshot(market)

    assert snapshot["liquidity"] == 300
    assert snapshot["open_interest"] == 300


def test_snapshot_liquidity_is_none_when_open_interest_missing():
    """When Kalshi doesn't return open_interest, liquidity should be None
    (not 0) so the frontend's `?? 0` fallback handles the display rather
    than silently masking missing data as zero."""
    from app.domains.markets.kalshi_transformer import build_kalshi_market_snapshot

    market = _build_market(open_interest=None)
    snapshot = build_kalshi_market_snapshot(market)

    assert snapshot["liquidity"] is None
    assert snapshot["open_interest"] is None


def test_snapshot_preserves_other_existing_fields():
    """Sanity: don't accidentally drop any of the other snapshot fields
    when adding `liquidity`."""
    from app.domains.markets.kalshi_transformer import build_kalshi_market_snapshot

    market = _build_market(open_interest=500, volume=12345, volume_24h=678)
    snapshot = build_kalshi_market_snapshot(market)

    assert snapshot["ticker"] == "TEST-MKT-1"
    assert snapshot["volume"] == 12345
    assert snapshot["volume_24h"] == 678
    assert snapshot["status"] == "active"


def test_snapshot_includes_venue_kalshi():
    """Snapshot must carry an explicit venue marker so downstream report
    rendering (templates.py) can pick the right label + unit per venue."""
    from app.domains.markets.kalshi_transformer import build_kalshi_market_snapshot

    market = _build_market(open_interest=300)
    snapshot = build_kalshi_market_snapshot(market)

    assert snapshot["venue"] == "kalshi"
