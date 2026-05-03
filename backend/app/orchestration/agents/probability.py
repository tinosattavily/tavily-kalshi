"""Probability agent - thin wrapper calling AnalysisService."""

from __future__ import annotations

from app.config import get_logger
from app.domains.analysis import get_analysis_service
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_probability_agent(state: AgentState) -> AgentState:
    """Generate trading signal from market and news context."""
    logger.debug("Running probability agent")
    snapshot = state.get("market_snapshot", {}) or {}
    event_ctx = state.get("event_context", {}) or {}
    news_ctx = state.get("news_context", {}) or {}
    horizon = state.get("horizon") or "24h"

    service = get_analysis_service()
    signal = await service.generate_signal(
        market_snapshot=snapshot,
        event_context=event_ctx,
        news_context=news_ctx,
        horizon=horizon,
    )

    state["signal"] = signal
    return state
