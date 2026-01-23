# app/domains/analysis/calculations.py
"""Signal calculation utilities for probability, edge, Kelly sizing, and confidence."""

from __future__ import annotations

from typing import Any


def clamp_prob(x: float) -> float:
    """Clamp probability to [0, 1] range."""
    return max(0.0, min(1.0, x))


def infer_market_prob(market_snapshot: dict[str, Any]) -> float:
    """Extract market probability from market snapshot.

    Uses mid price or last traded price for the YES contract.
    Falls back to order book or 0.5 if price not available.
    """
    # Try yes_mid_price first (if available)
    yes_price = market_snapshot.get("yes_mid_price")

    if yes_price is None:
        # Fallback to yes_price
        yes_price = market_snapshot.get("yes_price")

    if yes_price is None:
        # Fallback to last_trade_price
        yes_price = market_snapshot.get("last_trade_price")

    if yes_price is None:
        # Final fallback: compute from best_bid and best_ask if available
        best_bid = market_snapshot.get("best_bid")
        best_ask = market_snapshot.get("best_ask")
        if best_bid is not None and best_ask is not None:
            yes_price = (best_bid + best_ask) / 2.0
        else:
            # Ultimate fallback
            yes_price = 0.5

    return clamp_prob(float(yes_price))


def compute_edge_and_ev(p_model: float, p_mkt: float) -> tuple[float, float]:
    """Compute edge and expected value per dollar.

    Args:
        p_model: Model probability (posterior)
        p_mkt: Market probability (implied price)

    Returns:
        Tuple of (edge_pct, ev_per_dollar)
        - edge_pct: Difference in probability points (p_model - p_mkt)
        - ev_per_dollar: Expected value per dollar for a $1 binary (same as edge_pct)
    """
    edge = p_model - p_mkt
    ev_per_dollar = edge  # For $1 binary, EV is same as the difference
    return edge, ev_per_dollar


def kelly_fraction_yes(p_model: float, price: float) -> float:
    """Compute Kelly fraction for YES contract.

    Formula: f* = (p_model - price) / (1 - price)

    Args:
        p_model: Model probability of YES outcome
        price: Current YES contract price

    Returns:
        Kelly fraction (can be negative, indicating bet against)
    """
    if price <= 0.0 or price >= 1.0:
        return 0.0

    if price == 1.0:
        return 0.0

    return (p_model - price) / (1.0 - price)


def kelly_fraction_no(p_model: float, price: float) -> float:
    """Compute Kelly fraction for NO contract.

    Treats NO as a contract priced at (1 - price), with true prob (1 - p_model).

    Args:
        p_model: Model probability of YES outcome
        price: Current YES contract price

    Returns:
        Kelly fraction for NO (can be negative)
    """
    p_no = 1.0 - p_model
    c_no = 1.0 - price

    if c_no <= 0.0 or c_no >= 1.0:
        return 0.0

    if c_no == 1.0:
        return 0.0

    return (p_no - c_no) / (1.0 - c_no)


def estimate_confidence(
    news_context: dict[str, Any], p_model: float, p_mkt: float
) -> tuple[str, float]:
    """Estimate confidence level and score based on news context and edge.

    Uses heuristic scoring based on:
    - Number of articles from Tavily
    - Diversity of sources
    - Recency of key news
    - Edge magnitude relative to news coverage

    Args:
        news_context: News context dictionary with articles and queries
        p_model: Model probability
        p_mkt: Market probability

    Returns:
        Tuple of (confidence_level, confidence_score)
        - confidence_level: "low", "medium", or "high"
        - confidence_score: Float in [0, 1]
    """
    # Count total articles
    articles = news_context.get("articles", [])
    if not isinstance(articles, list):
        articles = []

    total_articles = len(articles)

    # Count articles from queries (if available)
    # Check both tavily_queries and queries keys for compatibility
    queries = news_context.get("tavily_queries") or news_context.get("queries", [])
    if isinstance(queries, list):
        # If queries is a list of dicts with results, count those too
        query_article_count = 0
        for q in queries:
            if isinstance(q, dict):
                results = q.get("results", [])
                if isinstance(results, list):
                    query_article_count += len(results)
        # Use the larger count
        total_articles = max(total_articles, query_article_count)

    # Base confidence score from article count
    # Use a smooth scaling function instead of hardcoded buckets
    if total_articles == 0:
        score = 0.2
    elif total_articles == 1:
        score = 0.3
    elif total_articles < 5:
        # Scale linearly from 0.4 to 0.55 for 2-4 articles
        score = 0.4 + (total_articles - 2) * (0.55 - 0.4) / 2
    elif total_articles < 15:
        # Scale linearly from 0.5 to 0.8 for 5-14 articles
        score = 0.5 + (total_articles - 5) * (0.8 - 0.5) / 9
    else:
        # Scale from 0.8 to 0.95 for 15+ articles (diminishing returns)
        # Use logarithmic scaling for articles beyond 15
        excess_articles = min(total_articles - 15, 20)  # Cap at 35 articles
        score = 0.8 + excess_articles * (0.95 - 0.8) / 20

    # Adjust confidence based on edge magnitude
    # Larger edges require more evidence (articles) to be confident
    edge = abs(p_model - p_mkt)
    if edge > 0.30:
        # Very large edge (>30%) - need substantial evidence
        if total_articles < 10:
            score *= 0.6  # Significant penalty
        elif total_articles < 20:
            score *= 0.8  # Moderate penalty
    elif edge > 0.20:
        # Large edge (20-30%) - need good evidence
        if total_articles < 5:
            score *= 0.7  # Penalty for insufficient evidence
        elif total_articles < 10:
            score *= 0.85  # Small penalty
    elif edge > 0.10:
        # Moderate edge (10-20%) - reasonable confidence with moderate evidence
        if total_articles >= 5:
            score *= 1.05  # Small boost for well-supported moderate edges
    # Small edges (<10%) don't need adjustment

    # Check source diversity (if articles have source info)
    if isinstance(articles, list) and len(articles) > 0:
        sources = set()
        for article in articles:
            if isinstance(article, dict):
                source = article.get("source")
                if source:
                    sources.add(str(source))

        # More diverse sources = higher confidence
        unique_sources = len(sources)
        if unique_sources > 5:
            # Strong boost for diverse sources
            score = max(score * 1.1, 0.7)
        elif unique_sources < 2 and total_articles > 5:
            score *= 0.9  # Penalize if many articles but few sources

    # Clamp score to [0, 1]
    score = clamp_prob(score)

    # Bucket into low/medium/high
    if score < 0.4:
        level = "low"
    elif score < 0.7:
        level = "medium"
    else:
        level = "high"

    return level, score


