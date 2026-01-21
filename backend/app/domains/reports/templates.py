# app/domains/reports/templates.py
"""Fallback templates for report generation."""

from __future__ import annotations

from textwrap import dedent
from typing import Any, Dict, Mapping, Optional

from pydantic import BaseModel


def signal_to_dict(signal: Any) -> dict:
    """Normalize Signal into a plain dict.

    Args:
        signal: Signal model or dict

    Returns:
        Plain dict representation
    """
    if isinstance(signal, BaseModel):
        return signal.model_dump()
    if isinstance(signal, Mapping):
        return dict(signal)
    return {}


def generate_fallback_report(
    market_snapshot: Dict[str, Any],
    signal: Dict[str, Any],
    decision: Dict[str, Any],
    event_context: Optional[Dict[str, Any]] = None,
    news_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a basic templated report when LLM fails.

    Args:
        market_snapshot: Market snapshot dict
        signal: Signal dict
        decision: Decision dict
        event_context: Event context dict (optional)
        news_context: News context dict (optional)

    Returns:
        Report data dict
    """
    s = signal_to_dict(signal)

    # Extract probabilities with fallbacks
    market_prob = (
        s.get("market_prob")
        or s.get("p_mkt")
        or s.get("p_market")
        or s.get("model_prob_abs")
        or 0.0
    )

    model_prob = (
        s.get("model_prob")
        or s.get("p_model")
        or s.get("model_prob_abs")
        or market_prob
    )

    edge_pct = decision.get("edge_pct") or s.get("edge_pct")
    if edge_pct is None:
        edge_pct = abs(model_prob - market_prob)

    confidence = s.get("confidence_level") or s.get("confidence") or "low"

    action = decision.get("action", "HOLD")
    size = s.get("recommended_size_fraction", 0)
    tp = s.get("target_take_profit_prob")
    sl = s.get("target_stop_loss_prob")

    # Build report sections
    headline = (
        f"Model estimates {model_prob:.1%} vs market {market_prob:.1%}. "
        f"Edge {edge_pct:.2%}. Confidence {confidence.upper()}."
    )

    thesis = (
        f"Our model estimates the true probability at {model_prob:.1%}, compared to the market's "
        f"implied probability of {market_prob:.1%}, giving us an edge of {edge_pct:.2%}. "
        f"Confidence level is {confidence.upper()}. "
        f"Recommended action: {action} with position size {size:.1%}."
    )

    bull_case = [
        f"Model sees {model_prob:.1%} probability vs market {market_prob:.1%}",
        f"Edge of {edge_pct:.2%} suggests market mispricing",
    ]

    bear_case = [
        "Market may be correctly pricing the event",
        "Limited edge suggests cautious approach",
    ]

    key_risks = [
        "Model uncertainty",
        "Market volatility",
    ]

    execution_notes = f"Recommended {action} with {size:.1%} position size."
    if tp:
        execution_notes += f" Take profit at {tp:.1%}."
    if sl:
        execution_notes += f" Stop loss at {sl:.1%}."

    # Build markdown
    markdown = dedent(
        f"""
        ## TL;DR
        Action: **{action}** with edge ~{edge_pct:.2%}.

        ## Market snapshot
        - Question: {market_snapshot.get("question", "N/A")}
        - Yes price: {market_snapshot.get("yes_price", 0):.2%}
        - Liquidity: {market_snapshot.get("liquidity", 0):,.0f} USDC

        ## Rationale
        {decision.get("notes", "Strategy placeholder.")}
        """
    ).strip()

    return {
        "headline": headline,
        "thesis": thesis,
        "bull_case": bull_case,
        "bear_case": bear_case,
        "key_risks": key_risks,
        "execution_notes": execution_notes,
        "title": headline,
        "markdown": markdown,
    }
