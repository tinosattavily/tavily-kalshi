# Prophily Comprehensive Codebase Exploration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Develop complete understanding of the Prophily prediction market analysis system through systematic exploration of agents, data flow, API integrations, and frontend architecture.

**Architecture:** Prophily is a multi-agent AI system using LangGraph for orchestration. 8 specialized agents analyze Polymarket prediction markets by combining market data, news context (via Tavily), and AI analysis (via OpenAI) to generate trading signals with Kelly Criterion sizing.

**Tech Stack:** FastAPI (Python 3.11), LangGraph, MongoDB, Next.js 16, TypeScript, React 19, Tailwind CSS

---

## Part 1: LangGraph Agent System (Core Logic)

### Task 1.1: Understand Agent Orchestration

**Files:**
- Read: `backend/app/agents/graph.py` (already read - orchestration)
- Read: `backend/app/agents/state.py` (already read - shared state)

**Step 1: Document the agent execution flow**

The LangGraph `StateGraph` defines this sequential pipeline:
```
START → market_agent → (conditional: event_agent | END)
     → event_agent → tavily_prompt_agent → news_agent
     → news_summary_agent → probability_agent → strategy_agent
     → report_agent → END
```

**Key observations:**
- `route_after_market()` enables conditional routing - if `requires_market_selection=True`, graph halts for user input
- Two optional agents: `tavily_prompt_agent` and `news_summary_agent` (controlled by `config` dict)
- All agents share `AgentState` TypedDict - 72 lines defining all fields passed between agents

**Step 2: Document the AgentState structure**

| Field | Type | Purpose |
|-------|------|---------|
| `run_id` | str | Unique identifier for the analysis run |
| `market_url` | str | Polymarket URL being analyzed |
| `market_snapshot` | MarketSnapshot | Current market prices, volume, liquidity |
| `event_context` | EventContext | Event metadata (title, description) |
| `news_context` | NewsContext | Aggregated news articles with sentiment |
| `signal` | Signal | AI-generated trading signal |
| `decision` | Decision | Kelly sizing and action recommendation |
| `report` | ReportBlock | Comprehensive analysis report |
| `config` | dict | Runtime configuration (agent toggles, limits) |

---

### Task 1.2: Analyze Market Agent

**Files:**
- Read: `backend/app/agents/market_agent.py` (already read)
- Read: `backend/app/core/polymarket_utils.py`
- Read: `backend/app/core/market_transformer.py`
- Read: `backend/app/core/market_selector.py`

**Step 1: Read polymarket_utils.py**

Run: Read `backend/app/core/polymarket_utils.py`

Document:
- `extract_slug_from_url()` - URL parsing
- `get_event_and_markets_by_slug()` - API fetch with caching
- `fetch_order_book_async()` - CLOB order book retrieval

**Step 2: Read market_transformer.py**

Run: Read `backend/app/core/market_transformer.py`

Document:
- `build_market_options()` - Transform API markets to selection list
- `build_market_snapshot()` - Construct normalized snapshot

**Step 3: Read market_selector.py**

Run: Read `backend/app/core/market_selector.py`

Document:
- `select_market_from_options()` - Auto-selection vs user selection logic
- `find_market_by_slug()` - Market lookup

**Step 4: Document market_agent behavior**

Key responsibilities:
1. Extract slug from Polymarket URL
2. Fetch event + markets from Polymarket Gamma API
3. Detect single market vs multi-market event
4. Build market options for selection UI (if needed)
5. Fetch order book from CLOB API
6. Populate `market_snapshot` in state

---

### Task 1.3: Analyze Event Agent

**Files:**
- Read: `backend/app/agents/event_agent.py`

**Step 1: Read event_agent.py**

Run: Read `backend/app/agents/event_agent.py`

Document:
- What metadata it extracts
- How it populates `event_context`
- Any API calls or transformations

---

### Task 1.4: Analyze News Pipeline Agents

**Files:**
- Read: `backend/app/agents/tavily_prompt_agent.py`
- Read: `backend/app/agents/news_agent.py`
- Read: `backend/app/agents/news_summary_agent.py`
- Read: `backend/app/services/tavily_client.py`

**Step 1: Read tavily_prompt_agent.py**

Document:
- How it generates search queries from event context
- The `TavilyQuerySpec` structure
- OpenAI prompt used

**Step 2: Read news_agent.py**

Document:
- How it executes Tavily searches
- Article extraction and normalization
- Error handling

**Step 3: Read news_summary_agent.py**

Document:
- How it summarizes articles
- Sentiment analysis integration
- OpenAI prompt used

