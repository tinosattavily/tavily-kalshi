# Part 3: External API Integrations - Findings

> **Exploration completed:** 2026-01-28

This document captures the findings from exploring Prophily's external API integrations: Polymarket, Tavily, and OpenAI.

---

## Task 1: Polymarket API Integration

### PolymarketClient Class (`backend/app/services/polymarket_client.py`)

The `PolymarketClient` is a thin wrapper around utility functions, providing a clean async interface:

**Methods:**
| Method | Arguments | Returns | Purpose |
|--------|-----------|---------|---------|
| `get_event_and_markets(slug)` | `slug: str` | `Tuple[Optional[Dict], List[Dict]]` | Fetches event data and associated markets |
| `fetch_order_book(token_id)` | `token_id: str` | `Dict[str, Any]` | Fetches CLOB order book |
| `fetch_json(url, params)` | `url: str`, `params: Optional[Dict]` | `Any` | Generic JSON fetcher |

**Singleton Pattern:**
```python
_polymarket_client: Optional[PolymarketClient] = None

def get_polymarket_client() -> PolymarketClient:
    global _polymarket_client
    if _polymarket_client is None:
        _polymarket_client = PolymarketClient()
    return _polymarket_client
```

### URL Parsing (`backend/app/core/polymarket_utils.py:34-49`)

```python
def extract_slug_from_url(url: str | None) -> Optional[str]:
```

**Logic:**
1. Strip scheme (`https?://`)
2. Remove query params and fragments (`[?#]`)
3. Split path and return last segment

**Supported URL formats:**
- `https://polymarket.com/event/some-event-slug`
- `polymarket.com/event/some-event-slug`
- `/event/some-event-slug`
- Just `some-event-slug` (invalid - returns None)

### Gamma API Endpoints

**Base URL:** `https://gamma-api.polymarket.com`

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/events?slug={slug}` | GET | Get event with embedded markets | `{data: [Event]}` or `[Event]` |
| `/markets?slug={slug}` | GET | Get single market (fallback) | `{data: [Market]}` or `[Market]` |

**Response Handling:**
- Handles both array response and `{data: [...]}` format
- Uses Pydantic models (`Event`, `Market`) for type-safe deserialization
- Falls back to raw dict if Pydantic validation fails

### CLOB API Endpoints

**Base URL:** `https://clob.polymarket.com`

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/book?token_id={id}` | GET | Get order book | `{bids: [], asks: []}` |

**Order Book Structure:**
```python
{
    "bids": [{"price": float, "size": float}, ...],  # Sorted descending
    "asks": [{"price": float, "size": float}, ...],  # Sorted ascending
    "best_bid": float | None,  # Highest bid price
    "best_ask": float | None   # Lowest ask price
}
```

### Caching Implementation (`backend/app/core/cache.py`)

**Cache Types:**
1. **TTLCache** - In-memory with TTL expiration
2. **RedisCache** - Redis-backed with automatic fallback to in-memory

**Global Cache Instances:**
| Cache | TTL | Purpose |
|-------|-----|---------|
| `polymarket_cache` | 30 seconds | Market data (frequently changing) |
| `tavily_cache` | 5 minutes (300s) | News search results |
| `openai_cache` | 10 minutes (600s) | AI responses |

**Cache Key Format:**
```python
cache_key = f"polymarket:{url}:{hash(str(params))}"
```

**Redis Configuration:**
- Supports URL-based or parameter-based connection
- Connection timeout: 5 seconds
- Automatic reconnection with fallback

---

## Task 2: Resilience Patterns (`backend/app/core/resilience.py`)

### Circuit Breaker Implementation

**Custom implementation** (not using pybreaker library).

**States:**
| State | Behavior |
|-------|----------|
| `CLOSED` | Normal operation, requests pass through |
| `OPEN` | Failing, rejects all requests immediately |
| `HALF_OPEN` | Testing recovery, allows limited requests |

**Configuration per Service:**
| Circuit | Failure Threshold | Success Threshold | Timeout |
|---------|-------------------|-------------------|---------|
| `polymarket_circuit` | 5 failures | 2 successes | 30 seconds |
| `tavily_circuit` | 5 failures | 2 successes | 60 seconds |
| `openai_circuit` | 3 failures | 2 successes | 120 seconds |

**Key Methods:**
```python
circuit.can_attempt() -> bool    # Check if request allowed
circuit.record_success()         # Mark successful request
circuit.record_failure()         # Mark failed request
circuit.reset()                  # Manually reset to CLOSED
```

### Retry Logic

**Uses `tenacity` library for synchronous retries:**
```python
@with_retry(max_attempts=3, base_delay=1.0, max_delay=60.0, exceptions=(Exception,))
def some_function():
    ...
