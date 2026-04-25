# app/domains/analysis/probability.py
"""Probability estimation and signal generation."""

from __future__ import annotations

from typing import Any, Dict

from app.config import get_logger
from app.domains.analysis.calculations import (
    clamp_prob,
    compute_edge_and_ev,
    estimate_confidence,
    infer_market_prob,
    kelly_fraction_no,
    kelly_fraction_yes,
)
from app.domains.analysis.schemas import Signal
from app.infrastructure.llm import get_openai_client

logger = get_logger(__name__)


def create_fallback_signal(
    p_mkt: float,
    horizon: str,
    rationale: str | None = None,
) -> Signal:
    """Create a simple deterministic fallback signal.

    Args:
        p_mkt: Market probability
        horizon: Analysis horizon
        rationale: Optional rationale string

    Returns:
        Fallback Signal model
    """
    default_delta = 0.03
    p_model = clamp_prob(p_mkt + default_delta)
    edge, ev = compute_edge_and_ev(p_model, p_mkt)
    kelly_yes = kelly_fraction_yes(p_model, p_mkt)
    kelly_no = kelly_fraction_no(p_model, p_mkt)

    default_rationale = (
        "Improved macro backdrop and cautious commentary suggest a modest "
        "uptick relative to current market pricing."
    )
    rationale_short = rationale if rationale is not None else default_rationale

    return Signal(
        market_prob=p_mkt,
        model_prob=p_model,
        edge_pct=edge,
        expected_value_per_dollar=ev,
        kelly_fraction_yes=kelly_yes,
        kelly_fraction_no=kelly_no,
        confidence_level="medium",
        confidence_score=0.5,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon=horizon,
        rationale_short=rationale_short,
        rationale_long=None,
    )


async def generate_signal(
    market_snapshot: Dict[str, Any],
    event_context: Dict[str, Any],
    news_context: Dict[str, Any],
    horizon: str = "24h",
) -> Signal:
    """Generate trading signal using LLM with news and market context.

    Args:
        market_snapshot: Market data dict
        event_context: Event context dict
        news_context: News context dict
        horizon: Analysis horizon

    Returns:
        Signal model with probabilities and Kelly fractions
    """
    # Infer market probability from snapshot
    p_mkt = infer_market_prob(market_snapshot)

    event_title = event_context.get("title") or "Key event"
    market_question = market_snapshot.get("question") or ""
    tag_label = market_snapshot.get("label") or market_snapshot.get("group_item_title") or ""
    news_summary = news_context.get("summary") or ""
    articles = news_context.get("articles") or []

    top_headlines = "; ".join(
        a.get("title", "") for a in articles[:3] if isinstance(a, dict) and a.get("title")
    )

    # Try LLM signal generation
    try:
        openai_client = get_openai_client()
        data = await openai_client.generate_signal(
            event_title=event_title,
            market_question=market_question,
            yes_price=p_mkt,
            news_summary=news_summary,
            top_headlines=top_headlines,
            tag_label=tag_label,
            venue=market_snapshot.get("venue", "polymarket"),
            market_id=market_snapshot.get("market_id") or market_snapshot.get("slug") or "unknown",
        )
    except RuntimeError:
        logger.warning("OpenAI not available, using fallback signal")
        return create_fallback_signal(p_mkt, horizon)
    except Exception as exc:
        logger.warning("OpenAI call failed, using fallback", error=str(exc), exc_info=True)
        return create_fallback_signal(p_mkt, horizon)

    # Parse LLM response
    try:
        p_model_raw = float(data.get("model_prob_abs", p_mkt))
        p_model = clamp_prob(p_model_raw)

        edge, ev = compute_edge_and_ev(p_model, p_mkt)
        kelly_yes = kelly_fraction_yes(p_model, p_mkt)
        kelly_no = kelly_fraction_no(p_model, p_mkt)

        # Estimate confidence
        conf_level, conf_score = estimate_confidence(news_context, p_model, p_mkt)

        # Override with LLM confidence if available
        llm_confidence = data.get("confidence")
        if llm_confidence in {"low", "medium", "high"}:
            conf_level = llm_confidence
            if llm_confidence == "high" and conf_score < 0.7:
                conf_score = 0.75
            elif llm_confidence == "low" and conf_score > 0.4:
                conf_score = 0.35
            elif llm_confidence == "medium":
                conf_score = max(0.4, min(0.7, conf_score))

        rationale = data.get("rationale") or (
            "Model-adjusted probability reflects recent news and macro context."
        )

        signal = Signal(
            market_prob=round(p_mkt, 4),
            model_prob=round(p_model, 4),
            edge_pct=round(edge, 4),
            expected_value_per_dollar=round(ev, 4),
            kelly_fraction_yes=round(kelly_yes, 4),
            kelly_fraction_no=round(kelly_no, 4),
            confidence_level=conf_level,
            confidence_score=round(conf_score, 4),
            recommended_action="hold",
            recommended_size_fraction=0.0,
            target_take_profit_prob=None,
            target_stop_loss_prob=None,
            horizon=horizon,
            rationale_short=rationale,
            rationale_long=None,
        )

        logger.info(
            "signal_generated",
            p_mkt=round(p_mkt, 4),
            p_model=round(p_model, 4),
            edge=round(edge, 4),
            kelly_yes=round(kelly_yes, 4),
            confidence_level=conf_level,
            confidence_score=round(conf_score, 4),
        )
        return signal

    except Exception as exc:
        logger.warning("Error parsing model output, using fallback", error=str(exc), exc_info=True)
        return create_fallback_signal(p_mkt, horizon)


def create_signal_from_dict(
    signal_dict: Dict[str, Any],
    market_snapshot: Dict[str, Any],
    news_context: Dict[str, Any],
    horizon: str = "24h",
) -> Signal:
    """Create Signal model from legacy dict format.

    Args:
        signal_dict: Legacy signal dict
        market_snapshot: Market snapshot for fallback
        news_context: News context for confidence
        horizon: Analysis horizon

    Returns:
        Signal model
    """
    try:
        p_mkt = signal_dict.get("market_prob") or signal_dict.get("yes_price", 0.5)
        p_model = signal_dict.get("model_prob_abs") or signal_dict.get("model_prob", 0.0)

        if isinstance(p_model, float) and abs(p_model) < 1.0:
            p_model = p_mkt + p_model
        p_model = clamp_prob(p_model)

        edge, ev = compute_edge_and_ev(p_model, p_mkt)
        kelly_yes = kelly_fraction_yes(p_model, p_mkt)
        kelly_no = kelly_fraction_no(p_model, p_mkt)

        conf_level, conf_score = estimate_confidence(news_context, p_model, p_mkt)

        return Signal(
            market_prob=round(p_mkt, 4),
            model_prob=round(p_model, 4),
            edge_pct=round(edge, 4),
            expected_value_per_dollar=round(ev, 4),
            kelly_fraction_yes=round(kelly_yes, 4),
            kelly_fraction_no=round(kelly_no, 4),
            confidence_level=signal_dict.get("confidence", conf_level),
            confidence_score=conf_score,
            recommended_action="hold",
            recommended_size_fraction=0.0,
            target_take_profit_prob=None,
            target_stop_loss_prob=None,
            horizon=horizon,
            rationale_short=signal_dict.get("rationale", ""),
            rationale_long=None,
        )
    except Exception as exc:
        logger.warning("Error converting signal dict", error=str(exc), exc_info=True)
        p_mkt = infer_market_prob(market_snapshot)
        return create_fallback_signal(p_mkt, horizon, "Signal conversion failed")
