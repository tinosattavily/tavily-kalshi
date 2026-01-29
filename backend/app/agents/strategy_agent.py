"""Strategy agent - evaluates signals and makes trading decisions."""

from __future__ import annotations

from typing import Any

from app.agents.state import AgentState
from app.core.logging_config import get_logger
from app.core.signal_utils import (
    compute_edge_and_ev,
    estimate_confidence,
    infer_market_prob,
    kelly_fraction_no,
    kelly_fraction_yes,
)
from app.schemas.api import Signal

logger = get_logger(__name__)

CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}

PRESET_DEFAULTS: dict[str, dict[str, Any]] = {
    "conservative": {
        "min_edge_pct": 0.08,
        "min_confidence": "high",
        "max_capital_pct": 0.08,
        "max_kelly_fraction": 0.15,
        "risk_off": False,
    },
    "cautious": {
        "min_edge_pct": 0.08,
        "min_confidence": "high",
        "max_capital_pct": 0.08,
        "max_kelly_fraction": 0.15,
        "risk_off": False,
    },
    "aggressive": {
        "min_edge_pct": 0.03,
        "min_confidence": "low",
        "max_capital_pct": 0.25,
        "max_kelly_fraction": 0.5,
        "risk_off": False,
    },
    "balanced": {
        "min_edge_pct": 0.05,
        "min_confidence": "medium",
        "max_capital_pct": 0.15,
        "max_kelly_fraction": 0.25,
        "risk_off": False,
    },
}


def _preset_defaults(preset: str) -> dict[str, Any]:
    """Return default strategy parameters for a given risk preset."""
    normalized = (preset or "balanced").lower()
    return PRESET_DEFAULTS.get(normalized, PRESET_DEFAULTS["balanced"]).copy()


def _set_hold_action(signal: Signal) -> Signal:
    """Set signal to hold action with zero size."""
    signal.recommended_action = "hold"
    signal.recommended_size_fraction = 0.0
    return signal


def decide_action(signal: Signal, state: AgentState, params: dict[str, Any]) -> Signal:
    """Decide trading action based on signal, position, and strategy parameters.

    Args:
        signal: Signal model with probabilities and Kelly fractions
        state: Agent state with current position info
        params: Strategy parameters (min_edge_pct, min_confidence, max_capital_pct, etc.)

    Returns:
        Updated Signal model with recommended_action, recommended_size_fraction, and targets
    """
    p_mkt = signal.market_prob
    edge = signal.edge_pct

    pos_side = state.get("position_side", "flat")
    pos_size = state.get("position_size_fraction", 0.0)

    if params.get("risk_off", False):
        return _set_hold_action(signal)

    min_confidence_param = params.get("min_confidence", "medium")
    min_conf_order = CONFIDENCE_ORDER.get(min_confidence_param, 1)
    signal_conf_order = CONFIDENCE_ORDER.get(signal.confidence_level, 0)

    logger.debug(
        "Confidence check",
        signal_confidence=signal.confidence_level,
        signal_conf_order=signal_conf_order,
        min_confidence=min_confidence_param,
        min_conf_order=min_conf_order,
        will_hold=signal_conf_order < min_conf_order,
    )

    if signal_conf_order < min_conf_order:
        logger.info(
            "Signal confidence below minimum threshold - holding",
            signal_confidence=signal.confidence_level,
            min_confidence=min_confidence_param,
            signal_conf_order=signal_conf_order,
            min_conf_order=min_conf_order,
        )
        return _set_hold_action(signal)

    if abs(edge) < params.get("min_edge_pct", 0.05):
        return _set_hold_action(signal)

    is_long_yes = edge > 0
    side = "long_yes" if is_long_yes else "long_no"
    kelly_fraction = signal.kelly_fraction_yes if is_long_yes else signal.kelly_fraction_no
    raw_fraction = max(0.0, kelly_fraction)

    kelly_cap = params.get("max_kelly_fraction", 0.25)
    max_capital = params.get("max_capital_pct", 0.15)
    target_fraction = min(raw_fraction * kelly_cap, max_capital)

    _compute_position_action(signal, side, target_fraction, pos_side, pos_size)
    _set_target_prices(signal, p_mkt, edge)

    return signal


def _compute_position_action(
    signal: Signal,
    side: str,
    target_fraction: float,
    pos_side: str,
    pos_size: float,
) -> None:
    """Compute recommended action and size based on current position."""
    is_yes = side == "long_yes"
    buy_action = "buy_yes" if is_yes else "buy_no"
    reduce_action = "reduce_yes" if is_yes else "reduce_no"

    if pos_side == side:
        if target_fraction > pos_size:
            signal.recommended_action = buy_action
            signal.recommended_size_fraction = round(target_fraction - pos_size, 4)
        elif target_fraction < pos_size:
            signal.recommended_action = reduce_action
            signal.recommended_size_fraction = round(pos_size - target_fraction, 4)
        else:
            _set_hold_action(signal)
    elif pos_side == "flat" and target_fraction > 0:
        signal.recommended_action = buy_action
        signal.recommended_size_fraction = round(target_fraction, 4)
    else:
        _set_hold_action(signal)


def _set_target_prices(signal: Signal, p_mkt: float, edge: float) -> None:
    """Set take profit and stop loss target prices based on edge."""
    if edge == 0:
        signal.target_take_profit_prob = None
        signal.target_stop_loss_prob = None
        return

    signal.target_take_profit_prob = round(p_mkt + edge * 0.8, 4)
    signal.target_stop_loss_prob = round(p_mkt - edge * 0.5, 4)


