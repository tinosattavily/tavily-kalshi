# app/domains/analysis/presets.py
"""Strategy preset configurations."""

from __future__ import annotations

from typing import Any, Dict

from app.shared.types import StrategyParams

CAUTIOUS: StrategyParams = {
    "min_edge_pct": 0.08,
    "min_confidence": "high",
    "max_capital_pct": 0.08,
    "max_kelly_fraction": 0.15,
    "risk_off": False,
}

BALANCED: StrategyParams = {
    "min_edge_pct": 0.05,
    "min_confidence": "medium",
    "max_capital_pct": 0.15,
    "max_kelly_fraction": 0.25,
    "risk_off": False,
}

AGGRESSIVE: StrategyParams = {
    "min_edge_pct": 0.03,
    "min_confidence": "low",
    "max_capital_pct": 0.25,
    "max_kelly_fraction": 0.5,
    "risk_off": False,
}

PRESETS: Dict[str, StrategyParams] = {
    "Cautious": CAUTIOUS,
    "Conservative": CAUTIOUS,  # Alias
    "Balanced": BALANCED,
    "Aggressive": AGGRESSIVE,
}


def get_preset(name: str) -> StrategyParams:
    """Get strategy preset by name.

    Args:
        name: Preset name (Cautious, Conservative, Balanced, Aggressive)

    Returns:
        Strategy parameters dict
    """
    # Normalize name
    normalized = (name or "Balanced").lower()

    if normalized in ("conservative", "cautious"):
        return CAUTIOUS.copy()
    if normalized == "aggressive":
        return AGGRESSIVE.copy()

    return BALANCED.copy()


def get_preset_with_overrides(
    preset_name: str,
    overrides: Dict[str, Any] | None = None,
) -> StrategyParams:
    """Get strategy preset with optional parameter overrides.

    Args:
        preset_name: Base preset name
        overrides: Optional dict of parameter overrides

    Returns:
        Merged strategy parameters
    """
    base = get_preset(preset_name)
    if overrides:
        return {**base, **overrides}
    return base


# =============================================================================
# Cents-based presets (for Kalshi integration)
# All edge thresholds in cents (1-99)
# =============================================================================

class StrategyPresetCents:
    """Strategy preset with cents-based thresholds."""

    def __init__(
        self,
        min_edge: int,
        min_confidence: str,
        max_position_pct: int,
        kelly_fraction: int,
    ):
        self.min_edge = min_edge  # Minimum edge in cents to act
        self.min_confidence = min_confidence  # "low", "medium", "high"
        self.max_position_pct = max_position_pct  # Max % of bankroll per position
        self.kelly_fraction = kelly_fraction  # Use this % of full Kelly


CAUTIOUS_CENTS = StrategyPresetCents(
    min_edge=8,  # 8 cents = 8%
    min_confidence="high",
    max_position_pct=8,
    kelly_fraction=15,  # Use 15% of Kelly
)

BALANCED_CENTS = StrategyPresetCents(
    min_edge=5,  # 5 cents = 5%
    min_confidence="medium",
    max_position_pct=15,
    kelly_fraction=25,  # Use 25% of Kelly
)

AGGRESSIVE_CENTS = StrategyPresetCents(
    min_edge=3,  # 3 cents = 3%
    min_confidence="low",
    max_position_pct=25,
    kelly_fraction=50,  # Use 50% of Kelly
)

PRESETS_CENTS: Dict[str, StrategyPresetCents] = {
    "Cautious": CAUTIOUS_CENTS,
    "Conservative": CAUTIOUS_CENTS,
    "Balanced": BALANCED_CENTS,
    "Aggressive": AGGRESSIVE_CENTS,
}


def get_preset_cents(name: str) -> StrategyPresetCents:
    """Get cents-based strategy preset by name.

    Args:
        name: Preset name (Cautious, Conservative, Balanced, Aggressive)

    Returns:
        Strategy preset with cents-based thresholds
    """
    normalized = (name or "Balanced").lower()

    if normalized in ("conservative", "cautious"):
        return CAUTIOUS_CENTS
    if normalized == "aggressive":
        return AGGRESSIVE_CENTS

    return BALANCED_CENTS