**Step 4: Read tavily_client.py**

Document:
- Tavily API integration
- Caching strategy
- Rate limiting

---

### Task 1.5: Analyze Signal Generation Agents

**Files:**
- Read: `backend/app/agents/prob_agent.py`
- Read: `backend/app/agents/strategy_agent.py`
- Read: `backend/app/agents/report_agent.py`

**Step 1: Read prob_agent.py**

Document:
- How it generates probability estimates
- The Signal structure (direction, model_prob, confidence)
- OpenAI prompt and response parsing

**Step 2: Read strategy_agent.py**

Document:
- Kelly Criterion implementation
- Edge calculation: `(model_prob - market_price) / (1 - market_price)`
- Decision logic (BUY/SELL/HOLD)

**Step 3: Read report_agent.py**

Document:
- Report structure (headline, thesis, bull/bear cases)
- OpenAI prompt for comprehensive analysis
- Markdown generation

---

## Part 2: End-to-End Data Flow

### Task 2.1: Trace Frontend Request Initiation

**Files:**
- Read: `frontend/components/Background.tsx` (already read)
- Read: `frontend/app/api/analyze/start/route.ts`
- Read: `frontend/lib/api.ts`

**Step 1: Document frontend request flow**

1. User enters Polymarket URL in `UrlInputBar`
2. `handleSubmit()` calls `POST /api/analyze/start`
3. Response returns `run_id`
4. `useEffect` starts polling `/api/run/{run_id}`
5. Results update incrementally as phases complete

**Step 2: Read Next.js API route**

Run: Read `frontend/app/api/analyze/start/route.ts`

Document:
- How it proxies to backend
- Request/response transformation
- Error handling

---

### Task 2.2: Trace Backend Request Handling

**Files:**
- Read: `backend/app/routes/analyze.py` (already read)
- Read: `backend/app/services/phased_analysis.py`
- Read: `backend/app/services/run_snapshot.py`

**Step 1: Document `/analyze/start` endpoint**

1. Generate `run_id`
2. Initialize run document in MongoDB
3. Spawn background task via `BackgroundTasks`
4. Return `run_id` immediately

**Step 2: Read phased_analysis.py**

Run: Read `backend/app/services/phased_analysis.py`

Document:
- Phase execution order
- How each phase updates MongoDB
- Error handling per phase

**Step 3: Read run_snapshot.py**

Run: Read `backend/app/services/run_snapshot.py`

Document:
- `init_run_document_async()` - Initial document creation
- `persist_run_snapshot_async()` - Final persistence
- Document schema

---

### Task 2.3: Trace Database Persistence

**Files:**
- Read: `backend/app/db/models.py` (already read)
- Read: `backend/app/db/async_repositories.py`
- Read: `backend/app/db/async_client.py`

**Step 1: Document MongoDB schema**

Collections:
- `runs` - Analysis run documents
- `traces` - Debug traces (optional)

Key document structure: `RunDocument` with nested `MarketSnapshot`, `NewsContext`, `Signal`, `Decision`, `ReportBlock`

**Step 2: Read async_repositories.py**

Run: Read `backend/app/db/async_repositories.py`

Document:
- Repository pattern implementation
- CRUD operations for runs
- Query patterns

**Step 3: Read async_client.py**

Run: Read `backend/app/db/async_client.py`

Document:
- Motor async client setup
- Connection pooling
- Error handling

---

### Task 2.4: Trace Frontend Polling & Display

**Files:**
- Read: `frontend/app/api/run/[run_id]/route.ts`
- Read: `frontend/components/background/SignalCard.tsx`
- Read: `frontend/components/background/ReportCard.tsx`

**Step 1: Read polling endpoint**

Run: Read `frontend/app/api/run/[run_id]/route.ts`

Document:
- How it fetches from backend
- Response transformation

**Step 2: Document polling logic in Background.tsx**

The `useEffect` at line 419-628:
1. Polls every 1.5s (or 3s on error)
2. Updates `runStatus` from `run.status`
3. Updates `results` incrementally
4. Stops when all phases are "done" or "error"

**Step 3: Document result display components**

- `MarketSnapshotCard` - Shows prices, volume, order book
- `NewsCard` - Shows articles with sentiment
- `SignalCard` - Shows direction, confidence, rationale
- `ReportCard` - Shows full analysis report

---

## Part 3: API Integrations

### Task 3.1: Polymarket API Integration

**Files:**
- Read: `backend/app/services/polymarket_client.py` (already read)
- Read: `backend/app/core/polymarket_utils.py`
- Read: `backend/app/core/resilience.py`

