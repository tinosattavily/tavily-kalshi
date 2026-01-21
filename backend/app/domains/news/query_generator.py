# app/domains/news/query_generator.py
"""Search query generation for news fetching."""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional, TypedDict

from app.config import get_logger

logger = get_logger(__name__)

try:
    import openai
except ImportError:
    openai = None


class TavilyQuerySpec(TypedDict, total=False):
    """Structured specification for a single Tavily query."""

    name: str
    query: str
    max_results: int
    search_depth: Literal["basic", "advanced"]
    timeframe: Optional[str]
    notes: Optional[str]


SYSTEM_PROMPT = """You are a research director for a prediction-market analysis system.

Your job: turn a Polymarket market description into 1–3 structured web search
queries for Tavily that help determine the TRUE probability of the YES outcome.

Constraints:
- Focus ONLY on information that affects whether the market resolves YES or NO.
- Disambiguate ambiguous entities (e.g., "Biden" → "Joe Biden, President of the United States").
- Tune queries to the given analysis horizon:
  * "intraday": emphasize latest developments, breaking news, live events.
  * "24h": mix of latest updates + near-term catalysts.
  * "resolution": structural factors, long-term drivers, track record, polls, fundamentals.

Return ONLY a JSON object with a "queries" field containing a list of 1–3 query objects.
Each query object must have:
- "name" (short slug, e.g. "latest_developments")
- "query" (full natural-language query string)
- "max_results" (integer between 5 and 12)
- "search_depth" ("basic" or "advanced")
- "timeframe" (optional; "24h" / "7d" / "30d" or empty string)

Only output valid JSON. No extra text or prose."""


def build_prompt_from_context(
    market_snapshot: Dict[str, Any],
    event_context: Dict[str, Any],
    event_data: Dict[str, Any],
    horizon: str = "24h",
    strategy_preset: str = "Balanced",
) -> str:
    """Build a prompt for query generation from context data.

    Args:
        market_snapshot: Market data dict
        event_context: Event context dict
        event_data: Event data dict
        horizon: Analysis horizon (intraday, 24h, resolution)
        strategy_preset: Strategy preset name

    Returns:
        Formatted prompt string
    """
    question = market_snapshot.get("question") or ""
    outcomes = market_snapshot.get("outcomes") or []
    category = event_context.get("category") or event_data.get("category") or ""
    region = event_context.get("region") or ""
    resolution_criteria = event_context.get("resolution_criteria") or ""

    return f"""Market snapshot:
- Question: {question}
- Outcomes: {outcomes}
- Category: {category}
- Region: {region}
- Resolution criteria: {resolution_criteria}

Analysis horizon: {horizon}
Strategy preset: {strategy_preset}

Generate 1–3 Tavily query specifications optimized for this market and horizon.""".strip()


def parse_tavily_specs(raw_json: dict) -> List[TavilyQuerySpec]:
    """Convert raw LLM JSON into a list of TavilyQuerySpec.

    Args:
        raw_json: Raw JSON dict from LLM response

    Returns:
        List of validated TavilyQuerySpec dicts
    """
    queries: List[TavilyQuerySpec] = []

    raw_queries = raw_json.get("queries", [])
    if not isinstance(raw_queries, list):
        logger.warning(
            "LLM response 'queries' field is not a list",
            raw_type=type(raw_queries).__name__,
        )
        return queries

    for item in raw_queries:
        if not isinstance(item, dict):
            logger.warning("Skipping invalid query item", item_type=type(item).__name__)
            continue

        name = item.get("name") or "news"
        query = item.get("query") or ""
        if not query:
            logger.warning("Skipping query with empty query string", name=name)
            continue

        # Validate max_results
        max_results_raw = item.get("max_results")
        try:
            max_results = int(max_results_raw) if max_results_raw is not None else 8
            max_results = max(5, min(12, max_results))
        except (ValueError, TypeError):
            logger.warning("Invalid max_results, using default", max_results_raw=max_results_raw)
            max_results = 8

        # Validate search_depth
        search_depth_raw = item.get("search_depth", "basic")
        if search_depth_raw not in ("basic", "advanced"):
            logger.warning("Invalid search_depth, using 'basic'", search_depth=search_depth_raw)
            search_depth: Literal["basic", "advanced"] = "basic"
        else:
            search_depth = search_depth_raw

        spec: TavilyQuerySpec = {
            "name": name,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }

        # Optional fields
        timeframe = item.get("timeframe")
        if timeframe and isinstance(timeframe, str):
            spec["timeframe"] = timeframe

        notes = item.get("notes")
        if notes and isinstance(notes, str):
            spec["notes"] = notes

        queries.append(spec)

    return queries


