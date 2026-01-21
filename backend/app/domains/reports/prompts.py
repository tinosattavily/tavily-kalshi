# app/domains/reports/prompts.py
"""LLM prompt templates for report generation."""

from __future__ import annotations

from typing import Any, Dict, Optional


SYSTEM_PROMPT = (
    "You are writing a concise trade note for a prediction market. "
    "You will receive structured data about the market, model signal, "
    "news, and recommended action. "
    "Return ONLY a valid JSON object with the exact fields specified. "
    "Do not include any markdown formatting or code blocks."
)


def build_user_prompt(
    market_question: str,
    yes_price: float,
    market_prob: float,
    model_prob: float,
    edge_pct: float,
    kelly: float,
    confidence: str,
    confidence_score: float,
    rationale: str,
    action: str,
    size: float,
    tp: Optional[float],
    sl: Optional[float],
    news_summary: str = "",
    sentiment_dist: str = "",
) -> str:
    """Build the user prompt for report generation.

    Args:
        market_question: The market question
        yes_price: Current YES price
        market_prob: Market implied probability
        model_prob: Model estimated probability
        edge_pct: Edge in percentage points
        kelly: Kelly fraction for YES
        confidence: Confidence level string
        confidence_score: Confidence score
        rationale: Model rationale
        action: Recommended action
        size: Position size fraction
        tp: Take profit probability (optional)
        sl: Stop loss probability (optional)
        news_summary: News summary (optional)
        sentiment_dist: Sentiment distribution string (optional)

    Returns:
        Formatted user prompt string
    """
    # Format tp and sl safely
    tp_str = f"{tp:.4f} ({tp * 100:.2f}%)" if tp is not None else "None (N/A)"
    sl_str = f"{sl:.4f} ({sl * 100:.2f}%)" if sl is not None else "None (N/A)"

    return f"""
You are analyzing a prediction market trade. Here is the structured data:

**Market Snapshot:**
- Question: {market_question}
- YES price: {yes_price:.4f} ({yes_price * 100:.2f}%)
- Market implied probability: {market_prob:.4f} ({market_prob * 100:.2f}%)

**Model Signal:**
- Model probability: {model_prob:.4f} ({model_prob * 100:.2f}%)
- Edge: {edge_pct:.4f} ({edge_pct * 100:.2f} percentage points)
- Kelly fraction (YES): {kelly:.4f} ({kelly * 100:.2f}%)
- Confidence: {confidence.upper()} (score: {confidence_score:.2f})
- Rationale: {rationale or "No rationale provided"}

**Recommended Action:**
- Action: {action}
- Position size: {size:.4f} ({size * 100:.2f}%)
- Take profit: {tp_str}
- Stop loss: {sl_str}

**News Context:**
{f"Summary: {news_summary}" if news_summary else "No news summary available"}
{f"Sentiment distribution: {sentiment_dist}" if sentiment_dist else ""}

Return a JSON object with these exact fields:
{{
  "headline": "1 sentence, punchy, mention model vs market if relevant",
  "thesis": "3-5 sentences tying together market context, news, and model edge",
  "bull_case": ["bullet 1", "bullet 2", "bullet 3"],
  "bear_case": ["bullet 1", "bullet 2", "bullet 3"],
  "key_risks": ["risk 1", "risk 2", "risk 3"],
  "execution_notes": (
      "2-3 sentences on how to size, how to use TP/SL, "
      "and when to re-check the market"
  )
}}

Requirements:
- headline: 1 sentence, punchy, mention model vs market if relevant
- thesis: 3-5 sentences tying together market context, news, and model edge
- bull_case: 2-4 short bullet points (as array of strings)
- bear_case: 2-4 short bullet points (as array of strings)
- key_risks: 2-4 short bullet points (as array of strings)
- execution_notes: 2-3 sentences on sizing, TP/SL usage, and when to re-check

Return ONLY the JSON object, no other text.
"""


def extract_prompt_data(
    market_snapshot: Dict[str, Any],
    signal: Dict[str, Any],
    decision: Dict[str, Any],
    news_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Extract data needed for prompt building from state dicts.

    Args:
        market_snapshot: Market snapshot dict
        signal: Signal dict
        decision: Decision dict
        news_context: News context dict (optional)

    Returns:
        Dict with all prompt parameters
    """
    # Extract from signal with fallbacks
    market_prob = (
        signal.get("market_prob")
        or signal.get("p_mkt")
        or signal.get("p_market")
        or signal.get("model_prob_abs")
        or market_snapshot.get("yes_price", 0)
        or 0.0
    )

    model_prob = (
        signal.get("model_prob")
        or signal.get("p_model")
        or signal.get("model_prob_abs")
        or market_prob
        or 0.0
    )

    edge_pct = decision.get("edge_pct") or signal.get("edge_pct")
    if edge_pct is None:
        edge_pct = abs(model_prob - market_prob)

    confidence = signal.get("confidence_level") or signal.get("confidence") or "low"

    # News context
    news_summary = ""
    sentiment_dist = ""
    if news_context:
        news_summary = news_context.get("summary", news_context.get("combined_summary", ""))
        articles = news_context.get("articles", [])
        if articles:
            bullish = sum(1 for a in articles if a.get("sentiment") == "bullish")
            bearish = sum(1 for a in articles if a.get("sentiment") == "bearish")
            neutral = sum(1 for a in articles if a.get("sentiment") == "neutral")
            total = len(articles)
            if total > 0:
                sentiment_dist = (
                    f"Bullish: {bullish} ({bullish / total * 100:.0f}%), "
                    f"Bearish: {bearish} ({bearish / total * 100:.0f}%), "
                    f"Neutral: {neutral} ({neutral / total * 100:.0f}%)"
                )

    return {
        "market_question": market_snapshot.get("question", "N/A"),
        "yes_price": market_snapshot.get("yes_price", 0),
        "market_prob": market_prob,
        "model_prob": model_prob,
        "edge_pct": edge_pct,
        "kelly": signal.get("kelly_fraction_yes", 0),
        "confidence": confidence,
        "confidence_score": signal.get("confidence_score", 0.5),
        "rationale": signal.get("rationale_short") or signal.get("rationale", ""),
        "action": decision.get("action", "HOLD"),
        "size": signal.get("recommended_size_fraction", 0),
        "tp": signal.get("target_take_profit_prob"),
        "sl": signal.get("target_stop_loss_prob"),
        "news_summary": news_summary,
        "sentiment_dist": sentiment_dist,
    }
