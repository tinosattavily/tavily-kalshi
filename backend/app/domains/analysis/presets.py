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