```

**Custom async retry helper:**
```python
result = await with_async_retry(
    func,
    max_attempts=3,
    base_delay=1.0,
    max_delay=60.0,
    **kwargs
)
```

**Backoff Strategy:** Exponential with formula `min(base_delay * 2^(attempt-1), max_delay)`

**Decorators Available:**
| Decorator | Purpose |
|-----------|---------|
| `@with_retry(...)` | Sync retry with exponential backoff |
| `@with_circuit_breaker(circuit)` | Circuit breaker protection |

---

## Task 3: Tavily API Integration

### Client Setup (`backend/app/services/tavily_client.py`)

**Implementation:** Raw HTTP with `aiohttp` (not official Tavily SDK)

**Configuration:**
- API URL: `https://api.tavily.com/search`
- API Key: `TAVILY_API_KEY` environment variable
- Timeout: 20 seconds

### Search API

**Request Payload:**
```python
{
    "api_key": TAVILY_API_KEY,
    "query": query,
    "max_results": max_results,  # Default: 5
    "include_answer": True,
    "include_raw_content": False
}
```

**Note:** `search_depth` parameter is included in function signature for future compatibility but is not currently supported by Tavily API.

**Response Processing:**
Uses `TavilySearchResult.from_api_response(data)` to normalize response.

### Pydantic Models (`backend/app/schemas/tavily.py`)

**TavilyRawArticle** - Raw API response:
| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Article title |
| `url` | str | Article URL |
| `content` | Optional[str] | Full content |
| `score` | Optional[float] | Relevance score (0-1) |
| `published_date` | Optional[str] | Publication date |
| `source` | Optional[str] | Source domain |
| `image` | Optional[str] | Image URL |

**TavilyArticle** - Processed/normalized:
| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Article title |
| `url` | str | Article URL |
| `source` | str | Extracted from URL if not provided |
| `published_at` | Optional[str] | ISO date string |
| `snippet` | Optional[str] | Truncated content (240 chars) |
| `content` | Optional[str] | Full content |
| `score` | Optional[float] | Relevance score |
| `sentiment` | Optional[str] | Added by sentiment analyzer |

**TavilySearchResult** - Complete result:
| Field | Type | Description |
|-------|------|-------------|
| `answer` | str | AI-generated summary |
| `articles` | List[TavilyArticle] | Processed articles |
| `query` | Optional[str] | Original query |
| `response_time` | Optional[float] | API response time |

### Error Handling

**Special Handling for HTTP 432:**
```python
if response.status == 432:
    raise ValueError(
        f"Tavily API error 432: {error_msg}. "
        "This usually indicates an invalid API key, expired subscription, "
        "rate limit exceeded, or account issue."
    )
```

**Retry Configuration:**
- Max attempts: 3
- Base delay: 1.0 second
- Max delay: 20.0 seconds

**Graceful Degradation:**
- Returns `{"answer": "", "articles": []}` on failure
- Doesn't crash the pipeline

---

## Task 4: OpenAI API Integration

### Client Setup (`backend/app/services/openai_client.py`)

