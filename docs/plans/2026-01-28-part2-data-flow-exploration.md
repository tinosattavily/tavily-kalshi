# Part 2: End-to-End Data Flow Exploration

> **For Claude:** This is a READ-ONLY exploration plan. Do not modify any files. Document findings as you go.

**Goal:** Trace the complete data flow from frontend request to backend processing to database persistence and back to frontend display.

**Context:** Prophily uses a phased analysis approach where the frontend initiates analysis, receives a run_id, then polls for incremental updates as each phase completes.

**Deliverable:** After completing this plan, produce a sequence diagram showing the complete request lifecycle.

---

## Task 1: Frontend Request Initiation

**Files to read:**
- `frontend/components/Background.tsx`
- `frontend/components/background/UrlInputBar.tsx`
- `frontend/lib/api.ts`

**Step 1: Read Background.tsx (focus on submission)**

```bash
cat frontend/components/Background.tsx
```

**Document these findings:**
1. What state variables track the analysis? (`url`, `isSubmitting`, `runId`, `results`, `runStatus`)
2. How does `handleSubmit()` work?
   - What endpoint does it call?
   - What request body does it send?
   - How does it handle the response?
3. How does `handleSelectMarket()` handle market selection?
4. What configuration options are sent to backend?

**Step 2: Read UrlInputBar.tsx**

```bash
cat frontend/components/background/UrlInputBar.tsx
```

**Document these findings:**
1. What props does it receive?
2. How does it trigger submission?
3. Any validation on the URL?

**Step 3: Read api.ts**

```bash
cat frontend/lib/api.ts
```

**Document these findings:**
1. Are there any API helper functions?
2. Base URL configuration?
3. Error handling patterns?

---

## Task 2: Next.js API Routes (Proxy Layer)

**Files to read:**
- `frontend/app/api/analyze/start/route.ts`
- `frontend/app/api/analyze/route.ts`
- `frontend/app/api/run/[run_id]/route.ts`
- `frontend/app/api/runs/recent/route.ts`

**Step 1: Read analyze/start/route.ts**

```bash
cat frontend/app/api/analyze/start/route.ts
```

**Document these findings:**
1. How does it proxy to the backend?
2. What is the backend URL?
3. How is the request body transformed?
4. How are errors handled?

**Step 2: Read analyze/route.ts (legacy sync endpoint)**

```bash
cat frontend/app/api/analyze/route.ts
```

**Document these findings:**
1. Is this still used or deprecated?
2. How does it differ from the async version?

**Step 3: Read run/[run_id]/route.ts**

```bash
cat "frontend/app/api/run/[run_id]/route.ts"
```

**Document these findings:**
1. How does it fetch run status from backend?
2. What response structure does it return?
3. How does it handle 404 (run not found)?

**Step 4: Read runs/recent/route.ts**

```bash
cat frontend/app/api/runs/recent/route.ts
```

**Document these findings:**
1. How does it fetch recent runs?
2. What query parameters does it support?

---

## Task 3: Backend API Routes

**Files to read:**
- `backend/app/routes/analyze.py`
- `backend/app/routes/runs.py`
- `backend/app/main.py`

**Step 1: Read analyze.py**

```bash
cat backend/app/routes/analyze.py
```

**Document these findings:**
1. **POST /analyze** (sync endpoint):
   - How does it run the analysis graph?
   - How does it handle market selection?
   - How does it persist results?

2. **POST /analyze/start** (async endpoint):
   - How does it generate run_id?
   - How does it initialize the run document?
   - How does it spawn the background task?
   - What does it return immediately?

3. **POST /reset-circuit-breaker**:
   - What does this admin endpoint do?

**Step 2: Read runs.py**

```bash
cat backend/app/routes/runs.py
```

**Document these findings:**
1. **GET /run/{run_id}**:
   - How does it fetch run status?
   - What fields does it return?
   - How does it handle missing runs?

2. **GET /runs/recent**:
   - How does it query recent runs?
   - What pagination/limits apply?

**Step 3: Read main.py**

```bash
cat backend/app/main.py
```

**Document these findings:**
1. How is the FastAPI app configured?
2. What middleware is used? (CORS, logging, etc.)
3. How are routes mounted?
4. What exception handlers exist?

---

## Task 4: Background Task Execution

**Files to read:**
- `backend/app/services/phased_analysis.py`

**Step 1: Read phased_analysis.py**

