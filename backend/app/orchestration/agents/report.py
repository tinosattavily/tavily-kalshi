"""Report agent - thin wrapper calling ReportService."""

from __future__ import annotations

from app.config import get_logger
from app.domains.reports import get_report_service
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_report_agent(state: AgentState) -> AgentState:
    """Generate a structured report with fallback."""
    logger.debug("Running report agent")

    service = get_report_service()
    decision = state.get("decision", {}) or {}
    market_snapshot = state.get("market_snapshot", {}) or {}
    event_context = state.get("event_context", {}) or {}
    signal = state.get("signal", {}) or {}
    news_context = state.get("news_context")

    report = await service.generate_report(
        market_snapshot=market_snapshot,
        signal=signal,
        decision=decision,
        event_context=event_context,
        news_context=news_context,
    )

    state["report"] = report
    state["env"] = service.get_env()
    return state
