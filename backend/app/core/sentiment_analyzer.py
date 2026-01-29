"""Sentiment analysis for news articles based on market context."""

from __future__ import annotations

import re
from typing import Any, Literal

from app.core.logging_config import get_logger

logger = get_logger(__name__)

Sentiment = Literal["bullish", "bearish", "neutral"]

# Bullish keywords (support YES outcome)
BULLISH_PATTERNS: frozenset[str] = frozenset([
    # Price/movement up
    "increase", "increased", "increasing", "rise", "rises", "rising", "rose",
    "up", "higher", "high", "grow", "growing", "grew", "gain", "gained", "gains",
    "surge", "surged", "surges", "rally", "rallied", "rallies", "soar", "soared",
    "jump", "jumped", "jumps", "climb", "climbed", "climbs", "boost", "boosted",
    # Positive sentiment
    "positive", "optimistic", "optimism", "strong", "strength", "stronger",
    "beat", "beats", "beaten", "exceed", "exceeded", "exceeds",
    "outperform", "outperformed", "outperforms", "success", "successful",
    "succeed", "succeeded",
    # Approval/support
    "approve", "approved", "approval", "pass", "passed", "passes",
    "support", "supported", "supports", "favor", "favored", "favors",
    "win", "won", "wins", "victory", "victories", "triumph", "triumphs",
    # Monetary policy (dovish = bullish for rate cut markets)
    "cut rates", "rate cut", "rate cuts", "lower rates", "dovish",
    "stimulus", "easing", "ease", "eased", "quantitative easing", "qe",
    "accommodative",
    # Market positive
    "bullish", "bull market", "breakthrough", "milestone", "record high",
])

# Bearish keywords (support NO outcome)
BEARISH_PATTERNS: frozenset[str] = frozenset([
    # Price/movement down
    "decrease", "decreased", "decreasing", "fall", "falls", "fell", "fallen",
    "down", "lower", "low", "decline", "declined", "declines", "drop", "dropped",
    "drops", "plunge", "plunged", "plunges", "crash", "crashed", "crashes",
    "collapse", "collapsed", "collapses", "sink", "sank", "sinks",
    "slump", "slumped", "slumps", "dip", "dipped", "dips", "slide", "slid", "slides",
    # Negative sentiment
    "negative", "negatively", "pessimistic", "pessimism", "weak", "weaker",
    "weakness", "miss", "missed", "misses", "underperform", "underperformed",
    "underperforms", "disappoint", "disappointed", "disappoints", "disappointment",
    "concern", "concerns", "concerned", "worry", "worries", "worried",
    # Rejection/failure
    "reject", "rejected", "rejects", "rejection", "fail", "failed", "fails",
    "failure", "oppose", "opposed", "opposes", "opposition", "against",
    "loss", "losses", "lost", "defeat", "defeated", "defeats",
    # Monetary policy (hawkish = bearish for rate cut markets)
    "raise rates", "rate hike", "rate hikes", "hike rates", "hawkish",
    "tighten", "tightened", "tightening", "restrictive", "restriction", "restrictions",
    # Market negative
    "bearish", "bear market", "correction", "corrections", "volatility",
    "uncertainty", "risk", "risks", "risky", "threat", "threats",
    "threaten", "threatened",
])

NEGATION_WORDS: frozenset[str] = frozenset([
    "not", "no", "never", "neither", "nobody", "none", "nothing",
    "nowhere", "without", "lack", "lacks", "lacking",
])


def _count_pattern_matches(text: str, patterns: frozenset[str]) -> int:
    """Count how many patterns match in the text using word boundary matching."""
    count = 0
    for pattern in patterns:
        if re.search(r"\b" + re.escape(pattern) + r"\b", text):
            count += 1
    return count


def _apply_negation_adjustments(
    text: str,
    bullish_count: int,
    bearish_count: int,
) -> tuple[int, int]:
    """Adjust sentiment counts when negation words are near sentiment terms."""
    for negation in NEGATION_WORDS:
        negation_pos = text.find(negation)
        if negation_pos == -1:
            continue

        # Check if negation is near bullish terms (within 20 chars)
        for pattern in BULLISH_PATTERNS:
            pattern_pos = text.find(pattern)
            if pattern_pos != -1 and abs(pattern_pos - negation_pos) < 20:
                bearish_count += 1
                bullish_count = max(0, bullish_count - 1)

        # Check if negation is near bearish terms (within 20 chars)
        for pattern in BEARISH_PATTERNS:
            pattern_pos = text.find(pattern)
            if pattern_pos != -1 and abs(pattern_pos - negation_pos) < 20:
                bullish_count += 1
                bearish_count = max(0, bearish_count - 1)

    return bullish_count, bearish_count


