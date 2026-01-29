"""Tavily prompt agent - generates structured Tavily query specifications using LLM."""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

from app.agents.state import AgentState, TavilyQuerySpec
from app.core.logging_config import get_logger
from app.services.openai_client import get_openai_client

logger = get_logger(__name__)

try:
    import openai
except ImportError:  # pragma: no cover - handled at runtime
    openai = None  # type: ignore[assignment]


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


def build_prompt_from_state(state: AgentState) -> str:
    """Render a compact text prompt for the LLM based on current agent state."""
    market = state.get("market_snapshot", {}) or {}
    event = state.get("event_context", {}) or {}
    event_doc = state.get("event", {}) or {}

    question = market.get("question") or ""
    outcomes = market.get("outcomes") or []
    category = event.get("category") or event_doc.get("category") or ""
    region = event.get("region") or ""
    resolution_criteria = event.get("resolution_criteria") or ""

    horizon = state.get("horizon") or "24h"
    strategy_preset = state.get("strategy_preset") or "Balanced"

    return f"""Market snapshot:
- Question: {question}
- Outcomes: {outcomes}
- Category: {category}
- Region: {region}
- Resolution criteria: {resolution_criteria}

Analysis horizon: {horizon}
Strategy preset: {strategy_preset}

Generate 1–3 Tavily query specifications optimized for this market and horizon.""".strip()


def _parse_max_results(value: Any) -> int:
    """Parse and clamp max_results to valid range (5-12), defaulting to 8."""
    if value is None:
        return 8
    try:
        return max(5, min(12, int(value)))
    except (ValueError, TypeError):
        return 8


def _parse_search_depth(value: Any) -> Literal["basic", "advanced"]:
    """Parse search_depth, defaulting to 'basic' if invalid."""
    if value in ("basic", "advanced"):
        return value
    return "basic"


def parse_tavily_specs(raw_json: dict[str, Any]) -> list[TavilyQuerySpec]:
    """Convert raw LLM JSON into a list of TavilyQuerySpec, with light validation."""
    raw_queries = raw_json.get("queries", [])
    if not isinstance(raw_queries, list):
        logger.warning(
            "LLM response 'queries' field is not a list",
            raw_type=type(raw_queries).__name__,
        )
        return []

    queries: list[TavilyQuerySpec] = []
    for item in raw_queries:
        if not isinstance(item, dict):
            logger.warning("Skipping invalid query item", item_type=type(item).__name__)
            continue

        query = item.get("query") or ""
        if not query:
            logger.warning("Skipping query with empty query string", name=item.get("name"))
            continue

        spec: TavilyQuerySpec = {
            "name": item.get("name") or "news",
            "query": query,
            "max_results": _parse_max_results(item.get("max_results")),
            "search_depth": _parse_search_depth(item.get("search_depth")),
        }

        timeframe = item.get("timeframe")
        if isinstance(timeframe, str) and timeframe:
            spec["timeframe"] = timeframe

        notes = item.get("notes")
        if isinstance(notes, str) and notes:
            spec["notes"] = notes

        queries.append(spec)

    return queries


def _strip_markdown_code_blocks(content: str) -> str:
    """Remove markdown code block delimiters from LLM response."""
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def _generate_tavily_queries_sync(
    system_prompt: str,
    user_prompt: str,
    cache_key: str,
) -> dict[str, Any]:
    """Generate Tavily query specifications using OpenAI (sync method)."""
    if openai is None:
        logger.warning("OpenAI not available")
        raise RuntimeError("OpenAI is not available")

    openai_client = get_openai_client()
    if not openai_client.api_key:
        logger.warning("OPENAI_API_KEY not configured")
        raise RuntimeError("OpenAI API key not configured")

    from app.core.cache import openai_cache
    from app.core.resilience import openai_circuit

    cached_result = openai_cache.get(cache_key)
    if cached_result is not None:
        logger.debug("Cache hit for Tavily query generation")
        return cached_result

    if not openai_circuit.can_attempt():
        logger.warning("OpenAI circuit breaker is OPEN")
        raise RuntimeError("OpenAI circuit breaker is OPEN")

    raw_content = None
    try:
        logger.debug("Cache miss - calling OpenAI API for Tavily queries")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if openai_client.client and openai_client._use_new_api:
            completion = openai_client.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
            )
            raw_content = completion.choices[0].message.content
        else:
            completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
            )
            raw_content = completion.choices[0].message["content"]

        if not raw_content:
            raise ValueError("OpenAI returned empty response")

        content_cleaned = _strip_markdown_code_blocks(raw_content)
        data = json.loads(content_cleaned)
        openai_circuit.record_success()
        openai_cache.set(cache_key, data)
        logger.debug("OpenAI API call successful and cached")
        return data
    except json.JSONDecodeError as exc:
        openai_circuit.record_failure()
        content_preview = raw_content[:200] if raw_content else "<no content>"
        logger.warning(
            "Failed to parse OpenAI JSON response",
            error=str(exc),
            raw_content=content_preview,
        )
        raise ValueError(f"Invalid JSON from OpenAI: {exc}") from exc
    except Exception as exc:
        openai_circuit.record_failure()
        logger.warning("OpenAI call failed", error=str(exc), exc_info=True)
        raise


def _build_cache_key(user_prompt: str, state: AgentState) -> str:
    """Build a cache key for Tavily query generation based on state parameters."""
    horizon = state.get("horizon") or "24h"
    market_slug = state.get("slug") or "unknown"
    event_slug = state.get("event", {}).get("slug") or ""
    strategy_preset = state.get("strategy_preset") or "Balanced"

    cache_input = (
        f"{SYSTEM_PROMPT}:{user_prompt}:{horizon}:{market_slug}:{event_slug}:{strategy_preset}"
    )
    return f"openai:tavily_queries:{hashlib.md5(cache_input.encode()).hexdigest()}"


async def run_tavily_prompt_agent(state: AgentState) -> AgentState:
    """Generate structured Tavily query specifications using an LLM.

    Inputs (from AgentState):
      - market_snapshot
      - event_context
      - horizon
      - strategy_preset
      - slug

    Outputs (into AgentState):
      - tavily_queries: list[TavilyQuerySpec] (only set on success)
    """
    if state.get("tavily_queries"):
        logger.debug("tavily_queries already present, skipping generation")
        return state

    market_slug = state.get("slug") or "unknown"
    horizon = state.get("horizon") or "24h"
    user_prompt = build_prompt_from_state(state)
    cache_key = _build_cache_key(user_prompt, state)

    try:
        loop = asyncio.get_event_loop()
        raw_response = await loop.run_in_executor(
            None,
            _generate_tavily_queries_sync,
            SYSTEM_PROMPT,
            user_prompt,
            cache_key,
        )

        tavily_queries = parse_tavily_specs(raw_response)

        if not tavily_queries:
            logger.warning(
                "LLM generated no valid queries, News Agent will use fallback",
                market_slug=market_slug,
                horizon=horizon,
            )
            return state

        logger.info(
            "tavily_queries_generated",
            market_slug=market_slug,
            horizon=horizon,
            num_queries=len(tavily_queries),
            first_query=tavily_queries[0]["query"][:180],
            query_names=[q["name"] for q in tavily_queries],
        )

        state["tavily_queries"] = tavily_queries
        return state

    except Exception as exc:
        logger.warning(
            "tavily_prompt_agent_failed",
            error=str(exc),
            market_slug=market_slug,
            horizon=horizon,
            error_type=type(exc).__name__,
            exc_info=not isinstance(exc, (RuntimeError, ValueError, KeyError)),
        )
        return state
