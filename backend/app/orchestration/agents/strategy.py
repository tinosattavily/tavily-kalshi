"""Strategy agent - thin wrapper calling AnalysisService."""

from __future__ import annotations

from app.config import get_logger
from app.domains.analysis import get_analysis_service
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_strategy_agent(state: AgentState) -> AgentState:
    """Evaluate the signal and compute decision using strategy parameters."""
    preset = state.get("strategy_preset") or "Balanced"
    horizon = state.get("horizon") or "24h"
    logger.debug("Running strategy agent", preset=preset)

    service = get_analysis_service(default_preset=preset)
    config = state.get("config", {}) or {}

    params = service.get_strategy_params(
        preset_name=preset,
        overrides=state.get("strategy_params") or {},
        config=config,
    )

    signal = service.normalize_signal(
        signal_data=state.get("signal"),
        market_snapshot=state.get("market_snapshot", {}) or {},
        news_context=state.get("news_context", {}) or {},
        horizon=horizon,
    )

    signal = service.apply_strategy(
        signal=signal,
        params=params,
        position_side=state.get("position_side", "flat"),
        position_size=state.get("position_size_fraction", 0.0),
    )

    decision = service.build_decision(signal)

    state["signal"] = signal
    state["decision"] = decision
    state["strategy_params"] = params
    state["strategy_preset"] = preset
    state["horizon"] = horizon

    return state