def _apply_context_adjustments(
    text: str,
    question_lower: str,
    bullish_count: int,
    bearish_count: int,
) -> tuple[int, int]:
    """Adjust counts based on market question context."""
    if "increase" in question_lower or "rise" in question_lower:
        # Market is asking about increase - bullish = supports increase
        if "increase" in text or "rise" in text or "higher" in text:
            bullish_count += 2
        if "decrease" in text or "fall" in text or "lower" in text:
            bearish_count += 2
    elif "decrease" in question_lower or "fall" in question_lower or "cut" in question_lower:
        # Market is asking about decrease - bullish = supports decrease
        if "decrease" in text or "cut" in text or "lower" in text:
            bullish_count += 2
        if "increase" in text or "rise" in text or "hike" in text:
            bearish_count += 2
    elif "fed" in question_lower or "interest rate" in question_lower:
        # Fed/rate markets - context matters
        if "cut" in text or "lower" in text or "dovish" in text:
            bullish_count += 2
        if "hike" in text or "raise" in text or "hawkish" in text:
            bearish_count += 2

    return bullish_count, bearish_count


def _determine_sentiment(bullish_count: int, bearish_count: int) -> Sentiment:
    """Determine final sentiment based on counts."""
    if bullish_count > bearish_count and bullish_count >= 1:
        return "bullish"
    if bearish_count > bullish_count and bearish_count >= 1:
        return "bearish"
    return "neutral"


def analyze_article_sentiment(
    article: dict[str, Any],
    market_question: str,
    yes_price: float,
    signal_direction: str | None = None,
    outcomes: list[str] | None = None,
) -> Sentiment:
    """Analyze sentiment of a news article relative to market position.

    This function evaluates whether an article is bullish (supports YES outcome),
    bearish (supports NO outcome), or neutral based on:
    - Article title and content
    - Market question and outcomes
    - Current YES price
    - Signal direction (if available)

    Args:
        article: Article dict with title, snippet/content
        market_question: The market question (e.g., "Will X happen?")
        yes_price: Current YES price (0-1)
        signal_direction: Optional signal direction ("up", "down", "flat")
        outcomes: Optional list of outcomes (e.g., ["Yes", "No"])

    Returns:
        "bullish", "bearish", or "neutral"
    """
    title = (article.get("title") or "").lower()
    content = (article.get("snippet") or article.get("content") or "").lower()
    text = f"{title} {content}"

    if not text.strip():
        logger.debug(
            "Article has no text for sentiment analysis",
            title=article.get("title", "")[:50],
        )
        return "neutral"

    question_lower = market_question.lower()

    # Count pattern matches
    bullish_count = _count_pattern_matches(text, BULLISH_PATTERNS)
    bearish_count = _count_pattern_matches(text, BEARISH_PATTERNS)

    # Apply negation adjustments
    bullish_count, bearish_count = _apply_negation_adjustments(
        text, bullish_count, bearish_count
    )

    # Apply context-aware adjustments based on market question
    bullish_count, bearish_count = _apply_context_adjustments(
        text, question_lower, bullish_count, bearish_count
    )

    # Consider signal direction if available
    if signal_direction == "up":
        bullish_count += 1
    elif signal_direction == "down":
        bearish_count += 1

    # Consider current price position - boost significance at extremes
    if yes_price < 0.1:
        bullish_count = int(bullish_count * 1.2)
    elif yes_price > 0.9:
        bearish_count = int(bearish_count * 1.2)

    sentiment = _determine_sentiment(bullish_count, bearish_count)

    logger.debug(
        "Sentiment analysis result",
        title=article.get("title", "")[:50],
        bullish_count=bullish_count,
        bearish_count=bearish_count,
        sentiment=sentiment,
        has_content=bool(content),
        text_length=len(text),
    )

    return sentiment


def analyze_articles_sentiment(
    articles: list[dict[str, Any]],
    market_question: str,
    yes_price: float,
    signal_direction: str | None = None,
    outcomes: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Analyze sentiment for a list of articles and add sentiment field.

    Args:
        articles: List of article dicts
        market_question: The market question
        yes_price: Current YES price
        signal_direction: Optional signal direction
        outcomes: Optional list of outcomes

    Returns:
        List of articles with sentiment field added
    """
    return [
        {
            **article,
            "sentiment": analyze_article_sentiment(
                article=article,
                market_question=market_question,
                yes_price=yes_price,
                signal_direction=signal_direction,
                outcomes=outcomes,
            ),
        }
        for article in articles
    ]
