"""Market agent - thin wrapper calling the venue adapter registry."""

from __future__ import annotations

from app.config import get_logger
from app.domains.markets.adapters.registry import get_adapter_for_url
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_market_agent(state: AgentState) -> AgentState:
    """Execute market agent: fetch and build market snapshot."""
    market_url = state.get("market_url")
    if not market_url:
        raise ValueError("market_url is required")

    logger.debug("Running market agent", market_url=market_url)

    selected_market_id = (
        state.get("selected_market_id")
        or state.get("selected_market_slug")
        or state.get("selected_ticker")
    )
    adapter = get_adapter_for_url(market_url)
    result = await adapter.fetch(market_url, selected_market_id=selected_market_id)
    state.update(result)

    if result.get("requires_market_selection"):
        state["requires_market_selection"] = True
        return state

    state["requires_market_selection"] = False
    state["selected_market_id"] = result.get("selected_market_id") or result.get("market_id")

    if result.get("venue") == "polymarket":
        state["slug"] = result.get("market_id", state.get("slug", ""))
        state["selected_market_slug"] = state["selected_market_id"]
        state["polymarket_url"] = result.get("canonical_url") or market_url
    elif result.get("venue") == "kalshi":
        state["ticker"] = result.get("market_id", "")
        state["selected_ticker"] = state["selected_market_id"]
        state["event_ticker"] = result.get("event_id", "")
        state["kalshi_url"] = result.get("canonical_url") or market_url

    return state
