"""Tests for Signal Utilities."""

from __future__ import annotations

from app.core.signal_utils import (
    clamp_prob,
    compute_edge_and_ev,
    estimate_confidence,
    infer_market_prob,
    kelly_fraction_no,
    kelly_fraction_yes,
)


def test_clamp_prob_in_range():
    """Test clamp_prob with values in range."""
    assert clamp_prob(0.5) == 0.5
    assert clamp_prob(0.0) == 0.0
    assert clamp_prob(1.0) == 1.0


def test_clamp_prob_below_zero():
    """Test clamp_prob with values below 0."""
    assert clamp_prob(-0.5) == 0.0
    assert clamp_prob(-10.0) == 0.0


def test_clamp_prob_above_one():
    """Test clamp_prob with values above 1."""
    assert clamp_prob(1.5) == 1.0
    assert clamp_prob(10.0) == 1.0


def test_infer_market_prob_yes_price():
    """Test infer_market_prob with yes_price."""
    snapshot = {"yes_price": 0.6}
    assert infer_market_prob(snapshot) == 0.6


def test_infer_market_prob_yes_mid_price():
    """Test infer_market_prob with yes_mid_price."""
    snapshot = {"yes_mid_price": 0.7}
    assert infer_market_prob(snapshot) == 0.7


def test_infer_market_prob_last_trade_price():
    """Test infer_market_prob with last_trade_price."""
    snapshot = {"last_trade_price": 0.55}
    assert infer_market_prob(snapshot) == 0.55


def test_infer_market_prob_from_bid_ask():
    """Test infer_market_prob computed from best_bid and best_ask."""
    snapshot = {
        "best_bid": 0.48,
        "best_ask": 0.52,
    }
    result = infer_market_prob(snapshot)
    assert result == 0.5  # (0.48 + 0.52) / 2


def test_infer_market_prob_missing_price():
    """Test infer_market_prob with missing price data."""
    snapshot = {}
    result = infer_market_prob(snapshot)
    assert result == 0.5  # Fallback


def test_compute_edge_and_ev():
    """Test compute_edge_and_ev with various probability combinations."""
    edge, ev = compute_edge_and_ev(0.6, 0.5)
    # Use approximate equality for floating point comparison
    assert abs(edge - 0.1) < 1e-10
    assert abs(ev - 0.1) < 1e-10

    edge, ev = compute_edge_and_ev(0.4, 0.5)
    assert abs(edge - (-0.1)) < 1e-10
    assert abs(ev - (-0.1)) < 1e-10


def test_compute_edge_and_ev_edge_cases():
    """Test compute_edge_and_ev with edge cases."""
    edge, ev = compute_edge_and_ev(0.5, 0.5)
    assert edge == 0.0
    assert ev == 0.0


def test_kelly_fraction_yes():
    """Test kelly_fraction_yes with various inputs."""
    # Positive edge
    kelly = kelly_fraction_yes(0.6, 0.5)
    assert kelly > 0

    # Negative edge
    kelly = kelly_fraction_yes(0.4, 0.5)
    assert kelly < 0


def test_kelly_fraction_yes_edge_cases():
    """Test kelly_fraction_yes with edge cases."""
    # Price = 0
    kelly = kelly_fraction_yes(0.6, 0.0)
    assert kelly == 0.0

    # Price = 1
    kelly = kelly_fraction_yes(0.6, 1.0)
    assert kelly == 0.0

    # Price > 1
    kelly = kelly_fraction_yes(0.6, 1.5)
    assert kelly == 0.0


def test_kelly_fraction_no():
    """Test kelly_fraction_no with various inputs."""
    # Positive edge for NO
    kelly = kelly_fraction_no(0.4, 0.5)  # p_model=0.4 means p_no=0.6, price=0.5 means c_no=0.5
    assert kelly > 0

    # Negative edge for NO
    kelly = kelly_fraction_no(0.6, 0.5)  # p_model=0.6 means p_no=0.4, price=0.5 means c_no=0.5
    assert kelly < 0


def test_kelly_fraction_no_edge_cases():
    """Test kelly_fraction_no with edge cases."""
    # Price = 0 (c_no = 1)
    kelly = kelly_fraction_no(0.6, 0.0)
    assert kelly == 0.0

    # Price = 1 (c_no = 0)
    kelly = kelly_fraction_no(0.6, 1.0)
    assert kelly == 0.0


def test_estimate_confidence_no_articles():
    """Test estimate_confidence with no articles."""
    news_context = {"articles": []}
    level, score = estimate_confidence(news_context, 0.6, 0.5)

    assert level == "low"
    assert score == 0.2


def test_estimate_confidence_few_articles():
    """Test estimate_confidence with few articles."""
    news_context = {
        "articles": [
            {"title": "Article 1"},
            {"title": "Article 2"},
        ]
    }
    level, score = estimate_confidence(news_context, 0.6, 0.5)

    # With 2 articles (< 5), score ≈ 0.367, which gives level "low" (< 0.4)
    assert level == "low"
    assert 0.3 <= score <= 0.4


def test_estimate_confidence_many_articles():
    """Test estimate_confidence with many articles."""
    news_context = {"articles": [{"title": f"Article {i}"} for i in range(20)]}
    level, score = estimate_confidence(news_context, 0.6, 0.5)

    assert level == "high"
    assert score >= 0.7


def test_estimate_confidence_source_diversity():
    """Test estimate_confidence with diverse sources."""
    news_context = {
        "articles": [
            {"title": "Article 1", "source": "Source1"},
            {"title": "Article 2", "source": "Source2"},
            {"title": "Article 3", "source": "Source3"},
            {"title": "Article 4", "source": "Source4"},
            {"title": "Article 5", "source": "Source5"},
            {"title": "Article 6", "source": "Source6"},
        ]
    }
    level, score = estimate_confidence(news_context, 0.6, 0.5)

    # 6 articles gives base score ~0.533, diversity boost gives ~0.587 (medium)
    assert level == "medium"
    assert 0.5 <= score <= 0.7


def test_estimate_confidence_large_edge_penalty():
    """Test estimate_confidence penalizes large edge without news."""
    news_context = {"articles": [{"title": "Article 1"}]}
    level, score = estimate_confidence(news_context, 0.8, 0.5)  # Large edge

    # Should be penalized for large edge with few articles
    assert score < 0.5


def test_estimate_confidence_from_queries():
    """Test estimate_confidence using articles from queries."""
    news_context = {
        "queries": [
            {
                "results": [
                    {"title": "Result 1"},
                    {"title": "Result 2"},
                ]
            }
        ]
    }
    level, score = estimate_confidence(news_context, 0.6, 0.5)

    # Should use query results if more than direct articles
    assert score >= 0.3


def test_estimate_confidence_invalid_articles():
    """Test estimate_confidence with invalid articles list."""
    news_context = {"articles": "not a list"}
    level, score = estimate_confidence(news_context, 0.6, 0.5)

    # Should handle gracefully
    assert level in ["low", "medium", "high"]
    assert 0.0 <= score <= 1.0
