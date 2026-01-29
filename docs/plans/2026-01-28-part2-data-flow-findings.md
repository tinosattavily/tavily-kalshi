# End-to-End Data Flow Exploration - Findings

> **Date:** 2026-01-28
> **Status:** Complete
> **Related Plan:** `2026-01-28-part2-data-flow-exploration.md`

---

## Task 1: Frontend Request Initiation

### Background.tsx Findings

**1. State Variables Tracking Analysis:**
- `url: string` - The Polymarket URL entered by user
- `isSubmitting: boolean` - Whether a submission is in progress
- `runId: string | null` - Current analysis run ID for polling
- `results: AnalysisResults | null` - Accumulated analysis results
- `runStatus: { market?, news?, signal?, report? } | null` - Phase completion statuses
- `pollingRef: React.MutableRefObject<boolean>` - Controls polling lifecycle
- `runIdRef: React.MutableRefObject<string | null>` - Ref for immediate runId access

**2. handleSubmit() (lines 214-303):**
- Endpoint: `POST /api/analyze/start`
- Request body:
```typescript
{
  market_url: url.trim(),
  configuration: {
    use_tavily_prompt_agent: boolean,
    use_news_summary_agent: boolean,
    max_articles: number,
    max_articles_per_query: number,
    min_confidence: string,
    enable_sentiment_analysis: boolean
  }
}
```
- Response handling: Expects `{ run_id: string }`
- Sets `runId` and `pollingRef.current = true` to start polling
- Initializes empty results skeleton for UI loading states

**3. handleSelectMarket() (lines 305-381):**
- Same endpoint `/api/analyze/start` with added `selected_market_slug` field
- Used when user selects from multiple markets in an event

**4. Configuration Options:**
- `useTavilyPromptAgent` - AI-generated search queries
- `useNewsSummaryAgent` - AI news summarization
- `maxArticles` - Total article limit
- `maxArticlesPerQuery` - Per-query article limit
- `minConfidence` - Signal confidence threshold
- `enableSentimentAnalysis` - Per-article sentiment

### UrlInputBar.tsx Findings

**Props:**
```typescript
{
  url: string,
  isSubmitting: boolean,
  isFocused: boolean,
  onChange: (value: string) => void,
  onSubmit: () => void,
  onKeyDown: (e: KeyboardEvent) => void,
  onFocusChange: (focused: boolean) => void
}
```

- Triggers submission via button click or Enter key
- Validation: Button disabled when `!url.trim() || isSubmitting`

### api.ts Findings

**`getBackendUrl()`:**
- Returns `BACKEND_URL` env var if set
- Development: `http://localhost:8000`
- Production: `https://tavily-backend-env.eba-jv6q9hd7.us-east-1.elasticbeanstalk.com`

**Error Handling:**
- `handleFetchError()` - Wraps errors in NextResponse JSON with status 500
- `parseErrorResponse()` - Extracts detail from response JSON or text

---

## Task 2: Next.js API Routes (Proxy Layer)

### analyze/start/route.ts Findings

- Proxies `POST` to `${getBackendUrl()}/api/analyze/start`
- **Timeout:** 10 seconds via AbortController
- Passes request body unchanged
- Returns backend response with `run_id`
- Error handling: 504 on timeout, propagates backend errors

### analyze/route.ts (Legacy) Findings

- Also proxies to `/api/analyze/start` (same endpoint)
- No timeout configured
- **Status:** Appears to be legacy wrapper, both routes use same backend endpoint

### run/[run_id]/route.ts Findings

- Proxies `GET` to `${getBackendUrl()}/api/run/${run_id}`
- **Timeout:** 60 seconds
- Validates `run_id` parameter (returns 400 for invalid)
- Returns `{ run: { ...runDocument } }`
- Handles 404 from backend for missing runs

### runs/recent/route.ts Findings

- Proxies `GET` to `${getBackendUrl()}/api/runs/recent?limit=${limit}`
- **Timeout:** 30 seconds
- Default limit: 20 (passed as query param)

---

## Task 3: Backend API Routes

### analyze.py Findings

**POST /api/analyze (Sync Endpoint):**
- Runs `run_analysis_graph()` synchronously
- Returns complete results in single response
- Persists via `persist_run_snapshot_async()`
- Returns `MarketSelectionResponse` if event URL requires market selection

