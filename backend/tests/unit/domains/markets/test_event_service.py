"""Tests for Event Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.domains.markets.event_service import _derive_event_slug
from app.orchestration.agents.event import run_event_agent
from app.orchestration.state import AgentState


def test_derive_event_slug_empty():
    """Test _derive_event_slug with empty/None input."""
    assert _derive_event_slug(None) == "unknown-event"
    assert _derive_event_slug("") == "unknown-event"


def test_derive_event_slug_single_part():
    """Test _derive_event_slug with single-part slug."""
    assert _derive_event_slug("market") == "market"
    assert _derive_event_slug("single") == "single"


def test_derive_event_slug_multi_part():
    """Test _derive_event_slug with multi-part slug."""
    assert _derive_event_slug("event-market") == "event"
    assert _derive_event_slug("fed-decision-in-december-50bps") == "fed-decision-in-december"
    assert _derive_event_slug("a-b-c-d") == "a-b-c"


def test_derive_event_slug_edge_cases():
    """Test _derive_event_slug with edge cases."""
    # Single dash
    result = _derive_event_slug("-")
    assert result == "-" or result == ""

    # Multiple dashes
    assert _derive_event_slug("a---b") == "a--"


@pytest.mark.anyio(backend="asyncio")
async def test_run_event_agent_full_state():
    """Test run_event_agent with full state and all event fields."""
    state: AgentState = {
        "slug": "fed-decision-in-december-50bps",
        "run_at": "2025-11-15T15:10:00Z",
        "polymarket_url": "https://polymarket.com/event/fed-decision",
        "event": {
            "slug": "fed-decision-in-december",
            "gamma_event_id": "35090",
            "title": "Fed Decision in December?",
            "description": "What will the Fed do at its December 2025 meeting?",
            "category": "Macro",
            "image": "https://example.com/image.png",
            "end_date": "2025-12-10T00:00:00Z",
            "commentCount": 42,
            "seriesCommentCount": 15,
            "volume24hr": 1000000.0,
        },
    }

    result = await run_event_agent(state)

    assert result["event"]["slug"] == "fed-decision-in-december"
    assert result["event"]["gamma_event_id"] == "35090"
    assert result["event"]["title"] == "Fed Decision in December?"
    assert result["event"]["description"] == "What will the Fed do at its December 2025 meeting?"
    assert result["event"]["category"] == "Macro"
    assert result["event"]["image"] == "https://example.com/image.png"
    assert result["event"]["end_date"] == "2025-12-10T00:00:00Z"
    assert result["event"]["commentCount"] == 42
    assert result["event"]["seriesCommentCount"] == 15
    assert result["event"]["volume24hr"] == 1000000.0
    assert result["event_description"] == "What will the Fed do at its December 2025 meeting?"
    assert result["event_context"]["title"] == "Fed Decision in December?"
    assert result["event_context"]["commentCount"] == 42
    assert result["event_context"]["seriesCommentCount"] == 15
    assert result["event_context"]["volume24hr"] == 1000000.0
    assert result["event_context"]["url"] == "https://polymarket.com/event/fed-decision"


@pytest.mark.anyio(backend="asyncio")
async def test_run_event_agent_missing_fields():
    """Test run_event_agent with missing event fields (fallbacks)."""
    state: AgentState = {
        "slug": "test-market",
    }

    result = await run_event_agent(state)

    # _derive_event_slug("test-market") returns "test" (all parts except last)
    assert result["event"]["slug"] == "test"
    # gamma_event_id uses the derived event_slug, not the original market slug
    assert result["event"]["gamma_event_id"] == "evt-test"
    assert "?" in result["event"]["title"]
    assert (
        result["event"]["description"]
        == "Placeholder description for the macro event associated with this market."
    )
    assert result["event"]["category"] == "Macro"
    assert result["event"]["image"] is None
    assert result["event"]["end_date"] is not None
    assert "Z" in result["event"]["end_date"]


@pytest.mark.anyio(backend="asyncio")
async def test_run_event_agent_preserves_comment_count_zero():
    """Test that commentCount of 0 is preserved (not treated as None)."""
    state: AgentState = {
        "slug": "test-market",
        "event": {
            "commentCount": 0,
            "seriesCommentCount": 0,
            "volume24hr": 0.0,
        },
    }

    result = await run_event_agent(state)

    assert result["event"]["commentCount"] == 0
    assert result["event"]["seriesCommentCount"] == 0
    assert result["event"]["volume24hr"] == 0.0
    assert result["event_context"]["commentCount"] == 0
    assert result["event_context"]["seriesCommentCount"] == 0
    assert result["event_context"]["volume24hr"] == 0.0


@pytest.mark.anyio(backend="asyncio")
async def test_run_event_agent_handles_none_comment_count():
    """Test that None commentCount is handled correctly."""
    state: AgentState = {
        "slug": "test-market",
        "event": {
            "commentCount": None,
        },
    }

    result = await run_event_agent(state)

    assert "commentCount" not in result["event"] or result["event"].get("commentCount") is None
    assert result["event_context"]["commentCount"] is None


@pytest.mark.anyio(backend="asyncio")
async def test_run_event_agent_missing_market_slug():
    """Test run_event_agent with missing market_slug."""
    state: AgentState = {
        "event": {},
    }

    result = await run_event_agent(state)

    assert result["event"]["slug"] == "unknown-event"
    assert result["event"]["gamma_event_id"] == "evt-unknown-event"


@pytest.mark.anyio(backend="asyncio")
async def test_run_event_agent_missing_run_at():
    """Test run_event_agent with missing run_at (uses current time)."""
    state: AgentState = {
        "slug": "test-market",
    }

    with patch("app.orchestration.agents.event.datetime") as mock_datetime:
        fixed_time = datetime(2025, 11, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        result = await run_event_agent(state)

        assert result["event"]["updated_at"] is not None


@pytest.mark.anyio(backend="asyncio")
async def test_run_event_agent_url_fallback():
    """Test run_event_agent URL fallback from market_url to polymarket_url."""
    state: AgentState = {
        "slug": "test-market",
        "market_url": "https://polymarket.com/market/test",
    }

    result = await run_event_agent(state)

    assert result["event_context"]["url"] == "https://polymarket.com/market/test"

    # Test polymarket_url takes precedence
    state["polymarket_url"] = "https://polymarket.com/event/test"
    result = await run_event_agent(state)
    assert result["event_context"]["url"] == "https://polymarket.com/event/test"


@pytest.mark.anyio(backend="asyncio")
async def test_run_event_agent_derives_slug_from_market():
    """Test that event slug is derived from market slug when not provided."""
    state: AgentState = {
        "slug": "fed-decision-in-december-50bps",
        "event": {},
    }

    result = await run_event_agent(state)

    assert result["event"]["slug"] == "fed-decision-in-december"


@pytest.mark.anyio(backend="asyncio")
async def test_run_event_agent_preserves_created_at():
    """Test that created_at is preserved if present."""
    state: AgentState = {
        "slug": "test-market",
        "event": {
            "created_at": "2025-01-01T00:00:00Z",
        },
    }

    result = await run_event_agent(state)

    assert result["event"]["created_at"] == "2025-01-01T00:00:00Z"
    assert result["event"]["updated_at"] is not None
