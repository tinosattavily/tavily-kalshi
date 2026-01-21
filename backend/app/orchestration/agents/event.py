"""Event agent - thin wrapper calling EventService."""

from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_logger
from app.domains.markets.event_service import get_event_service
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_event_agent(state: AgentState) -> AgentState:
    """Normalize event metadata and provide event context."""
    market_slug = state.get("slug")
    logger.debug("Running event agent", market_slug=market_slug)

    event_service = get_event_service()
    event_data = state.get("event", {}) or {}
    timestamp = state.get("run_at") or datetime.now(timezone.utc).isoformat()
    url = state.get("polymarket_url") or state.get("market_url")

    normalized_event, event_context, description = event_service.normalize_event(
        event=event_data,
        market_slug=market_slug,
        url=url,
        timestamp=timestamp,
    )

    state["event"] = normalized_event
    state["event_context"] = event_context
    state["event_description"] = description

    return state
