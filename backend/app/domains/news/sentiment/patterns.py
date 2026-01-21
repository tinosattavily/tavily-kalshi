# app/domains/news/sentiment/patterns.py
"""Sentiment analysis keyword patterns."""

from typing import List

# Bullish keywords (support YES outcome)
BULLISH_PATTERNS: List[str] = [
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
    "bullish", "bull market", "rally", "breakthrough", "milestone", "record high",
]

# Bearish keywords (support NO outcome)
BEARISH_PATTERNS: List[str] = [
    # Price/movement down
    "decrease", "decreased", "decreasing", "fall", "falls", "fell", "fallen",
    "down", "lower", "low", "decline", "declined", "declines",
    "drop", "dropped", "drops", "plunge", "plunged", "plunges",
    "crash", "crashed", "crashes", "collapse", "collapsed", "collapses",
    "sink", "sank", "sinks", "slump", "slumped", "slumps",
    "dip", "dipped", "dips", "slide", "slid", "slides",
    # Negative sentiment
    "negative", "negatively", "pessimistic", "pessimism",
    "weak", "weaker", "weakness", "miss", "missed", "misses",
    "underperform", "underperformed", "underperforms",
    "disappoint", "disappointed", "disappoints", "disappointment",
    "concern", "concerns", "concerned", "worry", "worries", "worried",
    # Rejection/failure
    "reject", "rejected", "rejects", "rejection",
    "fail", "failed", "fails", "failure",
    "oppose", "opposed", "opposes", "opposition", "against",
    "loss", "losses", "lost", "defeat", "defeated", "defeats",
    # Monetary policy (hawkish = bearish for rate cut markets)
    "raise rates", "rate hike", "rate hikes", "hike rates", "hawkish",
    "tighten", "tightened", "tightening", "restrictive", "restriction", "restrictions",
    # Market negative
    "bearish", "bear market", "correction", "corrections",
    "volatility", "uncertainty", "risk", "risks", "risky",
    "threat", "threats", "threaten", "threatened",
]

# Negation words that flip sentiment
NEGATION_WORDS: List[str] = [
    "not", "no", "never", "neither", "nobody", "none", "nothing",
    "nowhere", "without", "lack", "lacks", "lacking",
]