**POST /api/analyze/start (Async Endpoint):**
1. Generates `run_id`: `f"run-{uuid4().hex}"`
2. Initializes run document: `init_run_document_async(run_id, market_url, horizon, strategy_preset, strategy_params)`
3. Spawns background task: `background_tasks.add_task(run_analysis_for_run_id, run_id, payload)`
4. Returns immediately: `{"run_id": run_id}`

**POST /api/reset-circuit-breaker (Admin):**
- Resets OpenAI circuit breaker state

### runs.py Findings

**GET /api/run/{run_id}:**
- Calls `get_run_async(run_id)`
- Returns 404 if not found
- Response: `SingleRunResponse(run=doc)` -> `{ run: { ...document } }`

**GET /api/runs/recent:**
- Calls `list_recent_runs_async(limit)`
- **Important:** Only returns complete runs (all phases "done")
- Response: `RunResponse(market_id="all", runs=[...])`

### main.py Findings

**FastAPI Configuration:**
- Title: "Tavily Signals API"
- Docs at `/docs`, ReDoc at `/redoc`

**Middleware:**
- `CORSMiddleware` - Origins from `CORS_ORIGINS` env var (default: `http://localhost:3000`)
- `GZipMiddleware` - Minimum size 1000 bytes

**Routes:**
- `analyze.router` mounted at `/api` with tags `["analysis"]`
- `runs.router` mounted at `/api` with tags `["runs"]`

**Exception Handler:**
- Global handler returns sanitized errors with request_id
- Prevents leaking internal details to clients

---

## Task 4: Background Task Execution

### phased_analysis.py Findings

**`run_analysis_for_run_id(run_id, req)`:**

1. **State Initialization:**
```python
state: AgentState = {
    "run_id": run_id,
    "market_url": str(req.market_url),
    "polymarket_url": str(req.market_url),
    "selected_market_slug": req.selected_market_slug,
    "horizon": req.horizon or "24h",
    "strategy_preset": req.strategy_preset or "Balanced",
    "strategy_params": {...},
    "config": {...}
}
```

2. **Graph Execution:** `state = await run_analysis_graph(state)`

3. **Phase Updates (after graph completes):**

   **Market Selection Check:**
   - If `state.get("requires_market_selection")`: Updates market phase as "done" with `market_options`, returns early

   **Phase 1 (Market/Event):**
   - `update_run_phase_async(run_id, "market", "done", {market_snapshot, event_context})`
   - `update_run_with_event_and_market_async(run_id, state)` - Links event/market IDs

   **Phase 2 (News):**
   - `update_run_phase_async(run_id, "news", "done", {news_context})`

   **Phase 3 (Signal/Report):**
   - `update_run_phase_async(run_id, "signal", "done", {signal, decision})`
   - `update_run_phase_async(run_id, "report", "done", {report})`

4. **Final Persistence:** `persist_run_snapshot_async(state)` for backward compatibility

5. **Error Handling:** On exception, marks all phases as "error"

---

## Task 5: Database Persistence Layer

### run_snapshot.py Findings

**`init_run_document_async()`:**
```python
{
    "run_id": run_id,           # String identifier for polling
    "polymarket_url": market_url,
    "slug": "pending",
    "run_at": timestamp,
    "horizon": horizon,
    "strategy_preset": strategy_preset,
    "strategy_params": strategy_params,
    "market_snapshot": {},
    "event_context": {},
    "news_context": {"tavily_queries": [], "articles": [], "summary": ""},
    "signal": {},
    "decision": {},
    "report": {},
    "env": {},
    "created_at": timestamp,
    "updated_at": timestamp,
    "status": {
        "market": "pending",
        "news": "pending",
        "signal": "pending",
        "report": "pending"
    }
}
```

**`persist_run_snapshot_async()`:**
1. Upserts event document (by slug)
2. Upserts market document (by slug)
3. Creates run document with full data
4. Creates trace document if trace payload exists
5. Returns: `{ run_id, event, market, run, trace_id? }`

**`update_run_phase_async()`:**
- Updates `status.{phase}` and phase-specific data fields
- Uses `run_id` string for MongoDB lookup
- Sets `updated_at` timestamp

### async_repositories.py Findings

**Collections:** events, markets, runs, traces

