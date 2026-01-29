# Part 1: LangGraph Agent System Exploration

> **For Claude:** This is a READ-ONLY exploration plan. Do not modify any files. Document findings as you go.

**Goal:** Develop complete understanding of the 8-agent LangGraph pipeline, shared state, and orchestration logic.

**Context:** Prophily uses LangGraph to orchestrate 8 specialized agents that analyze Polymarket prediction markets. Each agent reads from and writes to a shared `AgentState` TypedDict.

**Deliverable:** After completing this plan, produce a summary document explaining how the agent system works.

---

## Task 1: Understand Agent Orchestration

**Files to read:**
- `backend/app/agents/graph.py`
- `backend/app/agents/state.py`

**Step 1: Read graph.py**

```bash
# Read the orchestration file
cat backend/app/agents/graph.py
```

**Document these findings:**
1. What is the execution order of agents?
2. How does `build_analysis_graph()` wire the StateGraph?
3. What does `route_after_market()` do? When does it return "end" vs "event_agent"?
4. Which agents are optional and how are they skipped?
5. How is the graph compiled and invoked?

**Step 2: Read state.py**

```bash
cat backend/app/agents/state.py
```

**Document these findings:**
1. List all fields in `AgentState` TypedDict
2. Which fields are inputs vs outputs?
3. What imported types does it use from `db/models.py`?
4. What is `TracePayload` used for?

---

## Task 2: Analyze Market Agent (First Agent)

**Files to read:**
- `backend/app/agents/market_agent.py`
- `backend/app/core/polymarket_utils.py`
- `backend/app/core/market_transformer.py`
- `backend/app/core/market_selector.py`

**Step 1: Read market_agent.py**

```bash
cat backend/app/agents/market_agent.py
```

**Document these findings:**
1. What is the purpose of `run_market_agent()`?
2. How does it extract the slug from the URL?
3. How does it handle single market vs multi-market events?
4. When does it set `requires_market_selection = True`?
5. What data does it populate in state? (`market`, `market_snapshot`, `event`)
6. How does it fetch order book data?

**Step 2: Read polymarket_utils.py**

```bash
cat backend/app/core/polymarket_utils.py
```

**Document these findings:**
1. What is `extract_slug_from_url()` regex pattern?
2. How does `get_event_and_markets_by_slug()` work?
3. What Polymarket API endpoints are called?
4. How is caching implemented?
5. How is `fetch_order_book_async()` implemented?

**Step 3: Read market_transformer.py**

```bash
cat backend/app/core/market_transformer.py
```

**Document these findings:**
1. What does `build_market_options()` return?
2. What does `build_market_snapshot()` construct?
3. How are prices extracted from API response?

**Step 4: Read market_selector.py**

```bash
cat backend/app/core/market_selector.py
```

**Document these findings:**
1. What logic determines if user selection is needed?
2. How does `find_market_by_slug()` work?

---

## Task 3: Analyze Event Agent

**Files to read:**
- `backend/app/agents/event_agent.py`

**Step 1: Read event_agent.py**

```bash
cat backend/app/agents/event_agent.py
```

**Document these findings:**
1. What is the purpose of `run_event_agent()`?
2. What metadata does it extract?
3. How does it populate `event_context`?
4. Does it make any API calls or just transform existing data?
5. What is `event_description` used for?

---

## Task 4: Analyze News Pipeline (3 Agents)

**Files to read:**
- `backend/app/agents/tavily_prompt_agent.py`
- `backend/app/agents/news_agent.py`
- `backend/app/agents/news_summary_agent.py`
- `backend/app/services/tavily_client.py`

**Step 1: Read tavily_prompt_agent.py**

```bash
cat backend/app/agents/tavily_prompt_agent.py
```

**Document these findings:**
1. What is `TavilyQuerySpec`?
2. How does it generate search queries from event context?
3. What OpenAI prompt does it use?
4. How many queries does it generate?
5. What gets stored in `state["tavily_queries"]`?

**Step 2: Read news_agent.py**

```bash
cat backend/app/agents/news_agent.py
```

**Document these findings:**
1. How does it execute Tavily searches?
2. How are articles extracted and normalized?
3. What is the `NewsArticle` structure?
4. How does it handle errors per query?
5. What limits apply (max_articles, max_articles_per_query)?

**Step 3: Read news_summary_agent.py**

```bash
cat backend/app/agents/news_summary_agent.py
```

**Document these findings:**
1. How does it summarize articles?
2. What OpenAI prompt does it use?
3. Does it perform sentiment analysis?
4. What gets stored in `news_context.summary`?

**Step 4: Read tavily_client.py**

```bash
cat backend/app/services/tavily_client.py
```

**Document these findings:**
1. How is the Tavily client initialized?
2. What search parameters are used?
3. Is there caching or rate limiting?

---

## Task 5: Analyze Signal Generation (3 Agents)

**Files to read:**
- `backend/app/agents/prob_agent.py`
- `backend/app/agents/strategy_agent.py`
- `backend/app/agents/report_agent.py`

**Step 1: Read prob_agent.py**

```bash
cat backend/app/agents/prob_agent.py
```

**Document these findings:**
1. How does it generate probability estimates?
2. What inputs does it use (market data, news)?
3. What OpenAI prompt does it use?
4. How is the `Signal` structured?
   - `direction`: "up" | "down" | "flat"
   - `model_prob`: float (probability estimate)
   - `confidence`: "low" | "medium" | "high"
   - `rationale`: string
5. How does it determine confidence level?

**Step 2: Read strategy_agent.py**

```bash
cat backend/app/agents/strategy_agent.py
```

**Document these findings:**
1. How is edge calculated?
   - Formula: `(model_prob - market_price) / (1 - market_price)`?
2. How is Kelly Criterion applied?
3. What determines BUY vs SELL vs HOLD?
4. What is `toy_kelly_fraction`?
5. How do `strategy_params` affect decisions?
   - `min_edge_pct`
   - `min_confidence`
   - `max_kelly_fraction`

**Step 3: Read report_agent.py**

```bash
cat backend/app/agents/report_agent.py
```

**Document these findings:**
1. What OpenAI prompt generates the report?
2. What is the `ReportBlock` structure?
   - `headline`
   - `thesis`
   - `bull_case`
   - `bear_case`
   - `key_risks`
   - `execution_notes`
3. How does it synthesize all prior analysis?

---

## Summary Output

After completing all tasks, write a summary that answers:

1. **Agent Pipeline:** What is the exact execution order?
2. **Data Flow:** What does each agent read and write to state?
3. **Optional Agents:** Which can be skipped and how?
4. **External Calls:** Which agents call external APIs (Polymarket, Tavily, OpenAI)?
5. **Key Decisions:** How are trading signals and Kelly sizing calculated?

Create a diagram showing:
```
[Input: market_url]
     ↓
[market_agent] → market_snapshot, event
     ↓ (conditional)
[event_agent] → event_context
     ↓
[tavily_prompt_agent] → tavily_queries (optional)
     ↓
[news_agent] → news_context.articles
     ↓
[news_summary_agent] → news_context.summary (optional)
     ↓
[prob_agent] → signal
     ↓
[strategy_agent] → decision
     ↓
[report_agent] → report
     ↓
[Output: complete AgentState]
```
