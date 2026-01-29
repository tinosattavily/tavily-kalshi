"""Multi-agent analysis graph orchestration using LangGraph."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.agents.event_agent import run_event_agent
from app.agents.market_agent import run_market_agent
from app.agents.news_agent import run_news_agent
from app.agents.news_summary_agent import run_news_summary_agent
from app.agents.prob_agent import run_prob_agent
from app.agents.report_agent import run_report_agent
from app.agents.state import AgentState
from app.agents.strategy_agent import run_strategy_agent
from app.agents.tavily_prompt_agent import run_tavily_prompt_agent
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def tavily_prompt_agent_node(state: AgentState) -> AgentState:
    """Execute tavily prompt agent if enabled in configuration."""
    config = state.get("config", {})
    if not config.get("use_tavily_prompt_agent", True):
        logger.debug("Tavily prompt agent skipped (disabled in configuration)")
        return state
    return await run_tavily_prompt_agent(state)


async def news_agent_node(state: AgentState) -> AgentState:
    """Execute news agent with logging for article collection."""
    run_id = state.get("run_id")
    logger.info("Executing news_agent node in LangGraph", run_id=run_id)

    result = await run_news_agent(state)

    news_context = result.get("news_context", {})
    articles = news_context.get("articles", []) if news_context else []
    logger.info(
        "news_agent node completed",
        run_id=run_id,
        has_news_context=bool(news_context),
        articles_count=len(articles),
    )
    return result


async def news_summary_agent_node(state: AgentState) -> AgentState:
    """Execute news summary agent if enabled in configuration."""
    config = state.get("config", {})
    if not config.get("use_news_summary_agent", True):
        logger.debug("News summary agent skipped (disabled in configuration)")
        return state
    return await run_news_summary_agent(state)


def route_after_market(state: AgentState) -> str:
    """Determine routing after market agent based on market selection state."""
    return "end" if state.get("requires_market_selection") else "event_agent"


def build_analysis_graph() -> StateGraph:
    """Build and compile the LangGraph StateGraph for the agent workflow.

    Execution flow:
    1. market_agent - Extract market data (may require user selection for multi-market events)
    2. event_agent - Build event context
    3. tavily_prompt_agent - Generate search queries (optional)
    4. news_agent - Fetch news articles
    5. news_summary_agent - Summarize news (optional)
    6. probability_agent - Calculate probability estimates
    7. strategy_agent - Determine trading strategy
    8. report_agent - Generate final report

    Returns:
        Compiled StateGraph ready for execution.
    """
    builder = StateGraph(AgentState)

    # Register agent nodes - simple pass-through wrappers use the agent function directly
    builder.add_node("market_agent", run_market_agent)
    builder.add_node("event_agent", run_event_agent)
    builder.add_node("tavily_prompt_agent", tavily_prompt_agent_node)
    builder.add_node("news_agent", news_agent_node)
    builder.add_node("news_summary_agent", news_summary_agent_node)
    builder.add_node("probability_agent", run_prob_agent)
    builder.add_node("strategy_agent", run_strategy_agent)
    builder.add_node("report_agent", run_report_agent)

    # Entry point
    builder.add_edge(START, "market_agent")

    # Conditional routing: stop for market selection or continue to event_agent
    builder.add_conditional_edges(
        "market_agent",
        route_after_market,
        {"event_agent": "event_agent", "end": END},
    )

    # Linear pipeline from event_agent through report_agent
    builder.add_edge("event_agent", "tavily_prompt_agent")
    builder.add_edge("tavily_prompt_agent", "news_agent")
    builder.add_edge("news_agent", "news_summary_agent")
    builder.add_edge("news_summary_agent", "probability_agent")
    builder.add_edge("probability_agent", "strategy_agent")
    builder.add_edge("strategy_agent", "report_agent")
    builder.add_edge("report_agent", END)

    return builder.compile()


_analysis_graph: StateGraph | None = None


def get_analysis_graph() -> StateGraph:
    """Get or create the compiled analysis graph (lazy-loaded singleton)."""
    global _analysis_graph
    if _analysis_graph is None:
        _analysis_graph = build_analysis_graph()
    return _analysis_graph


def reset_analysis_graph() -> None:
    """Reset the cached graph singleton. Used for testing to allow fresh graph compilation."""
    global _analysis_graph
    _analysis_graph = None


def _format_utc_timestamp() -> str:
    """Generate an ISO 8601 UTC timestamp without microseconds."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def run_analysis_graph(initial_state: AgentState) -> AgentState:
    """Run the multi-agent analysis graph and return the final state.

    Initializes state with defaults (run_id, run_at, market_url) and executes
    the full agent pipeline. See build_analysis_graph for execution flow details.

    Args:
        initial_state: Initial agent state dictionary.

    Returns:
        Final agent state after graph execution.
    """
    run_id = f"run-{uuid4().hex}"

    state: AgentState = dict(initial_state)
    state.setdefault("run_id", run_id)
    state.setdefault("run_at", _format_utc_timestamp())
    state.setdefault("market_url", state.get("polymarket_url", "https://polymarket.com"))

    logger.info("Starting analysis graph", run_id=run_id, market_url=state.get("market_url"))

    result_state = await get_analysis_graph().ainvoke(state)

    logger.info("Analysis graph completed", run_id=run_id)
    return result_state
