# app/domains/news/sentiment/__init__.py
"""Sentiment analysis exports."""

from app.domains.news.sentiment.analyzer import (
    Sentiment,
    analyze_article_sentiment,
    analyze_articles_sentiment,
)
from app.domains.news.sentiment.patterns import (
    BEARISH_PATTERNS,
    BULLISH_PATTERNS,
    NEGATION_WORDS,
)

__all__ = [
    "BEARISH_PATTERNS",
    "BULLISH_PATTERNS",
    "NEGATION_WORDS",
    "Sentiment",
    "analyze_article_sentiment",
    "analyze_articles_sentiment",
]
