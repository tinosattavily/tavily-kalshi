# Part 1: Agent System Exploration Findings

> Generated from exploration of the 8-agent LangGraph pipeline

---

## 1. Agent Pipeline - Execution Order

```
[Input: market_url]
       ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 1. MARKET_AGENT                                                       │
│    • Fetches event/market data from Polymarket Gamma API             │
│    • Handles single vs multi-market events                           │
│    • Fetches order book from CLOB API                                │
│    Output: market, market_snapshot, event, market_options            │
└──────────────────────────────────────────────────────────────────────┘
       ↓ (conditional: if requires_market_selection → END)
┌──────────────────────────────────────────────────────────────────────┐
│ 2. EVENT_AGENT                                                        │
│    • Normalizes event metadata                                       │
│    • No external API calls                                           │
│    Output: event (normalized), event_context, event_description      │
└──────────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 3. TAVILY_PROMPT_AGENT (optional - config.use_tavily_prompt_agent)   │
│    • Uses OpenAI to generate 1-3 optimized search queries            │
│    Output: tavily_queries (list of TavilyQuerySpec)                  │
└──────────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 4. NEWS_AGENT                                                         │
│    • Executes Tavily searches (or uses fallback queries)             │
│    • Deduplicates articles, runs sentiment analysis                  │
│    Output: news_context.articles, news_context.queries               │
└──────────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 5. NEWS_SUMMARY_AGENT (optional - config.use_news_summary_agent)     │
│    • Uses OpenAI to generate sentiment-weighted summary              │
│    Output: news_context.summary                                      │
└──────────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 6. PROBABILITY_AGENT                                                  │
│    • Uses OpenAI to generate probability estimate                    │
│    • Computes edge, Kelly fractions, confidence                      │
│    Output: signal (Signal model)                                     │
└──────────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 7. STRATEGY_AGENT                                                     │
│    • Applies strategy parameters (preset + overrides)                │
│    • Determines action: BUY_YES, BUY_NO, REDUCE, HOLD               │
│    Output: signal (updated), decision                                │
└──────────────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 8. REPORT_AGENT                                                       │
│    • Uses OpenAI to generate structured trade report                 │
│    Output: report (ReportBlock)                                      │
└──────────────────────────────────────────────────────────────────────┘
       ↓
[Output: complete AgentState]
```

---

## 2. Data Flow - What Each Agent Reads & Writes

| Agent | Reads From State | Writes To State |
|-------|------------------|-----------------|
| **market_agent** | `market_url`, `slug`, `selected_market_slug` | `market`, `market_snapshot`, `event`, `market_options`, `requires_market_selection` |
| **event_agent** | `slug`, `event`, `run_at`, `polymarket_url` | `event` (normalized), `event_context`, `event_description` |
| **tavily_prompt_agent** | `market_snapshot`, `event_context`, `horizon`, `strategy_preset` | `tavily_queries` |
| **news_agent** | `tavily_queries`, `event_context`, `market_snapshot`, `config` | `news_context.articles`, `news_context.queries`, `news_context.combined_summary` |
| **news_summary_agent** | `news_context`, `event_context`, `market_snapshot` | `news_context.summary` |
| **prob_agent** | `market_snapshot`, `event_context`, `news_context`, `horizon` | `signal` |
| **strategy_agent** | `signal`, `strategy_preset`, `strategy_params`, `config`, position fields | `signal` (updated), `decision`, `strategy_params` |
| **report_agent** | `market_snapshot`, `signal`, `decision`, `event_context`, `news_context` | `report`, `env` |

---

## 3. Optional Agents

| Agent | Skip Condition | Behavior When Skipped |
|-------|----------------|----------------------|
| **tavily_prompt_agent** | `config.use_tavily_prompt_agent = False` | Returns state unchanged; news_agent uses fallback queries |
| **news_summary_agent** | `config.use_news_summary_agent = False` | Returns state unchanged; uses `combined_summary` from news_agent |

**Conditional Exit:**
- `market_agent` can return early with `requires_market_selection = True` when a multi-market event URL is provided without a selected market slug

---

## 4. External API Calls

| Agent | API | Endpoint | Purpose |
|-------|-----|----------|---------|
| **market_agent** | Polymarket Gamma | `/events?slug=X` | Fetch event + nested markets |
| **market_agent** | Polymarket Gamma | `/markets?slug=X` | Fallback for single markets |
| **market_agent** | Polymarket CLOB | `/book?token_id=X` | Fetch order book |
| **tavily_prompt_agent** | OpenAI | `chat.completions` | Generate search queries |
| **news_agent** | Tavily | `/search` | Search for news articles |
| **news_summary_agent** | OpenAI | `chat.completions` | Generate news summary |
| **prob_agent** | OpenAI | `chat.completions` | Generate probability signal |
| **report_agent** | OpenAI | `chat.completions` | Generate trade report |

**Resilience:** All external calls use caching, retry logic (3 attempts, exponential backoff), and circuit breakers.

---

## 5. Key Decision Logic

### Trading Signal Calculation (prob_agent)