**SDK:** Official OpenAI SDK (supports both v0.x and v1.0+ APIs)

**Auto-detection:**
```python
try:
    from openai import OpenAI
    self.client = OpenAI(api_key=self.api_key)
    self._use_new_api = True
except (ImportError, AttributeError):
    openai.api_key = self.api_key
    self._use_new_api = False
```

**Configuration:**
| Setting | Value |
|---------|-------|
| API Key | `OPENAI_API_KEY` |
| Model | `gpt-4o-mini` |
| Temperature (signals) | 0.2 |
| Temperature (summaries) | 0.3 |

### API Methods

**1. `generate_signal()`** - Trading signal generation
```python
async def generate_signal(
    event_title: str,
    market_question: str,
    yes_price: float,
    news_summary: str,
    top_headlines: str,
    tag_label: str = "",
) -> Dict[str, Any]
```

**2. `summarize_news_with_sentiment()`** - News summarization
```python
async def summarize_news_with_sentiment(
    articles: List[Dict[str, Any]],
    event_title: str,
    market_question: str,
) -> str
```

### Probability Agent Prompts (`backend/app/agents/prob_agent.py`)

**System Prompt:**
> "You are a careful prediction market analyst. Given a Polymarket market, its current YES price and recent news, you estimate the TRUE probability that YES is correct over the next few days. You must respond ONLY with a single JSON object."

**User Prompt Includes:**
- Event title, market question, bracket/label
- Current YES price and implied probability
- News summary from Tavily
- Top 3 headlines

**Expected JSON Response:**
```json
{
    "model_prob_abs": 0.65,
    "direction": "up",
    "expected_delta_range": [0.02, 0.08],
    "confidence": "medium",
    "rationale": "Recent news suggests..."
}
```

### Report Agent Prompts (`backend/app/agents/report_agent.py`)

**System Prompt:**
> "You are writing a concise trade note for a prediction market. You will receive structured data about the market, model signal, news, and recommended action. Return ONLY a valid JSON object with the exact fields specified."

**Inputs Provided:**
- Market snapshot (question, YES price, implied probability)
- Model signal (probability, edge, Kelly, confidence, rationale)
- Recommended action (action, size, TP, SL)
- News context (summary, sentiment distribution)

**Expected JSON Response:**
```json
{
    "headline": "One sentence summary",
    "thesis": "3-5 sentences explaining the trade",
    "bull_case": ["bullet 1", "bullet 2", "bullet 3"],
    "bear_case": ["bullet 1", "bullet 2", "bullet 3"],
    "key_risks": ["risk 1", "risk 2", "risk 3"],
    "execution_notes": "2-3 sentences on sizing and execution"
}
```

**Fallback Template:**
If OpenAI fails, `_generate_fallback_report()` creates a basic template with:
- Computed headline from signal values
- Basic thesis with probability comparison
- Generic bull/bear cases
- Standard key risks

---

## Task 5: Sentiment Analysis (`backend/app/core/sentiment_analyzer.py`)

### Implementation

**Type:** Local keyword-based analysis (no external API)

**Sentiment Labels:**
- `"bullish"` - Supports YES outcome
- `"bearish"` - Supports NO outcome
- `"neutral"` - No clear direction

### Analysis Logic

**1. Keyword Matching:**

**Bullish Patterns (~60 keywords):**
- Price movement: increase, rise, up, higher, surge, rally, soar, jump, climb
- Positive sentiment: positive, optimistic, strong, beat, exceed, outperform
- Approval: approve, pass, support, favor, win, victory
- Dovish monetary: cut rates, dovish, stimulus, easing, accommodative

**Bearish Patterns (~80 keywords):**
- Price movement: decrease, fall, down, lower, decline, drop, plunge, crash
- Negative sentiment: negative, pessimistic, weak, miss, underperform, disappoint
- Rejection: reject, fail, oppose, against, loss, defeat
- Hawkish monetary: raise rates, hawkish, tighten, restrictive