**Key Functions:**
- `upsert_event_async()` - Upserts by slug
- `upsert_market_async()` - Upserts by slug
- `create_run_async()` - Inserts new run
- `get_run_async()` - Supports both ObjectId and run_id string
- `list_recent_runs_async()` - Filters: `status.market/news/signal/report` all "done"

**Indexes:**
- events: `slug` (unique)
- markets: `slug` (unique), `polymarket_url` (unique), `event_id`
- runs: `(market_id, run_at)`, `(event_id, run_at)`, `slug`
- traces: `run_id`

### async_client.py Findings

**Motor Client Configuration:**
```python
AsyncIOMotorClient(
    settings.mongodb_uri,
    serverSelectionTimeoutMS=5000,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=45000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
    retryWrites=True,
    retryReads=True
)
```

**Database:** `"tavily_proj"`

### models.py Findings

**RunDocument Schema:**
```python
class RunDocument(TypedDict, total=False):
    _id: ObjectId
    market_id: ObjectId
    event_id: ObjectId
    polymarket_url: str
    slug: str
    run_at: str
    horizon: Horizon              # "intraday" | "24h" | "resolution"
    strategy_preset: StrategyPreset  # "Cautious" | "Balanced" | "Aggressive"
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
    trace_id: ObjectId           # Optional
    status: RunStatus            # Phase statuses
    run_id: str                  # String ID for polling
```

**RunStatus:**
```python
class RunStatus(TypedDict, total=False):
    market: str   # "pending" | "done" | "error"
    news: str     # "pending" | "done" | "error"
    signal: str   # "pending" | "done" | "error"
    report: str   # "pending" | "done" | "error"
```

---

## Task 6: Frontend Polling & Display

### Polling useEffect (lines 418-628)

**Polling Trigger:**
- Starts when `runId` (or `runIdRef.current`) is valid and `pollingRef.current === true`

**Polling Intervals:**
- Normal: 1500ms
- On error: 2500ms
- On 500 error: 3000ms
- On 404: 1500ms (run not found yet)

**Stops When:**
- All phases are "done" or "error"
- Market selection required (stops to wait for user)
- Component unmounts (cancelled flag)

**Incremental Updates:**
```javascript
// Status update
if (run.status) setRunStatus(run.status);

// Results update
if (run.status?.market === "done") -> market_snapshot, event_context, market_options
if (run.status?.news === "done") -> news_context
if (run.status?.signal === "done") -> signal, decision
if (run.status?.report === "done") -> report
```

**Market Selection Detection:**
```javascript
const requiresMarketSelection =
    run.market_options?.length > 0 &&
    (!run.market_snapshot || Object.keys(run.market_snapshot).length === 0);
```

**Completion Detection:**
```javascript
const allDoneOrError = phases.every(s => s === "done" || s === "error");
if (allDoneOrError) {
    pollingRef.current = false;
    setIsSubmitting(false);
    setRecentSessionsRefreshTrigger(prev => prev + 1);
}
```

---

