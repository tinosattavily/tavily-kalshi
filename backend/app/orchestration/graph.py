"""Multi-agent analysis graph orchestration using LangGraph."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.config import get_logger
from app.orchestration.agents.article_fetcher import run_article_fetcher
from app.orchestration.agents.event import run_event_agent
from app.orchestration.agents.market import run_market_agent
from app.orchestration.agents.probability import run_probability_agent
from app.orchestration.agents.report import run_report_agent
from app.orchestration.agents.search_planner import run_search_planner
from app.orchestration.agents.strategy import run_strategy_agent
from app.orchestration.agents.summarizer import run_summarizer
from app.orchestration.state import AgentState

logger = get_logger(__name__)


# Node wrapper functions for LangGraph
async def market_agent_node(state: AgentState) -> AgentState:
    """Market agent node."""
    return await run_market_agent(state)


async def event_agent_node(state: AgentState) -> AgentState:
    """Event agent node."""
    return await run_event_agent(state)


async def tavily_prompt_agent_node(state: AgentState) -> AgentState:
    """Tavily prompt agent node (optional)."""
    config = state.get("config", {})
    if config.get("use_tavily_prompt_agent", True):
        return await run_search_planner(state)
    # Skip if disabled - just return state unchanged
    logger.debug("Tavily prompt agent skipped (disabled in configuration)")
    return state


async def news_agent_node(state: AgentState) -> AgentState:
    """News agent node."""
    logger.info("Executing news_agent node in LangGraph", run_id=state.get("run_id"))
    result = await run_article_fetcher(state)
    news_context = result.get("news_context")
    articles_count = (
        len(news_context.get("articles", [])) if news_context else 0
    )
    logger.info(
        "news_agent node completed",
        run_id=state.get("run_id"),
        has_news_context=bool(news_context),
        articles_count=articles_count,
    )
    return result


async def news_summary_agent_node(state: AgentState) -> AgentState:
    """News summary agent node (optional)."""
    config = state.get("config", {})
    if config.get("use_news_summary_agent", True):
        return await run_summarizer(state)
    # Skip if disabled - just return state unchanged
    logger.debug("News summary agent skipped (disabled in configuration)")
    return state


async def probability_agent_node(state: AgentState) -> AgentState:
    """Probability agent node."""
    return await run_probability_agent(state)


async def strategy_agent_node(state: AgentState) -> AgentState:
    """Strategy agent node."""
    return await run_strategy_agent(state)


async def report_agent_node(state: AgentState) -> AgentState:
    """Report agent node."""
    return await run_report_agent(state)


def route_after_market(state: AgentState) -> str:
    """Route after market agent: check if market selection is required.

    For multi-market events (Polymarket or Kalshi), the graph pauses to allow
    the user to select a specific market before continuing analysis.

    Returns:
        "end" if market selection is required, "event_agent" otherwise.
    """
    # Check if market selection is needed
    requires_selection = state.get("requires_market_selection", False)

    if requires_selection:
        selected_market_id = state.get("selected_market_id")
        selected_ticker = state.get("selected_ticker")
        selected_slug = state.get("selected_market_slug")

        # If selection is required but nothing selected, pause for user input
        if not selected_market_id and not selected_ticker and not selected_slug:
            logger.info(
                "Market selection required - pausing for user input",
                run_id=state.get("run_id"),
                available_markets=len(state.get("available_markets", []) or state.get("market_options", [])),
            )
            return "end"

    return "event_agent"


def build_analysis_graph() -> StateGraph:
    """Build the LangGraph StateGraph representing the agent workflow.

    Execution flow:
    1. market_agent (with conditional routing for market selection)
    2. event_agent
    3. tavily_prompt_agent (optional, can be skipped)
    4. news_agent
    5. news_summary_agent (optional, can be skipped)
    6. probability_agent
    7. strategy_agent
    8. report_agent

    Returns:
        Compiled StateGraph ready for execution.
    """
    # Create the graph builder
    builder = StateGraph(AgentState)

    # Add all agent nodes
    builder.add_node("market_agent", market_agent_node)
    builder.add_node("event_agent", event_agent_node)
    builder.add_node("tavily_prompt_agent", tavily_prompt_agent_node)
    builder.add_node("news_agent", news_agent_node)
    builder.add_node("news_summary_agent", news_summary_agent_node)
    builder.add_node("probability_agent", probability_agent_node)
    builder.add_node("strategy_agent", strategy_agent_node)
    builder.add_node("report_agent", report_agent_node)

    # Wire the graph: START → market_agent
    builder.add_edge(START, "market_agent")

    # Conditional edge: market_agent → (event_agent | END)
    # If requires_market_selection is True, stop and let UI handle selection
    builder.add_conditional_edges(
        "market_agent",
        route_after_market,
        {
            "event_agent": "event_agent",
            "end": END,
        },
    )

    # Linear chain from event_agent to report_agent
    builder.add_edge("event_agent", "tavily_prompt_agent")
    builder.add_edge("tavily_prompt_agent", "news_agent")
    builder.add_edge("news_agent", "news_summary_agent")
    builder.add_edge("news_summary_agent", "probability_agent")
    builder.add_edge("probability_agent", "strategy_agent")
    builder.add_edge("strategy_agent", "report_agent")
    builder.add_edge("report_agent", END)

    # Compile the graph
    return builder.compile()


# Global compiled graph instance (lazy-loaded)
_analysis_graph: StateGraph | None = None


def get_analysis_graph() -> StateGraph:
    """Get or create the compiled analysis graph."""
    global _analysis_graph
    if _analysis_graph is None:
        _analysis_graph = build_analysis_graph()
    return _analysis_graph


async def run_analysis_graph(initial_state: AgentState) -> AgentState:
    """Run the multi-agent analysis graph using LangGraph.

    This function maintains backward compatibility with the previous implementation.
    It initializes the state, runs the LangGraph, and returns the final state.

    Execution flow:
    1. market_agent (sequential - must run first)
    2. event_agent (sequential - depends on market_agent)
    3. tavily_prompt_agent (sequential - depends on event_agent, optional)
    4. news_agent (sequential - depends on tavily_prompt_agent)
    5. news_summary_agent (sequential - depends on news_agent, optional)
    6. prob_agent (sequential - depends on news_summary_agent)
    7. strategy_agent (sequential - depends on prob_agent)
    8. report_agent (sequential - depends on strategy_agent)

    Args:
        initial_state: Initial agent state dictionary.

    Returns:
        Final agent state after graph execution.
    """
    # Initialize state with defaults (same as before)
    run_id = f"run-{uuid4().hex}"
    state: AgentState = dict(initial_state)
    state.setdefault("run_id", run_id)
    state.setdefault(
        "run_at",
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    state.setdefault("market_url", state.get("polymarket_url", "https://polymarket.com"))

    logger.info("Starting analysis graph", run_id=run_id, market_url=state.get("market_url"))

    # Get the compiled graph and run it
    graph = get_analysis_graph()
    result_state = await graph.ainvoke(state)

    logger.info("Analysis graph completed", run_id=run_id)
    return result_state