**2. Negation Handling:**
Detects negation words within 20 characters of sentiment keywords and flips the sentiment.

**3. Context-Aware Adjustments:**
- If market asks about "increase" → boost bullish for increase-related content
- If market asks about "cut" or "decrease" → boost bullish for cut-related content
- Fed/rate markets → special handling for dovish/hawkish language

**4. Signal Direction Consideration:**
- `signal_direction == "up"` → slight bullish boost
- `signal_direction == "down"` → slight bearish boost

**5. Price Position Weighting:**
- `yes_price < 0.1` → 1.2x multiplier for bullish counts
- `yes_price > 0.9` → 1.2x multiplier for bearish counts

### Functions

```python
def analyze_article_sentiment(
    article: Dict[str, Any],
    market_question: str,
    yes_price: float,
    signal_direction: Optional[str] = None,
    outcomes: Optional[list[str]] = None,
) -> Sentiment  # "bullish" | "bearish" | "neutral"

def analyze_articles_sentiment(
    articles: list[Dict[str, Any]],
    ...
) -> list[Dict[str, Any]]  # Returns articles with sentiment field added
```

---

## Summary: API Reference Tables

### Polymarket APIs

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `gamma-api.polymarket.com/events?slug=X` | GET | Get event + markets | Event with markets array |
| `gamma-api.polymarket.com/markets?slug=X` | GET | Get single market | Market object |
| `clob.polymarket.com/book?token_id=X` | GET | Get order book | `{bids, asks, best_bid, best_ask}` |

### Tavily APIs

| Endpoint | Method | Purpose | Key Params |
|----------|--------|---------|------------|
| `api.tavily.com/search` | POST | Search news | `query`, `max_results`, `include_answer` |

### OpenAI APIs

| Endpoint | Method | Purpose | Model |
|----------|--------|---------|-------|
| `/chat/completions` | POST | Generate signals & reports | gpt-4o-mini |

### Error Handling Matrix

| API | Error Type | Handling |
|-----|------------|----------|
| Polymarket | Network timeout | Retry 3x with exponential backoff (1s-10s) |
| Polymarket | 404 Not Found | Return `(None, [])` |
| Polymarket | Circuit breaker open | Raise `RuntimeError` |
| Tavily | Rate limit (432) | Detailed error message, return empty |
| Tavily | Network error | Retry 3x (1s-20s), return empty on failure |
| Tavily | Circuit breaker open | Return `{"answer": "", "articles": []}` |
| OpenAI | Rate limit | Circuit breaker opens after 3 failures |
| OpenAI | API error | Retry via circuit breaker, fallback to template |
| OpenAI | Circuit breaker open | Use fallback signal/report |

### Environment Variables

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| `OPENAI_API_KEY` | OpenAI authentication | Yes | None |
| `TAVILY_API_KEY` | Tavily authentication | Yes (soft) | None (returns empty) |
| `REDIS_URL` | Redis cache connection | No | In-memory fallback |
| `REDIS_HOST` | Redis host (alt config) | No | None |
| `REDIS_PORT` | Redis port | No | 6379 |
| `REDIS_DB` | Redis database | No | 0 |
| `REDIS_PASSWORD` | Redis password | No | None |

### Cache Configuration

| Cache | TTL | Used By |
|-------|-----|---------|
| `polymarket_cache` | 30 seconds | Market data fetches |
| `tavily_cache` | 300 seconds (5 min) | News searches |
| `openai_cache` | 600 seconds (10 min) | Signal & summary generation |

### Circuit Breaker Configuration

| Service | Failure Threshold | Recovery Timeout | Success Threshold |
|---------|-------------------|------------------|-------------------|
| Polymarket | 5 | 30 seconds | 2 |
| Tavily | 5 | 60 seconds | 2 |
| OpenAI | 3 | 120 seconds | 2 |