def _create_fallback_signal(p_mkt: float, horizon: str, rationale: str) -> Signal:
    """Create a minimal fallback signal with default values."""
    return Signal(
        market_prob=p_mkt,
        model_prob=p_mkt,
        edge_pct=0.0,
        expected_value_per_dollar=0.0,
        kelly_fraction_yes=0.0,
        kelly_fraction_no=0.0,
        confidence_level="low",
        confidence_score=0.0,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon=horizon,
        rationale_short=rationale,
        rationale_long=None,
    )


def _convert_dict_to_signal(
    signal_dict: dict[str, Any],
    state: AgentState,
    horizon: str,
) -> Signal:
    """Convert legacy dict signal format to Signal model."""
    p_mkt = signal_dict.get("market_prob") or signal_dict.get("yes_price", 0.5)
    p_model = signal_dict.get("model_prob_abs") or signal_dict.get("model_prob", 0.0)

    if isinstance(p_model, float) and abs(p_model) < 1.0:
        p_model = p_mkt + p_model
    p_model = max(0.0, min(1.0, p_model))

    edge, ev = compute_edge_and_ev(p_model, p_mkt)
    kelly_yes = kelly_fraction_yes(p_model, p_mkt)
    kelly_no = kelly_fraction_no(p_model, p_mkt)

    news_ctx = state.get("news_context", {}) or {}
    conf_level, conf_score = estimate_confidence(news_ctx, p_model, p_mkt)

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


def _resolve_signal(state: AgentState, horizon: str) -> Signal:
    """Resolve signal from state, handling various input types."""
    signal_raw = state.get("signal")
    snapshot = state.get("market_snapshot", {}) or {}

    if signal_raw is None:
        logger.warning("No signal found in state, creating empty signal")
        p_mkt = infer_market_prob(snapshot)
        return _create_fallback_signal(p_mkt, horizon, "No signal available")

    if isinstance(signal_raw, Signal):
        return signal_raw

    if isinstance(signal_raw, dict):
        try:
            return _convert_dict_to_signal(signal_raw, state, horizon)
        except Exception as exc:
            logger.warning(
                "Error converting dict signal to Signal model",
                error=str(exc),
                exc_info=True,
            )
            p_mkt = infer_market_prob(snapshot)
            return _create_fallback_signal(p_mkt, horizon, "Signal conversion failed")

    logger.warning("Unexpected signal type", signal_type=type(signal_raw).__name__)
    p_mkt = infer_market_prob(snapshot)
    return _create_fallback_signal(p_mkt, horizon, "Invalid signal type")


def _build_strategy_params(state: AgentState, preset: str) -> dict[str, Any]:
    """Build strategy parameters from preset, config, and user overrides.

    Priority: user_overrides (explicit strategy_params) > config > preset defaults
    """
    preset_base = _preset_defaults(preset)
    user_overrides = state.get("strategy_params", {}) or {}
    config = state.get("config", {}) or {}

    if "min_confidence" in config and "min_confidence" not in user_overrides:
        user_overrides = {**user_overrides, "min_confidence": config["min_confidence"]}
        logger.debug(
            "Applied min_confidence from config",
            min_confidence=config["min_confidence"],
            preset=preset,
        )
    elif "min_confidence" in user_overrides:
        logger.debug(
            "Using min_confidence from strategy_params (overrides config)",
            min_confidence=user_overrides["min_confidence"],
            config_min_confidence=config.get("min_confidence"),
        )

    return {**preset_base, **user_overrides}


def _build_legacy_decision(signal: Signal) -> dict[str, Any]:
    """Build legacy decision dict for backward compatibility."""
    action_map = {
        "buy_yes": "BUY",
        "buy_no": "BUY",
        "reduce_yes": "SELL",
        "reduce_no": "SELL",
        "hold": "HOLD",
    }

    notes = (
        f"Action: {signal.recommended_action}, size: {signal.recommended_size_fraction:.4f}. "
        f"Edge: {signal.edge_pct:.4f}, confidence: {signal.confidence_level}."
    )

    return {
        "action": action_map.get(signal.recommended_action, "HOLD"),
        "side": "YES" if "yes" in signal.recommended_action else "NO",
        "edge_pct": round(signal.edge_pct, 4),
        "toy_kelly_fraction": round(signal.recommended_size_fraction, 4),
        "notes": notes,
    }


async def run_strategy_agent(state: AgentState) -> AgentState:
    """Evaluate the model signal and turn it into a concrete decision.

    This agent must run after prob_agent since it needs the signal.
    Uses decide_action to compute recommendations and update the signal.
    """
    preset = state.get("strategy_preset") or "Balanced"
    horizon = state.get("horizon") or "24h"
    logger.debug("Running strategy agent", preset=preset)

    params = _build_strategy_params(state, preset)
    state["strategy_preset"] = preset
    state["horizon"] = horizon
    state["strategy_params"] = params

    signal = _resolve_signal(state, horizon)
    signal = decide_action(signal, state, params)

    state["signal"] = signal
    state["decision"] = _build_legacy_decision(signal)

    logger.info(
        "signal_decision",
        market_slug=state.get("slug", "unknown"),
        recommended_action=signal.recommended_action,
        recommended_size_fraction=round(signal.recommended_size_fraction, 4),
        edge=round(signal.edge_pct, 4),
        confidence_level=signal.confidence_level,
    )

    return state
