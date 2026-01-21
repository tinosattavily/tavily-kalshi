from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

from bson import ObjectId

StrategyPreset = Literal["Cautious", "Balanced", "Aggressive"]
Horizon = Literal["intraday", "24h", "resolution"]
SignalDirection = Literal["up", "down", "flat"]
DecisionAction = Literal["BUY", "SELL", "HOLD"]
ConfidenceLevel = Literal["low", "medium", "high"]


class StrategyParams(TypedDict, total=False):
    min_edge_pct: float
    min_confidence: ConfidenceLevel
    max_capital_pct: float
    max_kelly_fraction: float  # Never use more than this fraction of full Kelly (e.g. 0.25)
    risk_off: bool  # To quickly disable new positions


class EventDocument(TypedDict, total=False):
    _id: ObjectId
    gamma_event_id: str
    slug: str
    title: str
    description: str
    category: str
    image: str | None
    end_date: str
    created_at: str
    updated_at: str


class MarketDocument(TypedDict, total=False):
    _id: ObjectId
    event_id: ObjectId
    gamma_market_id: str
    slug: str
    polymarket_url: str
    question: str
    outcomes: list[str]
    yes_index: int
    group_item_title: str | None
    created_at: str
    updated_at: str


class MarketSnapshot(TypedDict, total=False):
    question: str
    outcomes: list[str]
    yes_index: int
    yes_price: float
    no_price: float
    best_bid: float
    best_ask: float
    last_trade_price: float
    volume: float
    liquidity: float
    end_date: str


class EventContext(TypedDict, total=False):
    title: str
    description: str
    category: str


class NewsArticle(TypedDict, total=False):
    title: str
    source: str
    url: str
    published_at: str
    snippet: str
    sentiment: str  # "bullish", "bearish", or "neutral"


class NewsContext(TypedDict, total=False):
    tavily_queries: list[str]
    articles: list[NewsArticle]
    summary: str


class Signal(TypedDict, total=False):
    direction: SignalDirection
    model_prob: float
    model_prob_abs: float
    expected_delta_range: list[float]
    confidence: ConfidenceLevel
    rationale: str


class Decision(TypedDict, total=False):
    action: DecisionAction
    edge_pct: float
    toy_kelly_fraction: float
    notes: str


class ReportBlock(TypedDict, total=False):
    # Legacy fields (for backward compatibility)
    title: str
    markdown: str
    # New structured fields
    headline: str
    thesis: str
    bull_case: list[str]
    bear_case: list[str]
    key_risks: list[str]
    execution_notes: str


class RunEnvMetadata(TypedDict, total=False):
    app_version: str
    model: str
    tavily_version: str
    langgraph_graph_version: str


class RunStatus(TypedDict, total=False):
    market: str  # "pending" | "done" | "error"
    news: str  # "pending" | "done" | "error"
    signal: str  # "pending" | "done" | "error"
    report: str  # "pending" | "done" | "error"


class RunDocument(TypedDict, total=False):
    _id: ObjectId
    market_id: ObjectId
    event_id: ObjectId
    polymarket_url: str
    slug: str
    run_at: str
    horizon: Horizon
    strategy_preset: StrategyPreset
    strategy_params: StrategyParams
    market_snapshot: MarketSnapshot
    event_context: EventContext
    news_context: NewsContext
    signal: Signal
    decision: Decision
    report: ReportBlock
    env: RunEnvMetadata
    created_at: str
    updated_at: str
    trace_id: NotRequired[ObjectId]
    status: RunStatus
    run_id: str  # String identifier for the run (used for polling)


class TraceDocument(TypedDict, total=False):
    _id: ObjectId
    run_id: ObjectId
    created_at: str
    steps: list[dict[str, Any]]
    raw_state: Any
    metadata: dict[str, Any] | None