**Step 1: Document Polymarket APIs used**

1. **Gamma API** (`https://gamma-api.polymarket.com`)
   - `/events?slug={slug}` - Event metadata + markets
   - `/markets?slug={slug}` - Single market lookup

2. **CLOB API** (`https://clob.polymarket.com`)
   - `/book?token_id={id}` - Order book (bids/asks)

**Step 2: Read resilience.py**

Run: Read `backend/app/core/resilience.py`

Document:
- Circuit breaker implementation
- Retry logic with tenacity
- Failure thresholds

---

### Task 3.2: Tavily API Integration

**Files:**
- Read: `backend/app/services/tavily_client.py`

**Step 1: Document Tavily integration**

Run: Read `backend/app/services/tavily_client.py`

Document:
- Search endpoint usage
- Result extraction
- Rate limiting / caching

---

### Task 3.3: OpenAI API Integration

**Files:**
- Read: `backend/app/services/openai_client.py`
- Read: `backend/app/core/resilience.py` (circuit breaker)

**Step 1: Read openai_client.py**

Run: Read `backend/app/services/openai_client.py`

Document:
- Client initialization
- Model used (gpt-4, gpt-4-turbo, etc.)
- Prompt patterns
- Error handling with circuit breaker

---

## Part 4: Frontend Architecture

### Task 4.1: Component Hierarchy

**Files:**
- Read: `frontend/app/page.tsx`
- Read: `frontend/app/layout.tsx`
- Read: `frontend/components/Background.tsx` (already read)

**Step 1: Document component tree**

```
app/layout.tsx (root layout)
└── app/page.tsx (home page)
    └── Background.tsx (main container)
        ├── GridAndNoise.tsx (background effects)
        ├── TopNav.tsx (navigation)
        ├── RecentSessions.tsx (left sidebar)
        ├── UrlInputBar.tsx (URL input)
        ├── ConfigurationPanel.tsx (right sidebar)
        ├── MarketSelection.tsx (market picker)
        ├── MarketSnapshotCard.tsx (market data)
        ├── NewsCard.tsx (news articles)
        ├── SignalCard.tsx (trading signal)
        ├── DecisionCard.tsx (Kelly sizing)
        └── ReportCard.tsx (analysis report)
```

---

### Task 4.2: State Management

**Files:**
- Read: `frontend/components/Background.tsx` (already read)

**Step 1: Document state variables**

| State | Type | Purpose |
|-------|------|---------|
| `url` | string | Current Polymarket URL |
| `isSubmitting` | boolean | Loading state |
| `results` | AnalysisResults | Analysis output |
| `runStatus` | object | Phase completion status |
| `runId` | string | Current analysis run ID |
| `configuration` | AnalysisConfiguration | User settings |

**Step 2: Document key handlers**

- `handleSubmit()` - Initiates analysis
- `handleSelectMarket()` - Market selection
- `handleRunSelect()` - Load saved run
- `poll()` - Polling loop

---

### Task 4.3: Configuration Panel

**Files:**
- Read: `frontend/components/background/ConfigurationPanel.tsx`

**Step 1: Read ConfigurationPanel.tsx**

Run: Read `frontend/components/background/ConfigurationPanel.tsx`

Document:
- Available configuration options
- Default values
- How config is passed to backend

---

### Task 4.4: Skeleton Loading States

**Files:**
- Read: `frontend/components/skeletons/MarketSnapshotSkeleton.tsx`
- Read: `frontend/components/skeletons/SignalSkeleton.tsx`

**Step 1: Document skeleton pattern**

How skeletons provide loading UX:
1. Show skeleton while `runStatus.{phase} === "pending"`
2. Replace with actual card when `runStatus.{phase} === "done"`
3. Hide on error or when data is missing

---

## Summary Checklist

After completing all tasks, you should be able to answer:

- [ ] How does the LangGraph agent pipeline execute?
- [ ] What does each of the 8 agents do?
- [ ] How is shared state passed between agents?
- [ ] How does the frontend initiate analysis?
- [ ] How does polling work for incremental updates?
- [ ] What external APIs are used and how?
- [ ] How is data persisted in MongoDB?
- [ ] How does the frontend display results?
- [ ] What configuration options are available?
- [ ] How does error handling work across the stack?

---

## Execution Notes

**Estimated read operations:** ~25 files
**No code changes:** This is an exploration plan only

When executing, use parallel reads where possible to speed up exploration. Document findings as comments or notes for future reference.
