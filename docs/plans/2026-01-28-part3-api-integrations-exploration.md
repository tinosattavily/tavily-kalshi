# Part 3: External API Integrations Exploration

> **For Claude:** This is a READ-ONLY exploration plan. Do not modify any files. Document findings as you go.

**Goal:** Understand how Prophily integrates with external APIs: Polymarket (market data), Tavily (news search), and OpenAI (AI analysis).

**Context:** The system relies on three external services. Each has its own client with caching, retry logic, and error handling.

**Deliverable:** After completing this plan, produce an API reference document showing endpoints, payloads, and error handling for each integration.

---

## Task 1: Polymarket API Integration

**Files to read:**
- `backend/app/services/polymarket_client.py`
- `backend/app/core/polymarket_utils.py`
- `backend/app/core/cache.py`

**Step 1: Read polymarket_client.py**

```bash
cat backend/app/services/polymarket_client.py
```

**Document these findings:**
1. What is the `PolymarketClient` class?
2. What methods does it expose?
   - `get_event_and_markets(slug)`
   - `fetch_order_book(token_id)`
   - `fetch_json(url, params)`
3. How is the singleton pattern implemented?

**Step 2: Read polymarket_utils.py**

```bash
cat backend/app/core/polymarket_utils.py
```

**Document these findings:**

**URL Parsing:**
1. What regex does `extract_slug_from_url()` use?
2. What URL formats are supported?

**Gamma API:**
1. What is the base URL? (`https://gamma-api.polymarket.com`)
2. What endpoints are called?
   - `/events?slug={slug}` - Event with markets
   - `/markets?slug={slug}` - Single market
3. How is caching implemented?
4. What retry logic exists?

**CLOB API:**
1. What is the base URL? (`https://clob.polymarket.com`)
2. What endpoint is called?
   - `/book?token_id={id}` - Order book
3. How is the order book structured?
   - `bids`: array of {price, size}
   - `asks`: array of {price, size}
   - `best_bid`, `best_ask`

**Step 3: Read cache.py**

```bash
cat backend/app/core/cache.py
```

**Document these findings:**
1. What caching strategies are used?
2. Is Redis used or in-memory only?
3. What are the TTL values?
4. How is cache invalidation handled?

---

## Task 2: Resilience Patterns

**Files to read:**
- `backend/app/core/resilience.py`

**Step 1: Read resilience.py**

```bash
cat backend/app/core/resilience.py
```

**Document these findings:**

**Circuit Breaker:**
1. How is the circuit breaker implemented?
2. What library is used? (pybreaker?)
3. What are the failure thresholds?
4. What is `openai_circuit`?
5. How do you reset the circuit breaker?

**Retry Logic:**
1. Is tenacity used for retries?
2. What retry strategies exist?
   - Exponential backoff?
   - Max attempts?
3. What exceptions trigger retries?

**Decorators:**
1. What decorators are available?
   - `@with_circuit_breaker`?
   - `@with_retry`?
2. How are they applied to API calls?

---

## Task 3: Tavily API Integration

**Files to read:**
- `backend/app/services/tavily_client.py`
- `backend/app/schemas/tavily.py`

**Step 1: Read tavily_client.py**

```bash
cat backend/app/services/tavily_client.py
```

**Document these findings:**

**Client Setup:**
1. How is the Tavily client initialized?
2. What API key environment variable is used? (`TAVILY_API_KEY`)
3. Is the official Tavily SDK used or raw HTTP?

**Search API:**
1. What search method is called?
2. What parameters are used?
   - `query`: search query
   - `max_results`: number of results
   - `search_depth`: "basic" or "advanced"?
   - `include_domains`, `exclude_domains`?
3. What does the response look like?

**Response Processing:**
1. How are results extracted?
2. What fields are used from each result?
   - `title`
   - `url`
   - `content` / `snippet`
   - `published_date`
   - `source`

**Error Handling:**
1. What errors can occur?
2. How are rate limits handled?
3. Is there caching for search results?

**Step 2: Read tavily.py schemas**

```bash
cat backend/app/schemas/tavily.py
```

**Document these findings:**
1. What Pydantic models exist?
2. What is the `TavilySearchResult` structure?
3. What is the `TavilySearchResponse` structure?

---

## Task 4: OpenAI API Integration

**Files to read:**
- `backend/app/services/openai_client.py`
- `backend/app/agents/prob_agent.py` (for prompt examples)
- `backend/app/agents/report_agent.py` (for prompt examples)

**Step 1: Read openai_client.py**

```bash
cat backend/app/services/openai_client.py
```

**Document these findings:**

**Client Setup:**
1. How is the OpenAI client initialized?
2. What API key environment variable is used? (`OPENAI_API_KEY`)
3. Is the official OpenAI SDK used?

**Model Configuration:**
1. What model is used? (gpt-4, gpt-4-turbo, gpt-4o?)
2. What temperature is set?
3. What max_tokens is set?

**API Methods:**
1. What wrapper methods exist?
   - `chat_completion()`?
   - `create_completion()`?
2. How are messages structured?

**Error Handling:**
1. How is the circuit breaker integrated?
2. What errors are caught?
   - `RateLimitError`
   - `APIError`
   - `Timeout`
3. How are retries handled?

**Step 2: Analyze prompts in prob_agent.py**

```bash
cat backend/app/agents/prob_agent.py
```

**Document these findings:**
1. What is the system prompt?
2. What is the user prompt structure?
3. How is market data included?
4. How is news context included?
5. How is the response parsed?
6. What JSON structure is expected?

**Step 3: Analyze prompts in report_agent.py**

```bash
cat backend/app/agents/report_agent.py
```

**Document these findings:**
1. What is the system prompt?
2. What inputs are provided?
3. What output structure is requested?
4. How is markdown generated?

---

## Task 5: Sentiment Analysis Integration

**Files to read:**
- `backend/app/core/sentiment_analyzer.py`

**Step 1: Read sentiment_analyzer.py**

```bash
cat backend/app/core/sentiment_analyzer.py
```

**Document these findings:**
1. How is sentiment analysis performed?
2. Is it using OpenAI or a local model?
3. What sentiment labels are used? ("bullish", "bearish", "neutral")
4. How is sentiment attached to articles?
5. Is there aggregate sentiment calculation?

---

## Summary Output

After completing all tasks, create an API reference:

### Polymarket APIs

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `gamma-api.polymarket.com/events?slug=X` | GET | Get event + markets | Event object with markets array |
| `gamma-api.polymarket.com/markets?slug=X` | GET | Get single market | Market object |
| `clob.polymarket.com/book?token_id=X` | GET | Get order book | Bids/asks arrays |

### Tavily APIs

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `api.tavily.com/search` | POST | Search news | Results array |

### OpenAI APIs

| Endpoint | Method | Purpose | Model |
|----------|--------|---------|-------|
| `/chat/completions` | POST | Generate analysis | gpt-4-turbo |

### Error Handling Matrix

| API | Error Type | Handling |
|-----|------------|----------|
| Polymarket | Network timeout | Retry 3x with backoff |
| Polymarket | 404 Not Found | Return empty result |
| Tavily | Rate limit | Retry with backoff |
| OpenAI | Rate limit | Circuit breaker opens |
| OpenAI | API error | Retry 2x, then fail |

### Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `OPENAI_API_KEY` | OpenAI authentication | Yes |
| `TAVILY_API_KEY` | Tavily authentication | Yes |
| `MONGODB_URI` | Database connection | Yes |
| `REDIS_URL` | Cache connection | No |
