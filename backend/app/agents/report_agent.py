"""Report agent - generates structured AI reports with fallback."""

from __future__ import annotations

import asyncio
import json
from textwrap import dedent
from typing import Any, Mapping

from pydantic import BaseModel

from app.agents.state import AgentState
from app.core.logging_config import get_logger
from app.services.openai_client import get_openai_client

logger = get_logger(__name__)

# Fields required in a valid report
REQUIRED_REPORT_FIELDS = [
    "headline",
    "thesis",
    "bull_case",
    "bear_case",
    "key_risks",
    "execution_notes",
]

# Fields that must be lists
LIST_FIELDS = ["bull_case", "bear_case", "key_risks"]

# Default environment metadata
DEFAULT_ENV_METADATA = {
    "app_version": "0.1.0",
    "model": "gpt-4o-mini",
    "tavily_version": "v1",
    "langgraph_graph_version": "market-v1",
}


def _signal_to_dict(signal: Any) -> dict[str, Any]:
    """Normalize Signal into a plain dict for downstream usage."""
    if isinstance(signal, BaseModel):
        return signal.model_dump()
    if isinstance(signal, Mapping):
        return dict(signal)
    return {}


def _get_first_of(d: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    """Return the first non-None value from a dict for the given keys."""
    for key in keys:
        value = d.get(key)
        if value is not None:
            return value
    return default


def _extract_signal_data(
    signal: dict[str, Any],
    decision: dict[str, Any],
    fallback_prob: float = 0.0,
) -> dict[str, Any]:
    """Extract and normalize signal data with fallbacks for different key names.

    Returns a dict with normalized keys: market_prob, model_prob, edge_pct,
    confidence, action, size, tp, sl, kelly, confidence_score, rationale.
    """
    s = _signal_to_dict(signal)

    market_prob = _get_first_of(
        s, ["market_prob", "p_mkt", "p_market", "model_prob_abs"], fallback_prob
    )
    model_prob = _get_first_of(
        s, ["model_prob", "p_model", "model_prob_abs"], market_prob
    )
    edge_pct = _get_first_of(
        {**s, **decision}, ["edge_pct"], abs(model_prob - market_prob)
    )

    return {
        "market_prob": market_prob,
        "model_prob": model_prob,
        "edge_pct": edge_pct,
        "confidence": _get_first_of(s, ["confidence_level", "confidence"], "low"),
        "action": decision.get("action", "HOLD"),
        "size": s.get("recommended_size_fraction", 0),
        "tp": s.get("target_take_profit_prob"),
        "sl": s.get("target_stop_loss_prob"),
        "kelly": s.get("kelly_fraction_yes", 0),
        "confidence_score": s.get("confidence_score", 0.5),
        "rationale": _get_first_of(s, ["rationale_short", "rationale"], ""),
    }


def _strip_code_block(content: str) -> str:
    """Remove markdown code blocks from content if present."""
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.split("\n")
    # Skip opening fence (line 0), end before closing fence if present
    has_closing_fence = lines[-1].strip().startswith("```")
    end_index = len(lines) - 1 if has_closing_fence else len(lines)
    return "\n".join(lines[1:end_index])


def _build_execution_notes(
    action: str, size: float, tp: float | None, sl: float | None
) -> str:
    """Build execution notes string with optional take-profit and stop-loss."""
    notes = f"Recommended {action} with {size:.1%} position size."
    if tp is not None:
        notes += f" Take profit at {tp:.1%}."
    if sl is not None:
        notes += f" Stop loss at {sl:.1%}."
    return notes


def _generate_fallback_report(
    market_snapshot: dict[str, Any],
    signal: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    """Generate a basic templated report when OpenAI fails."""
    data = _extract_signal_data(signal, decision)

    market_prob = data["market_prob"]
    model_prob = data["model_prob"]
    edge_pct = data["edge_pct"]
    confidence = data["confidence"]
    action = data["action"]
    size = data["size"]

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

    execution_notes = _build_execution_notes(action, size, data["tp"], data["sl"])

    question = market_snapshot.get("question", "N/A")
    yes_price = market_snapshot.get("yes_price", 0)
    liquidity = market_snapshot.get("liquidity", 0)
    rationale = decision.get("notes", "Strategy placeholder.")

    return {
        "headline": headline,
        "thesis": thesis,
        "bull_case": [
            f"Model sees {model_prob:.1%} probability vs market {market_prob:.1%}",
            f"Edge of {edge_pct:.2%} suggests market mispricing",
        ],
        "bear_case": [
            "Market may be correctly pricing the event",
            "Limited edge suggests cautious approach",
        ],
        "key_risks": [
            "Model uncertainty",
            "Market volatility",
        ],
        "execution_notes": execution_notes,
        "title": headline,
        "markdown": dedent(f"""
            ## TL;DR
            Action: **{action}** with edge ~{edge_pct:.2%}.

            ## Market snapshot
            - Question: {question}
            - Yes price: {yes_price:.2%}
            - Liquidity: {liquidity:,.0f} USDC

            ## Rationale
            {rationale}
        """).strip(),
    }


def _calculate_sentiment_distribution(articles: list[dict[str, Any]]) -> str:
    """Calculate sentiment distribution string from articles."""
    if not articles:
        return ""

    total = len(articles)
    bullish = sum(1 for a in articles if a.get("sentiment") == "bullish")
    bearish = sum(1 for a in articles if a.get("sentiment") == "bearish")
    neutral = sum(1 for a in articles if a.get("sentiment") == "neutral")

    return (
        f"Bullish: {bullish} ({bullish / total * 100:.0f}%), "
        f"Bearish: {bearish} ({bearish / total * 100:.0f}%), "
        f"Neutral: {neutral} ({neutral / total * 100:.0f}%)"
    )


def _format_prob(value: float | None) -> str:
    """Format a probability value for display, or return N/A placeholder."""
    if value is None:
        return "None (N/A)"
    return f"{value:.4f} ({value * 100:.2f}%)"


def _build_openai_messages(
    market_snapshot: dict[str, Any],
    signal: dict[str, Any],
    decision: dict[str, Any],
    news_context: dict[str, Any] | None,
) -> tuple[str, str]:
    """Build system and user messages for OpenAI report generation."""
    yes_price = market_snapshot.get("yes_price", 0)
    data = _extract_signal_data(signal, decision, fallback_prob=yes_price)

    market_question = market_snapshot.get("question", "N/A")
    market_prob = data["market_prob"]
    model_prob = data["model_prob"]
    edge_pct = data["edge_pct"]
    confidence = data["confidence"]
    kelly = data["kelly"]
    confidence_score = data["confidence_score"]
    action = data["action"]
    size = data["size"]
    rationale = data["rationale"] or "No rationale provided"

    # Format probability targets
    tp_str = _format_prob(data["tp"])
    sl_str = _format_prob(data["sl"])

    # Extract news context
    news_summary = ""
    sentiment_dist = ""
    if news_context:
        news_summary = _get_first_of(news_context, ["summary", "combined_summary"], "")
        sentiment_dist = _calculate_sentiment_distribution(
            news_context.get("articles", [])
        )

    news_section = f"Summary: {news_summary}" if news_summary else "No news summary available"
    if sentiment_dist:
        news_section += f"\nSentiment distribution: {sentiment_dist}"

    system_msg = (
        "You are writing a concise trade note for a prediction market. "
        "You will receive structured data about the market, model signal, "
        "news, and recommended action. "
        "Return ONLY a valid JSON object with the exact fields specified. "
        "Do not include any markdown formatting or code blocks."
    )

    user_msg = f"""
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
- Rationale: {rationale}

**Recommended Action:**
- Action: {action}
- Position size: {size:.4f} ({size * 100:.2f}%)
- Take profit: {tp_str}
- Stop loss: {sl_str}

**News Context:**
{news_section}

Return a JSON object with these exact fields:
{{
  "headline": "1 sentence, punchy, mention model vs market if relevant",
  "thesis": "3-5 sentences tying together market context, news, and model edge",
  "bull_case": ["bullet 1", "bullet 2", "bullet 3"],
  "bear_case": ["bullet 1", "bullet 2", "bullet 3"],
  "key_risks": ["risk 1", "risk 2", "risk 3"],
  "execution_notes": "2-3 sentences on how to size, how to use TP/SL, and when to re-check the market"
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

    return system_msg, user_msg


def _call_openai_sync(client: Any, system_msg: str, user_msg: str) -> str:
    """Synchronous OpenAI API call."""
    if not client.client:
        raise RuntimeError("OpenAI client not initialized")

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    if not client._use_new_api:
        # Legacy API path
        import openai

        if not openai.api_key:
            raise RuntimeError("OpenAI API key not configured")
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
        )
        return completion.choices[0].message["content"]

    # Modern API path - try with JSON response format first
    try:
        completion = client.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
    except (TypeError, AttributeError):
        # Fall back without response_format if not supported
        completion = client.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
        )
    return completion.choices[0].message.content


def _format_list_as_bullets(items: list[str]) -> str:
    """Format a list of strings as markdown bullet points."""
    return "\n".join(f"- {item}" for item in items)


def _format_report_markdown(report_data: dict[str, Any]) -> str:
    """Format report data as markdown."""
    bull_case = _format_list_as_bullets(report_data["bull_case"])
    bear_case = _format_list_as_bullets(report_data["bear_case"])
    key_risks = _format_list_as_bullets(report_data["key_risks"])

    return dedent(f"""
        ## TL;DR
        {report_data["headline"]}

        ## Thesis
        {report_data["thesis"]}

        ## Bull Case
        {bull_case}

        ## Bear Case
        {bear_case}

        ## Key Risks
        {key_risks}

        ## Execution Notes
        {report_data["execution_notes"]}
    """).strip()


async def _generate_report_with_openai(
    market_snapshot: dict[str, Any],
    signal: dict[str, Any],
    decision: dict[str, Any],
    news_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Generate structured report using OpenAI."""
    client = get_openai_client()

    if not client or not client.api_key:
        raise RuntimeError("OpenAI API key not configured")

    system_msg, user_msg = _build_openai_messages(
        market_snapshot, signal, decision, news_context
    )

    loop = asyncio.get_running_loop()
    raw_content = await loop.run_in_executor(
        None, _call_openai_sync, client, system_msg, user_msg
    )

    content = _strip_code_block(raw_content)
    report_data = json.loads(content)

    # Validate required fields
    for field in REQUIRED_REPORT_FIELDS:
        if field not in report_data:
            logger.warning(f"Missing field {field} in OpenAI response, using fallback")
            return _generate_fallback_report(market_snapshot, signal, decision)

    # Ensure arrays are lists
    for field in LIST_FIELDS:
        if not isinstance(report_data[field], list):
            report_data[field] = [str(report_data[field])]

    # Add legacy fields for backward compatibility
    report_data["title"] = report_data["headline"]
    report_data["markdown"] = _format_report_markdown(report_data)

    return report_data


async def run_report_agent(state: AgentState) -> AgentState:
    """Generate a structured AI report with fallback to template.

    This agent must run last as it needs the decision from strategy_agent.
    """
    logger.debug("Running report agent")

    decision = state.get("decision", {})
    market_snapshot = state.get("market_snapshot", {})
    signal = state.get("signal", {})
    news_context = state.get("news_context")

    try:
        report = await _generate_report_with_openai(
            market_snapshot, signal, decision, news_context
        )
        logger.debug("Report generated successfully with OpenAI")
    except Exception as exc:
        logger.warning(
            "Report generation failed, using fallback template",
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        report = _generate_fallback_report(market_snapshot, signal, decision)

    state["report"] = report
    state["env"] = state.get("env") or DEFAULT_ENV_METADATA

    return state
