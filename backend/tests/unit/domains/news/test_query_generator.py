"""Tests for Tavily Prompt Agent."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.news.query_generator import (
    build_prompt_from_context,
    generate_search_queries,
    parse_tavily_specs,
)
from app.orchestration.state import AgentState


def test_parse_tavily_specs_happy_path():
    """Test parsing valid Tavily query specs from LLM response."""
    raw_json = {
        "queries": [
            {
                "name": "latest_developments",
                "query": "Recent news in the last 24 hours about Fed interest rate decision",
                "max_results": 8,
                "search_depth": "advanced",
                "timeframe": "24h",
            },
            {
                "name": "fundamentals",
                "query": "Background and long-term factors influencing Fed policy",
                "max_results": 10,
                "search_depth": "basic",
            },
        ]
    }

    specs = parse_tavily_specs(raw_json)

    assert len(specs) == 2
    assert specs[0]["name"] == "latest_developments"
    assert specs[0]["query"] == "Recent news in the last 24 hours about Fed interest rate decision"
    assert specs[0]["max_results"] == 8
    assert specs[0]["search_depth"] == "advanced"
    assert specs[0]["timeframe"] == "24h"

    assert specs[1]["name"] == "fundamentals"
    assert specs[1]["max_results"] == 10
    assert specs[1]["search_depth"] == "basic"
    assert "timeframe" not in specs[1]


def test_parse_tavily_specs_invalid_query_skipped():
    """Test that invalid query specs (missing query) are skipped."""
    raw_json = {
        "queries": [
            {
                "name": "valid_query",
                "query": "Valid query string",
                "max_results": 8,
            },
            {
                "name": "invalid_query",
                # Missing "query" field
                "max_results": 8,
            },
        ]
    }

    specs = parse_tavily_specs(raw_json)

    assert len(specs) == 1
    assert specs[0]["name"] == "valid_query"
    assert specs[0]["query"] == "Valid query string"


def test_parse_tavily_specs_defaults_applied():
    """Test that default values are applied for missing fields."""
    raw_json = {
        "queries": [
            {
                "query": "Just a query string",
                # Missing name, max_results, search_depth
            }
        ]
    }

    specs = parse_tavily_specs(raw_json)

    assert len(specs) == 1
    assert specs[0]["name"] == "news"  # Default name
    assert specs[0]["max_results"] == 8  # Default max_results
    assert specs[0]["search_depth"] == "basic"  # Default search_depth


def test_parse_tavily_specs_max_results_clamped():
    """Test that max_results is clamped between 5 and 12."""
    raw_json = {
        "queries": [
            {"query": "Query 1", "max_results": 3},  # Below minimum
            {"query": "Query 2", "max_results": 15},  # Above maximum
            {"query": "Query 3", "max_results": 8},  # Valid
        ]
    }

    specs = parse_tavily_specs(raw_json)

    assert len(specs) == 3
    assert specs[0]["max_results"] == 5  # Clamped to minimum
    assert specs[1]["max_results"] == 12  # Clamped to maximum
    assert specs[2]["max_results"] == 8  # Unchanged


def test_parse_tavily_specs_empty_list():
    """Test parsing empty queries list."""
    raw_json = {"queries": []}
    specs = parse_tavily_specs(raw_json)
    assert len(specs) == 0


def test_parse_tavily_specs_missing_queries_field():
    """Test parsing response with missing queries field."""
    raw_json = {}
    specs = parse_tavily_specs(raw_json)
    assert len(specs) == 0


def test_build_prompt_from_state_full_state():
    """Test build_prompt_from_state with full state and all fields."""
    state: AgentState = {
        "market_snapshot": {
            "question": "Will this test pass?",
            "outcomes": ["Yes", "No"],
        },
        "event_context": {
            "category": "Macro",
            "region": "US",
            "resolution_criteria": "Test criteria",
        },
        "event": {
            "category": "Macro",
        },
        "horizon": "48h",
        "strategy_preset": "Aggressive",
    }

    prompt = build_prompt_from_context(
        market_snapshot=state.get("market_snapshot", {}),
        event_context=state.get("event_context", {}),
        event_data=state.get("event", {}),
        horizon=state.get("horizon", "24h"),
        strategy_preset=state.get("strategy_preset", "Balanced"),
    )

    assert "Will this test pass?" in prompt
    assert "Yes" in prompt or "No" in prompt
    assert "Macro" in prompt
    assert "48h" in prompt
    assert "Aggressive" in prompt


def test_build_prompt_from_state_missing_fields():
    """Test build_prompt_from_state with missing fields (fallbacks)."""
    prompt = build_prompt_from_context(
        market_snapshot={},
        event_context={},
        event_data={},
        horizon="24h",
        strategy_preset="Balanced",
    )

    assert "Market snapshot:" in prompt
    assert "Analysis horizon:" in prompt
    assert "Strategy preset:" in prompt


def test_build_prompt_from_state_various_configurations():
    """Test build_prompt_from_state with various event/market configurations."""
    # Test with event_context only
    state1: AgentState = {
        "event_context": {
            "category": "Politics",
            "region": "EU",
        },
    }
    prompt1 = build_prompt_from_context(
        market_snapshot={},
        event_context=state1.get("event_context", {}),
        event_data=state1.get("event", {}),
        horizon="24h",
        strategy_preset="Balanced",
    )
    assert "Politics" in prompt1
    assert "EU" in prompt1

    # Test with event doc only
    state2: AgentState = {
        "event": {
            "category": "Sports",
        },
    }
    prompt2 = build_prompt_from_context(
        market_snapshot={},
        event_context=state2.get("event_context", {}),
        event_data=state2.get("event", {}),
        horizon="24h",
        strategy_preset="Balanced",
    )
    assert "Sports" in prompt2


@pytest.mark.anyio(backend="asyncio")
async def test_generate_search_queries_with_openai():
    """Test generate_search_queries with OpenAI available."""
    state: AgentState = {
        "slug": "test-market",
        "horizon": "24h",
        "strategy_preset": "Balanced",
        "market_snapshot": {"question": "Will this test pass?"},
        "event_context": {"title": "Test Event"},
    }

    mock_response = {
        "queries": [
            {
                "name": "test_query",
                "query": "Test query string",
                "max_results": 8,
                "search_depth": "basic",
            }
        ]
    }

    with (
        patch("app.domains.news.query_generator.get_openai_client") as mock_get_client,
        patch("app.infrastructure.http.cache.openai_cache") as mock_cache,
        patch("app.infrastructure.http.resilience.openai_circuit") as mock_circuit,
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        mock_cache.get.return_value = None
        mock_circuit.can_attempt.return_value = True

        mock_client = MagicMock()
        mock_client.api_key = "test-key"
        mock_client.client = MagicMock()
        mock_client._use_new_api = True

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)
        mock_client.client.chat.completions.create = MagicMock(return_value=mock_completion)

        mock_get_client.return_value = mock_client

        mock_loop_instance = MagicMock()
        mock_loop_instance.run_in_executor = AsyncMock(return_value=mock_response)
        mock_loop.return_value = mock_loop_instance

        result = await generate_search_queries(
            market_snapshot=state.get("market_snapshot", {}),
            event_context=state.get("event_context", {}),
            event_data=state.get("event", {}),
            horizon=state.get("horizon", "24h"),
            strategy_preset=state.get("strategy_preset", "Balanced"),
            slug=state.get("slug", "unknown"),
        )

        assert len(result) == 1
        assert result[0]["name"] == "test_query"


@pytest.mark.anyio(backend="asyncio")
async def test_generate_search_queries_fallback():
    """Test generate_search_queries when OpenAI is unavailable."""
    state: AgentState = {
        "slug": "test-market",
        "horizon": "24h",
        "market_snapshot": {},
        "event_context": {},
    }

    with patch("app.domains.news.query_generator.get_openai_client") as mock_get_client:
        mock_get_client.side_effect = RuntimeError("OpenAI not available")

        result = await generate_search_queries(
            market_snapshot=state.get("market_snapshot", {}),
            event_context=state.get("event_context", {}),
            event_data=state.get("event", {}),
            horizon=state.get("horizon", "24h"),
            strategy_preset=state.get("strategy_preset", "Balanced"),
            slug=state.get("slug", "unknown"),
        )

        assert result == []


@pytest.mark.anyio(backend="asyncio")
async def test_generate_search_queries_missing_event_context():
    """Test generate_search_queries with missing event_context."""
    state: AgentState = {
        "slug": "test-market",
        "horizon": "24h",
        "market_snapshot": {},
    }

    with patch("app.domains.news.query_generator.get_openai_client") as mock_get_client:
        mock_get_client.side_effect = RuntimeError("OpenAI not available")

        result = await generate_search_queries(
            market_snapshot=state.get("market_snapshot", {}),
            event_context=state.get("event_context", {}),
            event_data=state.get("event", {}),
            horizon=state.get("horizon", "24h"),
            strategy_preset=state.get("strategy_preset", "Balanced"),
            slug=state.get("slug", "unknown"),
        )

        assert result == []


@pytest.mark.anyio(backend="asyncio")
async def test_generate_search_queries_cache_hit():
    """Test generate_search_queries returns cached results."""
    state: AgentState = {
        "slug": "test-market",
        "horizon": "24h",
        "market_snapshot": {},
        "event_context": {},
    }

    cached_response = {
        "queries": [
            {
                "name": "cached",
                "query": "Cached query",
                "max_results": 8,
                "search_depth": "basic",
            }
        ]
    }

    with patch("app.infrastructure.http.cache.openai_cache") as mock_cache:
        mock_cache.get.return_value = cached_response

        result = await generate_search_queries(
            market_snapshot=state.get("market_snapshot", {}),
            event_context=state.get("event_context", {}),
            event_data=state.get("event", {}),
            horizon=state.get("horizon", "24h"),
            strategy_preset=state.get("strategy_preset", "Balanced"),
            slug=state.get("slug", "unknown"),
        )

        assert len(result) == 1
        assert result[0]["name"] == "cached"


@pytest.mark.anyio(backend="asyncio")
async def test_generate_search_queries_invalid_json():
    """Test generate_search_queries with invalid JSON response."""
    state: AgentState = {
        "slug": "test-market",
        "horizon": "24h",
        "market_snapshot": {},
        "event_context": {},
    }

    with (
        patch("app.domains.news.query_generator.get_openai_client") as mock_get_client,
        patch("app.infrastructure.http.cache.openai_cache") as mock_cache,
        patch("app.infrastructure.http.resilience.openai_circuit") as mock_circuit,
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        mock_cache.get.return_value = None
        mock_circuit.can_attempt.return_value = True
        mock_client = MagicMock()
        mock_client.api_key = "test-key"
        mock_get_client.return_value = mock_client

        mock_loop.return_value.run_in_executor = MagicMock(
            side_effect=ValueError("Invalid JSON")
        )

        result = await generate_search_queries(
            market_snapshot=state.get("market_snapshot", {}),
            event_context=state.get("event_context", {}),
            event_data=state.get("event", {}),
            horizon=state.get("horizon", "24h"),
            strategy_preset=state.get("strategy_preset", "Balanced"),
            slug=state.get("slug", "unknown"),
        )

        assert result == []


@pytest.mark.anyio(backend="asyncio")
async def test_generate_search_queries_no_valid_queries():
    """Test generate_search_queries when LLM returns empty queries."""
    state: AgentState = {
        "slug": "test-market",
        "horizon": "24h",
        "market_snapshot": {},
        "event_context": {},
    }

    mock_response = {"queries": []}

    with (
        patch("app.domains.news.query_generator.get_openai_client") as mock_get_client,
        patch("app.infrastructure.http.cache.openai_cache") as mock_cache,
        patch("app.infrastructure.http.resilience.openai_circuit") as mock_circuit,
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        mock_cache.get.return_value = None
        mock_circuit.can_attempt.return_value = True
        mock_client = MagicMock()
        mock_client.api_key = "test-key"
        mock_get_client.return_value = mock_client

        mock_loop.return_value.run_in_executor = MagicMock(return_value=mock_response)

        result = await generate_search_queries(
            market_snapshot=state.get("market_snapshot", {}),
            event_context=state.get("event_context", {}),
            event_data=state.get("event", {}),
            horizon=state.get("horizon", "24h"),
            strategy_preset=state.get("strategy_preset", "Balanced"),
            slug=state.get("slug", "unknown"),
        )

        assert result == []


@pytest.mark.anyio(backend="asyncio")
async def test_generate_search_queries_circuit_breaker():
    """Test generate_search_queries with circuit breaker open."""
    state: AgentState = {
        "slug": "test-market",
        "horizon": "24h",
        "market_snapshot": {},
        "event_context": {},
    }

    with (
        patch("app.infrastructure.http.cache.openai_cache") as mock_cache,
        patch("app.infrastructure.http.resilience.openai_circuit") as mock_circuit,
    ):
        mock_cache.get.return_value = None
        mock_circuit.can_attempt.return_value = False

        result = await generate_search_queries(
            market_snapshot=state.get("market_snapshot", {}),
            event_context=state.get("event_context", {}),
            event_data=state.get("event", {}),
            horizon=state.get("horizon", "24h"),
            strategy_preset=state.get("strategy_preset", "Balanced"),
            slug=state.get("slug", "unknown"),
        )

        assert result == []