def build_fallback_query(
    event_title: Optional[str] = None,
    market_question: Optional[str] = None,
) -> str:
    """Build a single fallback query from event/market context.

    Args:
        event_title: Event title
        market_question: Market question

    Returns:
        Fallback query string
    """
    base = (event_title or market_question or "key event").replace("?", "")
    return f"Latest news and developments relevant to: {base}"


def build_fallback_queries(
    event_title: Optional[str] = None,
    market_question: Optional[str] = None,
) -> List[str]:
    """Construct a small set of fallback queries from event/market context.

    Args:
        event_title: Event title
        market_question: Market question

    Returns:
        List of fallback query strings
    """
    base = (event_title or market_question or "key event").replace("?", "")
    queries = [
        f"{base} latest news",
        f"{base} market expectations",
    ]

    lower = base.lower()
    if "fed" in lower or "interest rate" in lower:
        queries.append(f"{base} inflation data and FOMC guidance")
    if "election" in lower or "presidential" in lower:
        queries.append(f"{base} polling averages and latest polls")

    # Deduplicate
    seen = set()
    uniq: List[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            uniq.append(q)
    return uniq


async def generate_search_queries(
    market_snapshot: Dict[str, Any],
    event_context: Dict[str, Any],
    event_data: Optional[Dict[str, Any]] = None,
    horizon: str = "24h",
    strategy_preset: str = "Balanced",
    slug: str = "unknown",
) -> List[TavilyQuerySpec]:
    """Generate search queries using LLM.

    Args:
        market_snapshot: Market data dict
        event_context: Event context dict
        event_data: Event data dict
        horizon: Analysis horizon
        strategy_preset: Strategy preset name
        slug: Market slug for caching

    Returns:
        List of TavilyQuerySpec dicts, or empty list on failure
    """
    from app.infrastructure.http.cache import openai_cache
    from app.infrastructure.http.resilience import openai_circuit
    from app.infrastructure.llm import get_openai_client

    if openai is None:
        logger.warning("OpenAI not available")
        return []

    openai_client = get_openai_client()
    if not openai_client.api_key:
        logger.warning("OPENAI_API_KEY not configured")
        return []

    # Build prompt
    user_prompt = build_prompt_from_context(
        market_snapshot,
        event_context,
        event_data or {},
        horizon,
        strategy_preset,
    )

    # Create cache key
    event_slug = (event_data or {}).get("slug", "")
    cache_input = f"{SYSTEM_PROMPT}:{user_prompt}:{horizon}:{slug}:{event_slug}:{strategy_preset}"
    cache_key = f"openai:tavily_queries:{hashlib.md5(cache_input.encode()).hexdigest()}"

    # Try cache first
    cached_result = openai_cache.get(cache_key)
    if cached_result is not None:
        logger.debug("Cache hit for Tavily query generation")
        return parse_tavily_specs(cached_result)

    # Check circuit breaker
    if not openai_circuit.can_attempt():
        logger.warning("OpenAI circuit breaker is OPEN")
        return []

    # Call OpenAI
    try:
        def _call_openai() -> Dict[str, Any]:
            if openai_client.client and openai_client._use_new_api:
                completion = openai_client.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                )
                raw_content = completion.choices[0].message.content
            else:
                completion = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                )
                raw_content = completion.choices[0].message["content"]

            if not raw_content:
                raise ValueError("OpenAI returned empty response")

            # Clean up response
            content_cleaned = raw_content.strip()
            if content_cleaned.startswith("```json"):
                content_cleaned = content_cleaned[7:]
                if content_cleaned.endswith("```"):
                    content_cleaned = content_cleaned[:-3]
                content_cleaned = content_cleaned.strip()
            elif content_cleaned.startswith("```"):
                content_cleaned = content_cleaned[3:]
                if content_cleaned.endswith("```"):
                    content_cleaned = content_cleaned[:-3]
                content_cleaned = content_cleaned.strip()

            return json.loads(content_cleaned)

        loop = asyncio.get_event_loop()
        raw_response = await loop.run_in_executor(None, _call_openai)
        openai_circuit.record_success()

        # Cache successful result
        openai_cache.set(cache_key, raw_response)
        logger.debug("OpenAI API call successful and cached")

        return parse_tavily_specs(raw_response)

    except Exception as exc:
        openai_circuit.record_failure()
        logger.warning("Failed to generate search queries", error=str(exc))
        return []
