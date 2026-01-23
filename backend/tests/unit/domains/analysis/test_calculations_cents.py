"""Tests for cents-based calculation utilities."""

import pytest


class TestClampProbCents:
    """Tests for clamp_prob_cents function."""

    def test_valid_value_unchanged(self):
        """Should return valid value unchanged."""
        from app.domains.analysis.calculations import clamp_prob_cents

        assert clamp_prob_cents(50) == 50
        assert clamp_prob_cents(1) == 1
        assert clamp_prob_cents(99) == 99

    def test_clamps_low_values(self):
        """Should clamp values below 1 to 1."""
        from app.domains.analysis.calculations import clamp_prob_cents

        assert clamp_prob_cents(0) == 1
        assert clamp_prob_cents(-5) == 1

    def test_clamps_high_values(self):
        """Should clamp values above 99 to 99."""
        from app.domains.analysis.calculations import clamp_prob_cents

        assert clamp_prob_cents(100) == 99
        assert clamp_prob_cents(150) == 99


class TestComputeEdgeCents:
    """Tests for compute_edge_cents function."""

    def test_positive_edge(self):
        """Should compute positive edge correctly."""
        from app.domains.analysis.calculations import compute_edge_cents

        # Model thinks 60%, market shows 50%
        assert compute_edge_cents(60, 50) == 10

    def test_negative_edge(self):
        """Should compute negative edge correctly."""
        from app.domains.analysis.calculations import compute_edge_cents

        # Model thinks 40%, market shows 50%
        assert compute_edge_cents(40, 50) == -10

    def test_zero_edge(self):
        """Should return zero when probabilities match."""
        from app.domains.analysis.calculations import compute_edge_cents

        assert compute_edge_cents(50, 50) == 0


class TestKellyFractionYesCents:
    """Tests for kelly_fraction_yes_cents function."""

    def test_positive_edge_returns_fraction(self):
        """Should return positive Kelly fraction when model > market."""
        from app.domains.analysis.calculations import kelly_fraction_yes_cents

        # Model 60%, market 50%, should bet YES
        fraction = kelly_fraction_yes_cents(60, 50)
        assert fraction > 0
        assert fraction <= 100

    def test_no_edge_returns_zero(self):
        """Should return 0 when no edge."""
        from app.domains.analysis.calculations import kelly_fraction_yes_cents

        assert kelly_fraction_yes_cents(50, 50) == 0

    def test_negative_edge_returns_zero(self):
        """Should return 0 when model < market (no YES bet)."""
        from app.domains.analysis.calculations import kelly_fraction_yes_cents

        assert kelly_fraction_yes_cents(40, 50) == 0


class TestKellyFractionNoCents:
    """Tests for kelly_fraction_no_cents function."""

    def test_negative_edge_returns_fraction(self):
        """Should return positive Kelly fraction when model < market."""
        from app.domains.analysis.calculations import kelly_fraction_no_cents

        # Model 40%, market 50%, should bet NO
        fraction = kelly_fraction_no_cents(40, 50)
        assert fraction > 0
        assert fraction <= 100

    def test_no_edge_returns_zero(self):
        """Should return 0 when no edge."""
        from app.domains.analysis.calculations import kelly_fraction_no_cents

        assert kelly_fraction_no_cents(50, 50) == 0

    def test_positive_edge_returns_zero(self):
        """Should return 0 when model > market (no NO bet)."""
        from app.domains.analysis.calculations import kelly_fraction_no_cents

        assert kelly_fraction_no_cents(60, 50) == 0


class TestInferMarketProbCents:
    """Tests for infer_market_prob_cents function."""

    def test_uses_yes_price(self):
        """Should use yes_price from snapshot."""
        from app.domains.analysis.calculations import infer_market_prob_cents

        snapshot = {"yes_price": 45}
        assert infer_market_prob_cents(snapshot) == 45

    def test_uses_yes_bid_ask_mid(self):
        """Should calculate mid from yes_bid and yes_ask."""
        from app.domains.analysis.calculations import infer_market_prob_cents

        snapshot = {"yes_bid": 44, "yes_ask": 48}
        assert infer_market_prob_cents(snapshot) == 46

    def test_falls_back_to_last_trade(self):
        """Should fall back to last_trade_price."""
        from app.domains.analysis.calculations import infer_market_prob_cents

        snapshot = {"last_trade_price": 50}
        assert infer_market_prob_cents(snapshot) == 50

    def test_returns_50_as_default(self):
        """Should return 50 cents when no price available."""
        from app.domains.analysis.calculations import infer_market_prob_cents

        snapshot = {}
        assert infer_market_prob_cents(snapshot) == 50
