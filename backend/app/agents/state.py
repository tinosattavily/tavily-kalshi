"""Agent state definitions for LangGraph workflow."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from app.db.models import (
    Decision,
    EventContext,
    EventDocument,
    Horizon,
    MarketDocument,
    MarketSnapshot,
    NewsContext,
    ReportBlock,
    RunEnvMetadata,
    Signal,
    StrategyParams,
    StrategyPreset,
)


class TavilyQuerySpec(TypedDict, total=False):
    """Structured specification for a single Tavily query."""

    name: str
    query: str
    max_results: int
    search_depth: Literal["basic", "advanced"]
    timeframe: str  # e.g. "24h", "7d", "30d"
    notes: str


class TracePayload(TypedDict, total=False):
    """Trace data for debugging and observability."""

    steps: list[dict[str, Any]]
    raw_state: Any
    metadata: dict[str, Any]


class AgentState(TypedDict, total=False):
    """Shared state passed between agents in the LangGraph workflow.

    This TypedDict defines all fields that can be passed through the agent graph.
    Fields are organized into logical groups for clarity.
    """

    # Run identification
    run_id: str
    run_at: str

    # Market identifiers
    gamma_event_id: str
    gamma_market_id: str
    market_url: str
    polymarket_url: str
    slug: str

    # Strategy configuration
    horizon: Horizon
    strategy_preset: StrategyPreset
    strategy_params: StrategyParams

    # Market and event data
    event: EventDocument
    market: MarketDocument
    market_snapshot: MarketSnapshot
    event_context: EventContext
    event_description: str

    # Market selection (when URL is an event with multiple markets)
    selected_market_slug: str
    market_options: list[dict[str, Any]]
    requires_market_selection: bool

    # News and research
    tavily_queries: list[TavilyQuerySpec]
    news_context: NewsContext

    # Analysis outputs
    signal: Signal
    decision: Decision
    report: ReportBlock

    # Position tracking
    position_side: Literal["flat", "long_yes", "long_no"]
    position_size_fraction: float
    position_avg_price: float

    # Metadata and configuration
    env: RunEnvMetadata
    trace: TracePayload
    config: dict[str, Any]
