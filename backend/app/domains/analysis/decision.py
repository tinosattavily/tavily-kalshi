# app/domains/analysis/decision.py
"""Trading decision logic."""

from __future__ import annotations

from typing import Any, Dict

from app.config import get_logger
from app.domains.analysis.schemas import Signal
from app.domains.analysis.sizing import (
    compute_position_delta,
    compute_target_fraction,
    compute_targets,
)
from app.shared.types import StrategyParams

logger = get_logger(__name__)

CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}


def check_risk_off(params: StrategyParams) -> bool:
    """Check if risk_off flag is set.

    Args:
        params: Strategy parameters

    Returns:
        True if risk_off is enabled
    """
    return params.get("risk_off", False)


def check_confidence_threshold(
    signal_confidence: str,
    min_confidence: str,
) -> bool:
    """Check if signal confidence meets minimum threshold.

    Args:
        signal_confidence: Signal's confidence level
        min_confidence: Minimum required confidence

    Returns:
        True if confidence is sufficient
    """
    signal_order = CONFIDENCE_ORDER.get(signal_confidence, 0)
    min_order = CONFIDENCE_ORDER.get(min_confidence, 1)

    logger.debug(
        "Confidence check",
        signal_confidence=signal_confidence,
        signal_order=signal_order,
        min_confidence=min_confidence,
        min_order=min_order,
        passes=signal_order >= min_order,
    )

    return signal_order >= min_order


def check_edge_threshold(edge: float, min_edge: float) -> bool:
    """Check if edge meets minimum threshold.

    Args:
        edge: Signal edge (absolute value will be compared)
        min_edge: Minimum required edge

    Returns:
        True if edge is sufficient
    """
    return abs(edge) >= min_edge


def decide_action(
    signal: Signal,
    position_side: str = "flat",
    position_size: float = 0.0,
    params: StrategyParams | None = None,
) -> Signal:
    """Decide trading action based on signal and strategy parameters.

    Args:
        signal: Signal model with probabilities and Kelly fractions
        position_side: Current position side (flat, long_yes, long_no)
        position_size: Current position size fraction
        params: Strategy parameters

    Returns:
        Updated Signal model with action and targets
    """
    params = params or {}

    # 1) Check risk_off flag
    if check_risk_off(params):
        signal.recommended_action = "hold"
        signal.recommended_size_fraction = 0.0
        return signal

    # 2) Check confidence threshold
    min_confidence = params.get("min_confidence", "medium")
    if not check_confidence_threshold(signal.confidence_level, min_confidence):
        logger.info(
            "Signal confidence below minimum threshold - holding",
            signal_confidence=signal.confidence_level,
            min_confidence=min_confidence,
        )
        signal.recommended_action = "hold"
        signal.recommended_size_fraction = 0.0
        return signal

    # 3) Check edge threshold
    min_edge = params.get("min_edge_pct", 0.05)
    if not check_edge_threshold(signal.edge_pct, min_edge):
        signal.recommended_action = "hold"
        signal.recommended_size_fraction = 0.0
        return signal

    # 4) Compute target position
    target_fraction, side = compute_target_fraction(
        kelly_yes=signal.kelly_fraction_yes,
        kelly_no=signal.kelly_fraction_no,
        edge=signal.edge_pct,
        params=params,
    )

    # 5) Compute position delta
    action, size_change = compute_position_delta(
        target_fraction=target_fraction,
        side=side,
        current_side=position_side,
        current_size=position_size,
    )

    signal.recommended_action = action
    signal.recommended_size_fraction = size_change

    # 6) Set targets
    take_profit, stop_loss = compute_targets(
        p_mkt=signal.market_prob,
        edge=signal.edge_pct,
    )
    signal.target_take_profit_prob = take_profit
    signal.target_stop_loss_prob = stop_loss

    return signal


def build_decision_dict(signal: Signal) -> Dict[str, Any]:
    """Build legacy decision dict from Signal.

    Args:
        signal: Signal model

    Returns:
        Decision dict for backward compatibility
    """
    action_map = {
        "buy_yes": "BUY",
        "buy_no": "BUY",
        "reduce_yes": "SELL",
        "reduce_no": "SELL",
        "hold": "HOLD",
    }
    action = action_map.get(signal.recommended_action, "HOLD")

    notes = (
        f"Action: {signal.recommended_action}, size: {signal.recommended_size_fraction:.4f}. "
        f"Edge: {signal.edge_pct:.4f}, confidence: {signal.confidence_level}."
    )

    return {
        "action": action,
        "side": "YES" if "yes" in signal.recommended_action else "NO",
        "edge_pct": round(signal.edge_pct, 4),
        "toy_kelly_fraction": round(signal.recommended_size_fraction, 4),
        "notes": notes,
    }