```bash
cat backend/app/services/phased_analysis.py
```

**Document these findings:**
1. What is `run_analysis_for_run_id()`?
2. What phases are executed?
   - Phase 1: Market + Event
   - Phase 2: News pipeline
   - Phase 3: Signal + Report
3. How does each phase update the run document?
4. How are phase statuses updated? ("pending" → "done" | "error")
5. How are errors handled per phase?
6. Does it use the LangGraph or call agents directly?

---

## Task 5: Database Persistence Layer

**Files to read:**
- `backend/app/services/run_snapshot.py`
- `backend/app/db/async_repositories.py`
- `backend/app/db/async_client.py`
- `backend/app/db/models.py`

**Step 1: Read run_snapshot.py**

```bash
cat backend/app/services/run_snapshot.py
```

**Document these findings:**
1. What does `init_run_document_async()` do?
   - What initial fields are set?
   - What is the initial status?
2. What does `persist_run_snapshot_async()` do?
   - How does it extract data from AgentState?
   - What gets stored?
3. What does `update_run_phase_async()` do?
   - How does it update specific phases?

**Step 2: Read async_repositories.py**

```bash
cat backend/app/db/async_repositories.py
```

**Document these findings:**
1. What repository classes exist?
2. What CRUD operations are available?
3. How are queries structured?

**Step 3: Read async_client.py**

```bash
cat backend/app/db/async_client.py
```

**Document these findings:**
1. How is the Motor async client initialized?
2. What database/collection names are used?
3. How is connection pooling handled?

**Step 4: Read models.py**

```bash
cat backend/app/db/models.py
```

**Document these findings:**
1. What is the complete `RunDocument` schema?
2. What is `RunStatus` structure?
3. What nested documents exist? (MarketSnapshot, NewsContext, Signal, etc.)

---

## Task 6: Frontend Polling & Display

**Files to read:**
- `frontend/components/Background.tsx` (polling logic)

**Step 1: Analyze polling useEffect (lines 419-628)**

```bash
# Re-read Background.tsx focusing on the useEffect
cat frontend/components/Background.tsx
```

**Document these findings:**
1. How does the polling loop work?
   - What triggers polling to start?
   - What is the polling interval? (1.5s normal, 3s on error)
   - What stops polling?
2. How does it update `runStatus`?
3. How does it incrementally update `results`?
   - When is `market_snapshot` shown?
   - When is `news_context` shown?
   - When is `signal` shown?
   - When is `report` shown?
4. How does it handle market selection requirement?
5. How does it detect completion? (all phases "done" or "error")

---

## Summary Output

After completing all tasks, create a sequence diagram:

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐     ┌─────────┐
│ Browser │     │ Next.js API │     │   FastAPI   │     │ MongoDB │     │ Agents  │
└────┬────┘     └──────┬──────┘     └──────┬──────┘     └────┬────┘     └────┬────┘
     │                 │                   │                 │               │
     │ POST /analyze/start                 │                 │               │
     │────────────────>│                   │                 │               │
     │                 │ POST /api/analyze/start             │               │
     │                 │──────────────────>│                 │               │
     │                 │                   │ init_run_doc    │               │
     │                 │                   │────────────────>│               │
     │                 │                   │                 │               │
     │                 │                   │ spawn background task           │
     │                 │                   │─────────────────────────────────>
     │                 │   { run_id }      │                 │               │
     │                 │<──────────────────│                 │               │
     │  { run_id }     │                   │                 │               │
     │<────────────────│                   │                 │               │
     │                 │                   │                 │               │
     │ (start polling) │                   │                 │  Phase 1      │
     │                 │                   │                 │<──────────────│
     │ GET /run/{id}   │                   │                 │               │
     │────────────────>│                   │                 │               │
     │                 │ GET /api/run/{id} │                 │               │
     │                 │──────────────────>│                 │               │
     │                 │                   │ find run        │               │
     │                 │                   │────────────────>│               │
     │                 │                   │   run doc       │               │
     │                 │                   │<────────────────│               │
     │                 │   { run, status } │                 │               │
     │                 │<──────────────────│                 │               │
     │ { status: ... } │                   │                 │               │
     │<────────────────│                   │                 │               │
     │                 │                   │                 │               │
     │ (repeat polling until all phases done)               │               │
```

Document:
1. Request lifecycle timing
2. Where data transformations occur
3. Error handling at each layer
4. How incremental updates work
