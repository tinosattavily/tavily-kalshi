# app/domains/analysis/__init__.py
"""Analysis domain exports."""

from app.domains.analysis.calculations import (
    clamp_prob,
    compute_edge_and_ev,
    estimate_confidence,
    infer_market_prob,
    kelly_fraction_no,
    kelly_fraction_yes,
)
from app.domains.analysis.decision import (
    CONFIDENCE_ORDER,
    build_decision_dict,
    check_confidence_threshold,
    check_edge_threshold,
    check_risk_off,
    decide_action,
)
from app.domains.analysis.presets import (
    AGGRESSIVE,
    BALANCED,
    CAUTIOUS,
    PRESETS,
    get_preset,
    get_preset_with_overrides,
)
from app.domains.analysis.probability import (
    create_fallback_signal,
    create_signal_from_dict,
    generate_signal,
)
from app.domains.analysis.schemas import (
    AnalysisConfiguration,
    Signal,
    StrategyParamsModel,
)
from app.domains.analysis.service import AnalysisService, get_analysis_service
from app.domains.analysis.sizing import (
    compute_position_delta,
    compute_target_fraction,
    compute_targets,
)

__all__ = [
    # Schemas
    "AnalysisConfiguration",
    "Signal",
    "StrategyParamsModel",
    # Calculations
    "clamp_prob",
    "compute_edge_and_ev",
    "estimate_confidence",
    "infer_market_prob",
    "kelly_fraction_no",
    "kelly_fraction_yes",
    # Presets
    "AGGRESSIVE",
    "BALANCED",
    "CAUTIOUS",
    "PRESETS",
    "get_preset",
    "get_preset_with_overrides",
    # Sizing
    "compute_position_delta",
    "compute_target_fraction",
    "compute_targets",
    # Decision
    "CONFIDENCE_ORDER",
    "build_decision_dict",
    "check_confidence_threshold",
    "check_edge_threshold",
    "check_risk_off",
    "decide_action",
    # Probability
    "create_fallback_signal",
    "create_signal_from_dict",
    "generate_signal",
    # Service
    "AnalysisService",
    "get_analysis_service",
]
