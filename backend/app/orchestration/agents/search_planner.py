"""Search planner agent - thin wrapper around query generation."""

from __future__ import annotations

from app.config import get_logger
from app.domains.news.query_generator import generate_search_queries
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_search_planner(state: AgentState) -> AgentState:
    """Generate Tavily query specifications using LLM when enabled."""
    if state.get("tavily_queries"):
        logger.debug("tavily_queries already present, skipping generation")
        return state

    market_snapshot = state.get("market_snapshot", {}) or {}
    event_context = state.get("event_context", {}) or {}
    event_data = state.get("event", {}) or {}
    horizon = state.get("horizon") or "24h"
    strategy_preset = state.get("strategy_preset") or "Balanced"
    slug = state.get("slug") or "unknown"

    tavily_queries = await generate_search_queries(
        market_snapshot=market_snapshot,
        event_context=event_context,
        event_data=event_data,
        horizon=horizon,
        strategy_preset=strategy_preset,
        slug=slug,
    )

    if not tavily_queries:
        logger.warning(
            "LLM generated no valid queries, article_fetcher will use fallback",
            market_slug=slug,
            horizon=horizon,
        )
        return state

    state["tavily_queries"] = tavily_queries
    logger.info(
        "tavily_queries_generated",
        market_slug=slug,
        horizon=horizon,
        num_queries=len(tavily_queries),
    )

    return state
