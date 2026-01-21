# app/domains/analysis/sizing.py
"""Position sizing calculations."""

from __future__ import annotations

from typing import Any, Dict, Literal, Tuple

from app.config import get_logger
from app.shared.types import StrategyParams

logger = get_logger(__name__)


def compute_target_fraction(
    kelly_yes: float,
    kelly_no: float,
    edge: float,
    params: StrategyParams,
) -> Tuple[float, Literal["long_yes", "long_no"]]:
    """Compute target position fraction from Kelly fractions.

    Args:
        kelly_yes: Kelly fraction for YES contract
        kelly_no: Kelly fraction for NO contract
        edge: Edge (p_model - p_mkt)
        params: Strategy parameters

    Returns:
        Tuple of (target_fraction, side)
    """
    # Determine which side to bet on
    if edge > 0:
        raw_fraction = max(0.0, kelly_yes)
        side: Literal["long_yes", "long_no"] = "long_yes"
    else:
        raw_fraction = max(0.0, kelly_no)
        side = "long_no"

    # Apply strategy limits
    kelly_cap = params.get("max_kelly_fraction", 0.25)
    max_capital = params.get("max_capital_pct", 0.15)

    target_fraction = min(raw_fraction * kelly_cap, max_capital)

    return target_fraction, side


def compute_position_delta(
    target_fraction: float,
    side: Literal["long_yes", "long_no"],
    current_side: str,
    current_size: float,
) -> Tuple[str, float]:
    """Compute position change needed.

    Args:
        target_fraction: Target position fraction
        side: Target side (long_yes or long_no)
        current_side: Current position side
        current_size: Current position size fraction

    Returns:
        Tuple of (action, size_change)
        Actions: buy_yes, buy_no, reduce_yes, reduce_no, hold
    """
    if current_side == side:
        # Already in same direction
        if target_fraction > current_size:
            action = "buy_yes" if side == "long_yes" else "buy_no"
            size_change = round(target_fraction - current_size, 4)
        elif target_fraction < current_size:
            action = "reduce_yes" if side == "long_yes" else "reduce_no"
            size_change = round(current_size - target_fraction, 4)
        else:
            action = "hold"
            size_change = 0.0
    elif current_side == "flat":
        # Flat position - enter if target > 0
        if target_fraction > 0:
            action = "buy_yes" if side == "long_yes" else "buy_no"
            size_change = round(target_fraction, 4)
        else:
            action = "hold"
            size_change = 0.0
    else:
        # Different direction - hold for now
        # Could implement position reversal logic later
        action = "hold"
        size_change = 0.0

    return action, size_change


def compute_targets(
    p_mkt: float,
    edge: float,
) -> Tuple[float | None, float | None]:
    """Compute take profit and stop loss targets.

    Args:
        p_mkt: Market probability
        edge: Edge (p_model - p_mkt)

    Returns:
        Tuple of (take_profit_prob, stop_loss_prob)
    """
    if edge > 0:
        # Long YES: take profit when market moves up
        take_profit = round(p_mkt + edge * 0.8, 4)
        stop_loss = round(p_mkt - edge * 0.5, 4)
    elif edge < 0:
        # Long NO: take profit when market moves down
        take_profit = round(p_mkt + edge * 0.8, 4)
        stop_loss = round(p_mkt - edge * 0.5, 4)
    else:
        take_profit = None
        stop_loss = None

    return take_profit, stop_loss
