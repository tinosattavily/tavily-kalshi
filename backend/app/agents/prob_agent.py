"""Probability agent - generates trading signals using LLM."""

from __future__ import annotations

from typing import Any

from app.agents.state import AgentState
from app.core.logging_config import get_logger
from app.core.signal_utils import (
    clamp_prob,
    compute_edge_and_ev,
    estimate_confidence,
    infer_market_prob,
    kelly_fraction_no,
    kelly_fraction_yes,
)
from app.schemas.api import Signal
from app.services.openai_client import get_openai_client

logger = get_logger(__name__)

DEFAULT_RATIONALE = (
    "Improved macro backdrop and cautious commentary suggest a modest "
    "uptick relative to current market pricing."
)
DEFAULT_DELTA = 0.07


def _build_signal(
    p_mkt: float,
    p_model: float,
    horizon: str,
    confidence_level: str,
    confidence_score: float,
    rationale: str | None = None,
) -> Signal:
    """Build a Signal with computed edge, EV, and Kelly fractions."""
    edge, ev = compute_edge_and_ev(p_model, p_mkt)
    kelly_yes = kelly_fraction_yes(p_model, p_mkt)
    kelly_no = kelly_fraction_no(p_model, p_mkt)

    return Signal(
        market_prob=round(p_mkt, 4),
        model_prob=round(p_model, 4),
        edge_pct=round(edge, 4),
        expected_value_per_dollar=round(ev, 4),
        kelly_fraction_yes=round(kelly_yes, 4),
        kelly_fraction_no=round(kelly_no, 4),
        confidence_level=confidence_level,
        confidence_score=round(confidence_score, 4),
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon=horizon,
        rationale_short=rationale or DEFAULT_RATIONALE,
        rationale_long=None,
    )


def _fallback_signal(p_mkt: float, horizon: str, rationale: str | None = None) -> Signal:
    """Simple deterministic fallback if OpenAI isn't available."""
    p_model = clamp_prob(p_mkt + DEFAULT_DELTA)
    return _build_signal(
        p_mkt=p_mkt,
        p_model=p_model,
        horizon=horizon,
        confidence_level="medium",
        confidence_score=0.5,
        rationale=rationale,
    )


def _extract_top_headlines(articles: list[dict[str, Any]], count: int = 3) -> str:
    """Extract and join top headlines from articles list."""
    headlines = [
        a.get("title", "")
        for a in articles[:count]
        if isinstance(a, dict) and a.get("title")
    ]
    return "; ".join(headlines)


def _adjust_confidence_score(llm_confidence: str, heuristic_score: float) -> float:
    """Adjust confidence score based on LLM confidence level.

    Aligns the numeric score with the LLM's categorical confidence assessment.
    """
    if llm_confidence == "high" and heuristic_score < 0.7:
        return 0.75
    if llm_confidence == "low" and heuristic_score > 0.4:
        return 0.35
    if llm_confidence == "medium":
        return max(0.4, min(0.7, heuristic_score))
    return heuristic_score


async def run_prob_agent(state: AgentState) -> AgentState:
    """Signal generator that incorporates news + market context via LLM.

    This agent must run after news_agent since it needs news_context.
    Computes all signal quantities: p_mkt, p_model, edge, Kelly, EV, confidence.
    """
    logger.debug("Running probability agent")

    snapshot = state.get("market_snapshot") or {}
    event_ctx = state.get("event_context") or {}
    news_ctx = state.get("news_context") or {}
    horizon = state.get("horizon") or "24h"

    p_mkt = infer_market_prob(snapshot)
    articles = news_ctx.get("articles") or []

    llm_input = {
        "event_title": event_ctx.get("title") or "Key event",
        "market_question": snapshot.get("question") or "",
        "yes_price": p_mkt,
        "news_summary": news_ctx.get("summary") or "",
        "top_headlines": _extract_top_headlines(articles),
        "tag_label": snapshot.get("label") or snapshot.get("group_item_title") or "",
    }

    try:
        openai_client = get_openai_client()
        data = await openai_client.generate_signal(**llm_input)
    except Exception as exc:
        logger.warning("OpenAI call failed, using fallback", error=str(exc), exc_info=True)
        state["signal"] = _fallback_signal(p_mkt, horizon)
        return state

    try:
        p_model = clamp_prob(float(data.get("model_prob_abs", p_mkt)))
        conf_level, conf_score = estimate_confidence(news_ctx, p_model, p_mkt)

        llm_confidence = data.get("confidence")
        if llm_confidence in {"low", "medium", "high"}:
            conf_level = llm_confidence
            conf_score = _adjust_confidence_score(llm_confidence, conf_score)

        rationale = data.get("rationale") or (
            "Model-adjusted probability reflects recent news and macro context."
        )

        signal = _build_signal(
            p_mkt=p_mkt,
            p_model=p_model,
            horizon=horizon,
            confidence_level=conf_level,
            confidence_score=conf_score,
            rationale=rationale,
        )
        state["signal"] = signal

        logger.info(
            "signal_generated",
            market_slug=state.get("slug", "unknown"),
            p_mkt=signal.market_prob,
            p_model=signal.model_prob,
            edge=signal.edge_pct,
            kelly_yes=signal.kelly_fraction_yes,
            confidence_level=signal.confidence_level,
            confidence_score=signal.confidence_score,
        )
        return state

    except Exception as exc:  # pragma: no cover - parsing safeguard
        logger.warning("Error parsing model output, using fallback", error=str(exc), exc_info=True)
        state["signal"] = _fallback_signal(p_mkt, horizon)
        return state
