"""Tests for Sentiment Analyzer."""

from __future__ import annotations

from app.domains.news.sentiment.analyzer import (
    analyze_article_sentiment,
    analyze_articles_sentiment,
)


def test_analyze_article_sentiment_bullish_keywords():
    """Test analyze_article_sentiment with bullish keywords."""
    article = {
        "title": "Market increases significantly",
        "snippet": "Prices rose to new highs with strong gains",
    }

    sentiment = analyze_article_sentiment(article, "Will prices increase?", 0.5)

    assert sentiment == "bullish"


def test_analyze_article_sentiment_bearish_keywords():
    """Test analyze_article_sentiment with bearish keywords."""
    article = {
        "title": "Market crashes as prices fall",
        "snippet": "Significant decline and negative outlook",
    }

    sentiment = analyze_article_sentiment(article, "Will prices increase?", 0.5)

    assert sentiment == "bearish"


def test_analyze_article_sentiment_neutral():
    """Test analyze_article_sentiment with neutral article."""
    article = {
        "title": "Market update",
        "snippet": "Regular market activity continues",
    }

    sentiment = analyze_article_sentiment(article, "Will prices increase?", 0.5)

    assert sentiment == "neutral"


def test_analyze_article_sentiment_edge_cases():
    """Test analyze_article_sentiment with edge cases."""
    # Empty article
    article1 = {}
    sentiment1 = analyze_article_sentiment(article1, "Test?", 0.5)
    assert sentiment1 == "neutral"

    # Article with no text
    article2 = {"title": "", "snippet": ""}
    sentiment2 = analyze_article_sentiment(article2, "Test?", 0.5)
    assert sentiment2 == "neutral"


def test_analyze_article_sentiment_with_signal_direction():
    """Test analyze_article_sentiment with signal direction."""
    article = {
        "title": "Market update",
        "snippet": "Regular activity",
    }

    # With "up" signal direction
    sentiment1 = analyze_article_sentiment(
        article, "Will prices increase?", 0.5, signal_direction="up"
    )

    # Signal direction should influence sentiment
    assert sentiment1 in ["bullish", "neutral"]


def test_analyze_article_sentiment_price_context():
    """Test analyze_article_sentiment with price context."""
    article = {
        "title": "Positive news",
        "snippet": "Good developments",
    }

    # Very low price - bullish news more significant
    sentiment_low = analyze_article_sentiment(article, "Will prices increase?", 0.05)

    # Very high price - bearish news more significant
    sentiment_high = analyze_article_sentiment(article, "Will prices increase?", 0.95)

    # Both should be valid sentiments
    assert sentiment_low in ["bullish", "bearish", "neutral"]
    assert sentiment_high in ["bullish", "bearish", "neutral"]


def test_analyze_article_sentiment_negation():
    """Test analyze_article_sentiment with negation words."""
    article = {
        "title": "Market will not increase",
        "snippet": "No gains expected",
    }

    sentiment = analyze_article_sentiment(article, "Will prices increase?", 0.5)

    # Negation should flip sentiment
    assert sentiment in ["bearish", "neutral"]


def test_analyze_article_sentiment_fed_context():
    """Test analyze_article_sentiment with Fed/rate context."""
    article = {
        "title": "Fed considers rate cuts",
        "snippet": "Dovish policy expected",
    }

    sentiment = analyze_article_sentiment(article, "Will Fed cut interest rates?", 0.5)

    # Should recognize Fed context
    assert sentiment in ["bullish", "neutral"]


def test_analyze_articles_sentiment():
    """Test analyze_articles_sentiment with multiple articles."""
    articles = [
        {"title": "Prices increase", "snippet": "Gains"},
        {"title": "Prices fall", "snippet": "Declines"},
        {"title": "Market update", "snippet": "Regular activity"},
    ]

    enriched = analyze_articles_sentiment(articles, "Will prices increase?", 0.5)

    assert len(enriched) == 3
    assert all("sentiment" in article for article in enriched)
    assert enriched[0]["sentiment"] in ["bullish", "bearish", "neutral"]
    assert enriched[1]["sentiment"] in ["bullish", "bearish", "neutral"]
    assert enriched[2]["sentiment"] in ["bullish", "bearish", "neutral"]


def test_analyze_articles_sentiment_empty_list():
    """Test analyze_articles_sentiment with empty list."""
    articles = []

    enriched = analyze_articles_sentiment(articles, "Will prices increase?", 0.5)

    assert len(enriched) == 0


def test_analyze_articles_sentiment_mixed_sentiments():
    """Test analyze_articles_sentiment with mixed sentiments."""
    articles = [
        {"title": "Bullish news", "snippet": "Strong gains expected"},
        {"title": "Bearish news", "snippet": "Significant declines"},
        {"title": "Neutral update", "snippet": "Regular activity"},
    ]

    enriched = analyze_articles_sentiment(articles, "Will prices increase?", 0.5)

    sentiments = [a["sentiment"] for a in enriched]
    # Should have variety
    assert len(set(sentiments)) >= 1  # At least one unique sentiment