## Summary Sequence Diagram

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐     ┌───────────┐
│ Browser │     │ Next.js API │     │   FastAPI   │     │ MongoDB │     │ LangGraph │
└────┬────┘     └──────┬──────┘     └──────┬──────┘     └────┬────┘     └─────┬─────┘
     │                 │                   │                 │                 │
     │ POST /api/analyze/start             │                 │                 │
     │────────────────>│                   │                 │                 │
     │                 │ POST /api/analyze/start             │                 │
     │                 │──────────────────>│                 │                 │
     │                 │                   │                 │                 │
     │                 │                   │ generate run_id │                 │
     │                 │                   │ (run-{uuid})    │                 │
     │                 │                   │                 │                 │
     │                 │                   │ init_run_document_async           │
     │                 │                   │────────────────>│                 │
     │                 │                   │    (status: all pending)          │
     │                 │                   │<────────────────│                 │
     │                 │                   │                 │                 │
     │                 │                   │ add_background_task               │
     │                 │                   │─────────────────────────────────>│
     │                 │                   │                 │                 │
     │                 │   { run_id }      │                 │                 │
     │                 │<──────────────────│                 │                 │
     │  { run_id }     │                   │                 │                 │
     │<────────────────│                   │                 │                 │
     │                 │                   │                 │                 │
     │ (start polling) │                   │     [BACKGROUND TASK]             │
     │                 │                   │                 │                 │
     │                 │                   │                 │<────────────────│
     │                 │                   │                 │  run_analysis   │
     │                 │                   │                 │  _graph()       │
     │                 │                   │                 │                 │
     │                 │                   │                 │  Phase 1 done   │
     │                 │                   │ update_run_phase(market, done)    │
     │                 │                   │────────────────>│                 │
     │                 │                   │                 │                 │
     │ GET /api/run/{id}                   │                 │                 │
     │────────────────>│                   │                 │                 │
     │                 │ GET /api/run/{id} │                 │                 │
     │                 │──────────────────>│                 │                 │
     │                 │                   │ get_run_async   │                 │
     │                 │                   │────────────────>│                 │
     │                 │                   │   run doc       │                 │
     │                 │                   │<────────────────│                 │
     │                 │ { run: { status: {market: done}}}   │                 │
     │                 │<──────────────────│                 │                 │
     │ (show market)   │                   │                 │                 │
     │<────────────────│                   │                 │                 │
     │                 │                   │                 │  Phase 2 done   │
     │                 │                   │ update_run_phase(news, done)      │
     │                 │                   │────────────────>│                 │
     │                 │                   │                 │                 │
     │ GET /api/run/{id}                   │                 │                 │
     │ (poll again)    │                   │                 │                 │
     │─────...─────────│─────...───────────│─────...─────────│                 │
     │ (show news)     │                   │                 │                 │
     │                 │                   │                 │  Phase 3 done   │
     │                 │                   │ update_run_phase(signal, done)    │
     │                 │                   │ update_run_phase(report, done)    │
     │                 │                   │────────────────>│                 │
     │                 │                   │                 │<────────────────│
     │                 │                   │                 │  Graph complete │
     │ GET /api/run/{id}                   │                 │                 │
     │ (final poll)    │                   │                 │                 │
     │────────────────>│──────────────────>│────────────────>│                 │
     │                 │                   │                 │                 │
     │ (all phases done - stop polling)    │                 │                 │
     │<────────────────│<──────────────────│<────────────────│                 │
     │                 │                   │                 │                 │
```

---

## Key Data Transformations

| Layer | Input | Output |
|-------|-------|--------|
| Frontend -> Next.js | `{ market_url, configuration }` | Same |
| Next.js -> FastAPI | Same | Same |
| FastAPI analyze/start | Request | `{ run_id }` immediate |
| Background Task | AgentState | DB updates per phase |
| MongoDB -> FastAPI | run document | SingleRunResponse |
| FastAPI -> Next.js | `{ run: {...} }` | Same |
| Next.js -> Frontend | Same | Same |
| Frontend | run.status + run.* | UI components |

---

## Error Handling Summary

| Layer | Error Type | Handling |
|-------|------------|----------|
| Frontend | Network error | Alert + retry polling |
| Next.js | Timeout | 504 response |
| Next.js | Backend error | Propagate status + detail |
| FastAPI | Validation | 400 with detail |
| FastAPI | Internal | 500 with sanitized message |
| Background Task | Any phase | Mark all phases "error" |
| MongoDB | Connection | RuntimeError propagated |

---

## Key Files Reference

### Frontend
- `frontend/components/Background.tsx` - Main component, state management, polling
- `frontend/components/background/UrlInputBar.tsx` - URL input UI
- `frontend/lib/api.ts` - Backend URL config, error helpers

### Next.js API Routes
- `frontend/app/api/analyze/start/route.ts` - Proxy to start analysis
- `frontend/app/api/analyze/route.ts` - Legacy sync endpoint
- `frontend/app/api/run/[run_id]/route.ts` - Proxy for run status
- `frontend/app/api/runs/recent/route.ts` - Proxy for recent runs

### Backend Routes
- `backend/app/routes/analyze.py` - Analysis endpoints
- `backend/app/routes/runs.py` - Run retrieval endpoints
- `backend/app/main.py` - FastAPI app configuration

### Background Processing
- `backend/app/services/phased_analysis.py` - Background task execution

### Database Layer
- `backend/app/services/run_snapshot.py` - Run document management
- `backend/app/db/async_repositories.py` - MongoDB CRUD operations
- `backend/app/db/async_client.py` - Motor client configuration
- `backend/app/db/models.py` - TypedDict schemas