```python
p_mkt = infer_market_prob(market_snapshot)  # from yes_price
p_model = OpenAI LLM estimate
edge = p_model - p_mkt
kelly_yes = (p_model * (1/p_mkt) - 1) / (1/p_mkt - 1)  # simplified
kelly_no = ((1-p_model) * (1/(1-p_mkt)) - 1) / (1/(1-p_mkt) - 1)
confidence = estimate_confidence(news_context) OR LLM override
```

### Strategy Decision (strategy_agent)

```python
# Check thresholds
if risk_off OR confidence < min_confidence OR |edge| < min_edge_pct:
    action = HOLD

# Determine direction
if edge > 0:
    raw_fraction = kelly_yes
    side = "long_yes"
else:
    raw_fraction = kelly_no
    side = "long_no"

# Apply limits
target = min(raw_fraction * max_kelly_fraction, max_capital_pct)

# Compare with position
if flat: action = BUY (if target > 0)
if same_side: action = BUY (add) or REDUCE
if opposite_side: action = HOLD (no reversal logic)
```

### Strategy Presets

| Preset | min_edge | min_confidence | max_capital | max_kelly |
|--------|----------|----------------|-------------|-----------|
| **Conservative** | 8% | high | 8% | 0.15 (15% Kelly) |
| **Balanced** | 5% | medium | 15% | 0.25 (25% Kelly) |
| **Aggressive** | 3% | low | 25% | 0.50 (50% Kelly) |

---

## 6. AgentState TypedDict

All fields in the shared state:

```python
class AgentState(TypedDict, total=False):
    # Run metadata
    run_id: str
    run_at: str

    # Market identifiers
    gamma_event_id: str
    gamma_market_id: str
    market_url: str
    polymarket_url: str
    slug: str

    # Configuration
    horizon: Horizon  # "intraday" | "24h" | "resolution"
    strategy_preset: StrategyPreset  # "Cautious" | "Balanced" | "Aggressive"
    strategy_params: StrategyParams
    config: dict[str, Any]  # Agent toggles, limits, etc.

    # Market data (from market_agent)
    event: EventDocument
    market: MarketDocument
    market_snapshot: MarketSnapshot

    # Market selection (multi-market events)
    selected_market_slug: str
    market_options: list
    requires_market_selection: bool

    # Event context (from event_agent)
    event_context: EventContext
    event_description: str

    # News data (from news pipeline)
    tavily_queries: list[TavilyQuerySpec]
    news_context: NewsContext

    # Signal data (from prob_agent + strategy_agent)
    signal: Signal
    decision: Decision

    # Report (from report_agent)
    report: ReportBlock

    # Position tracking
    position_side: Literal["flat", "long_yes", "long_no"]
    position_size_fraction: float
    position_avg_price: float

    # Debug/trace
    env: RunEnvMetadata
    trace: TracePayload
```

---

## 7. Graph Orchestration (graph.py)

### Build Process

```python
def build_analysis_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    # Add 8 nodes
    builder.add_node("market_agent", market_agent_node)
    builder.add_node("event_agent", event_agent_node)
    builder.add_node("tavily_prompt_agent", tavily_prompt_agent_node)
    builder.add_node("news_agent", news_agent_node)
    builder.add_node("news_summary_agent", news_summary_agent_node)
    builder.add_node("probability_agent", probability_agent_node)
    builder.add_node("strategy_agent", strategy_agent_node)
    builder.add_node("report_agent", report_agent_node)

    # Wire: START → market_agent
    builder.add_edge(START, "market_agent")

    # Conditional: market_agent → (event_agent | END)
    builder.add_conditional_edges(
        "market_agent",
        route_after_market,  # Returns "event_agent" or "end"
        {"event_agent": "event_agent", "end": END}
    )

    # Linear chain
    builder.add_edge("event_agent", "tavily_prompt_agent")
    builder.add_edge("tavily_prompt_agent", "news_agent")
    builder.add_edge("news_agent", "news_summary_agent")
    builder.add_edge("news_summary_agent", "probability_agent")
    builder.add_edge("probability_agent", "strategy_agent")
    builder.add_edge("strategy_agent", "report_agent")
    builder.add_edge("report_agent", END)

    return builder.compile()
```

### Routing Logic

```python
def route_after_market(state: AgentState) -> str:
    if state.get("requires_market_selection"):
        return "end"  # Stop for UI to handle selection
    return "event_agent"  # Continue pipeline
```

---

## 8. Key File Locations

| Component | File |
|-----------|------|
| Graph orchestration | `backend/app/agents/graph.py` |
| Shared state | `backend/app/agents/state.py` |
| Market agent | `backend/app/agents/market_agent.py` |
| Event agent | `backend/app/agents/event_agent.py` |
| Tavily prompt agent | `backend/app/agents/tavily_prompt_agent.py` |
| News agent | `backend/app/agents/news_agent.py` |
| News summary agent | `backend/app/agents/news_summary_agent.py` |
| Probability agent | `backend/app/agents/prob_agent.py` |
| Strategy agent | `backend/app/agents/strategy_agent.py` |
| Report agent | `backend/app/agents/report_agent.py` |
| Polymarket utils | `backend/app/core/polymarket_utils.py` |
| Market transformer | `backend/app/core/market_transformer.py` |
| Tavily client | `backend/app/services/tavily_client.py` |
| OpenAI client | `backend/app/services/openai_client.py` |
| DB models | `backend/app/db/models.py` |