# =============================================================================
# Cents-based calculations (for Kalshi integration)
# All probabilities are integers 1-99 representing cents
# =============================================================================


def clamp_prob_cents(prob: int) -> int:
    """Clamp probability to valid cents range (1-99).

    Args:
        prob: Probability in cents

    Returns:
        Clamped probability (1-99)
    """
    return max(1, min(99, prob))


def compute_edge_cents(model_prob: int, market_prob: int) -> int:
    """Compute edge (model - market) in cents.

    Args:
        model_prob: Model probability in cents (1-99)
        market_prob: Market probability in cents (1-99)

    Returns:
        Edge in cents (positive = buy YES, negative = buy NO)
    """
    return model_prob - market_prob


def kelly_fraction_yes_cents(model_prob: int, market_prob: int) -> int:
    """Calculate Kelly fraction for YES bet using cents.

    Args:
        model_prob: Model probability in cents (1-99)
        market_prob: Market probability in cents (1-99)

    Returns:
        Kelly fraction as percentage (0-100) of bankroll to bet
    """
    if market_prob <= 0 or market_prob >= 100:
        return 0
    if model_prob <= market_prob:
        return 0  # No edge for YES

    # Convert to decimals for math
    p = model_prob / 100
    q = 1 - p
    # Odds: payout ratio for winning YES bet
    odds = (100 - market_prob) / market_prob

    kelly = (p * odds - q) / odds
    return min(max(0, int(kelly * 100)), 100)


def kelly_fraction_no_cents(model_prob: int, market_prob: int) -> int:
    """Calculate Kelly fraction for NO bet using cents.

    Args:
        model_prob: Model probability in cents (1-99)
        market_prob: Market probability in cents (1-99)

    Returns:
        Kelly fraction as percentage (0-100) of bankroll to bet
    """
    if market_prob <= 0 or market_prob >= 100:
        return 0
    if model_prob >= market_prob:
        return 0  # No edge for NO

    # For NO bet: model thinks YES is less likely than market
    model_no = 100 - model_prob
    market_no = 100 - market_prob

    p = model_no / 100
    q = 1 - p
    odds = (100 - market_no) / market_no

    kelly = (p * odds - q) / odds
    return min(max(0, int(kelly * 100)), 100)


def infer_market_prob_cents(market_snapshot: dict) -> int:
    """Extract market probability from snapshot in cents.

    Prioritizes: yes_price > mid(yes_bid, yes_ask) > last_trade_price > 50

    Args:
        market_snapshot: Market snapshot dictionary

    Returns:
        Market probability in cents (1-99)
    """
    # Try yes_price first
    yes_price = market_snapshot.get("yes_price")
    if yes_price is not None:
        return clamp_prob_cents(int(yes_price))

    # Try mid of bid/ask
    yes_bid = market_snapshot.get("yes_bid")
    yes_ask = market_snapshot.get("yes_ask")
    if yes_bid is not None and yes_ask is not None:
        mid = (yes_bid + yes_ask) // 2
        return clamp_prob_cents(mid)

    # Try bid only
    if yes_bid is not None:
        return clamp_prob_cents(int(yes_bid))

    # Try last trade
    last_price = market_snapshot.get("last_trade_price")
    if last_price is not None:
        return clamp_prob_cents(int(last_price))

    # Default to 50 cents (50%)
    return 50
