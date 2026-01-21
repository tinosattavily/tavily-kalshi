from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.orchestration.snapshot import (
    _utc_now_iso,
    build_event_document,
    build_market_document,
    build_run_document,
    build_trace_document,
    init_run_document_async,
    persist_run_snapshot_async,
    update_run_phase_async,
    update_run_with_event_and_market_async,
)
from app.orchestration.state import AgentState


def _sample_state() -> AgentState:
    return {
        "run_at": "2025-11-15T15:10:00Z",
        "slug": "fed-decision-in-december-50bps",
        "polymarket_url": "https://polymarket.com/event/fed-decision-in-december?tid=abc",
        "event": {
            "gamma_event_id": "35090",
            "slug": "fed-decision-in-december",
            "title": "Fed decision in December?",
            "description": "What will the Fed do at its December 2025 meeting...",
            "category": "Macro",
            "image": "https://example.com/event.png",
            "end_date": "2025-12-10T00:00:00Z",
        },
        "market": {
            "gamma_market_id": "570360",
            "slug": "fed-decision-in-december-50bps",
            "polymarket_url": "https://polymarket.com/event/fed-decision-in-december?tid=abc",
            "question": "Fed decreases interest rates by 50+ bps...",
            "outcomes": ["Yes", "No"],
            "yes_index": 0,
            "group_item_title": "50+ bps decrease",
        },
        "market_snapshot": {
            "question": "Fed decreases interest rates by 50+ bps...",
            "outcomes": ["Yes", "No"],
            "yes_index": 0,
            "yes_price": 0.0195,
            "no_price": 0.9805,
            "best_bid": 0.019,
            "best_ask": 0.02,
            "last_trade_price": 0.02,
            "volume": 19807829.12,
            "liquidity": 1234567.89,
            "end_date": "2025-12-10T00:00:00Z",
        },
        "event_context": {
            "title": "Fed decision in December?",
            "description": "What will the Fed do at its December 2025 meeting...",
            "category": "Macro",
        },
        "news_context": {
            "tavily_queries": [
                "Fed December 2025 meeting rate expectations",
                "latest FOMC projections December 2025",
            ],
            "articles": [
                {
                    "title": "New poll shows economists expect no change in December",
                    "source": "FT",
                    "url": "https://example.com/ft-story",
                    "published_at": "2025-11-15T10:00:00Z",
                    "snippet": "Economists surveyed now price a 70% chance of no change...",
                }
            ],
            "summary": "Recent inflation prints came in lower than expected.",
        },
        "signal": {
            "direction": "up",
            "model_prob": 0.08,
            "model_prob_abs": 0.0995,
            "expected_delta_range": [0.03, 0.08],
            "confidence": "medium",
            "rationale": "Improved inflation and dovish tone from key Fed officials.",
        },
        "decision": {
            "action": "BUY",
            "edge_pct": 0.08,
            "toy_kelly_fraction": 0.6,
            "notes": "Action triggered: edge 8% > min_edge 5% and confidence >= medium.",
        },
        "report": {
            "title": "Fed December 50bps cut — BUY YES (edge ~8%)",
            "markdown": "## TL;DR\nWe expect YES odds to move from 2% to around 10%...",
        },
        "env": {
            "app_version": "0.1.0",
            "model": "gpt-4.1-mini",
            "tavily_version": "v1",
            "langgraph_graph_version": "market-v1",
        },
        "strategy_params": {
            "min_edge_pct": 0.08,
            "min_confidence": "medium",
            "max_capital_pct": 0.15,
        },
        "strategy_preset": "Balanced",
        "horizon": "24h",
    }


def test_build_event_document_preserves_slug_and_category():
    state = _sample_state()
    doc = build_event_document(state, "2025-11-15T15:10:00Z")
    assert doc["slug"] == "fed-decision-in-december"
    assert doc["category"] == "Macro"
    assert doc["created_at"] is not None
    assert doc["updated_at"] is not None


def test_build_market_document_links_event():
    state = _sample_state()
    event_id = ObjectId()
    doc = build_market_document(state, "2025-11-15T15:10:00Z", event_id)
    assert doc["event_id"] == event_id
    assert doc["slug"] == "fed-decision-in-december-50bps"
    assert doc["polymarket_url"].startswith("https://polymarket.com/event/")
    assert doc["outcomes"] == ["Yes", "No"]


def test_build_run_document_denormalizes_snapshot_and_context():
    state = _sample_state()
    event_id = ObjectId()
    market_id = ObjectId()
    doc = build_run_document(state, "2025-11-15T15:10:00Z", event_id, market_id)

    assert doc["market_id"] == market_id
    assert doc["event_id"] == event_id
    assert doc["market_snapshot"]["yes_price"] == 0.0195
    assert doc["event_context"]["category"] == "Macro"
    assert doc["news_context"]["tavily_queries"]
    assert doc["signal"]["direction"] == "up"
    assert doc["decision"]["action"] == "BUY"
    assert doc["strategy_preset"] == "Balanced"


def test_build_trace_document():
    """Test build_trace_document."""
    from app.orchestration.state import TracePayload

    trace_payload: TracePayload = {
        "steps": [{"agent": "market", "status": "done"}],
        "raw_state": {"slug": "test"},
        "metadata": {"version": "1.0"},
    }
    run_id = ObjectId()
    timestamp = "2025-11-15T15:10:00Z"

    doc = build_trace_document(trace_payload, run_id, timestamp)

    assert doc["run_id"] == run_id
    assert doc["created_at"] == timestamp
    assert len(doc["steps"]) == 1
    assert doc["raw_state"]["slug"] == "test"


def test_utc_now_iso():
    """Test _utc_now_iso timestamp format."""
    timestamp = _utc_now_iso()

    assert "T" in timestamp
    assert "Z" in timestamp or "+00:00" in timestamp


def test_build_event_document_missing_fields():
    """Test build_event_document with missing fields."""
    state: AgentState = {
        "slug": "test-market",
    }

    doc = build_event_document(state, "2025-11-15T15:10:00Z")

    assert doc["slug"] is not None
    assert doc["created_at"] is not None


def test_build_market_document_missing_fields():
    """Test build_market_document with missing fields."""
    state: AgentState = {
        "slug": "test-market",
    }
    event_id = ObjectId()

    doc = build_market_document(state, "2025-11-15T15:10:00Z", event_id)

    assert doc["event_id"] == event_id
    assert doc["slug"] is not None


@pytest.mark.anyio(backend="asyncio")
async def test_persist_run_snapshot_async():
    """Test persist_run_snapshot_async successful persistence."""
    state = _sample_state()

    with (
        patch("app.orchestration.snapshot.upsert_event_async") as mock_upsert_event,
        patch("app.orchestration.snapshot.upsert_market_async") as mock_upsert_market,
        patch("app.orchestration.snapshot.create_run_async") as mock_create_run,
        patch("app.orchestration.snapshot.create_trace_async"),
        patch("app.orchestration.snapshot.attach_trace_to_run_async"),
    ):
        mock_upsert_event.return_value = {"_id": ObjectId()}
        mock_upsert_market.return_value = {"_id": ObjectId()}
        mock_create_run.return_value = ObjectId()

        result = await persist_run_snapshot_async(state)

        assert "run_id" in result
        assert "event" in result
        assert "market" in result
        assert "run" in result


@pytest.mark.anyio(backend="asyncio")
async def test_persist_run_snapshot_async_with_trace():
    """Test persist_run_snapshot_async with trace."""
    state = _sample_state()
    state["trace"] = {
        "steps": [{"agent": "market"}],
    }

    with (
        patch("app.orchestration.snapshot.upsert_event_async") as mock_upsert_event,
        patch("app.orchestration.snapshot.upsert_market_async") as mock_upsert_market,
        patch("app.orchestration.snapshot.create_run_async") as mock_create_run,
        patch("app.orchestration.snapshot.create_trace_async") as mock_create_trace,
        patch("app.orchestration.snapshot.attach_trace_to_run_async") as mock_attach,
    ):
        mock_upsert_event.return_value = {"_id": ObjectId()}
        mock_upsert_market.return_value = {"_id": ObjectId()}
        mock_create_run.return_value = ObjectId()
        mock_create_trace.return_value = ObjectId()
        mock_attach.return_value = AsyncMock()

        result = await persist_run_snapshot_async(state)

        assert "trace_id" in result
        assert mock_create_trace.called


@pytest.mark.anyio(backend="asyncio")
async def test_init_run_document_async():
    """Test init_run_document_async successful init."""
    with patch("app.orchestration.snapshot.create_run_async") as mock_create:
        mock_create.return_value = ObjectId()

        run_id = await init_run_document_async(
            "test-run-id",
            "https://polymarket.com/market/test",
            "48h",
            "Aggressive",
            {"min_edge_pct": 0.03},
        )

        assert isinstance(run_id, ObjectId)
        assert mock_create.called


@pytest.mark.anyio(backend="asyncio")
async def test_update_run_phase_async():
    """Test update_run_phase_async all phases."""
    with patch("app.orchestration.snapshot.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.update_one = AsyncMock(return_value=MagicMock(matched_count=1, modified_count=1))
        mock_collection.return_value = mock_coll

        # Test all phases
        for phase in ["market", "news", "signal", "report"]:
            await update_run_phase_async("test-run", phase, "done", {})

        assert mock_coll.update_one.call_count == 4


@pytest.mark.anyio(backend="asyncio")
async def test_update_run_phase_async_with_data():
    """Test update_run_phase_async with phase data."""
    with patch("app.orchestration.snapshot.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.update_one = AsyncMock(return_value=MagicMock(matched_count=1, modified_count=1))
        mock_collection.return_value = mock_coll

        await update_run_phase_async(
            "test-run",
            "market",
            "done",
            {
                "market_snapshot": {"yes_price": 0.5},
                "event_context": {"title": "Test"},
            },
        )

        assert mock_coll.update_one.called


@pytest.mark.anyio(backend="asyncio")
async def test_update_run_with_event_and_market_async():
    """Test update_run_with_event_and_market_async successful update."""
    state = _sample_state()

    with (
        patch("app.orchestration.snapshot.upsert_event_async") as mock_upsert_event,
        patch("app.orchestration.snapshot.upsert_market_async") as mock_upsert_market,
        patch("app.orchestration.snapshot.runs_collection_async") as mock_collection,
    ):
        event_id = ObjectId()
        market_id = ObjectId()
        mock_upsert_event.return_value = {"_id": event_id}
        mock_upsert_market.return_value = {"_id": market_id, "slug": "test-market"}
        mock_coll = AsyncMock()
        mock_coll.update_one = AsyncMock()
        mock_collection.return_value = mock_coll

        result_event_id, result_market_id = await update_run_with_event_and_market_async(
            "test-run", state
        )

        assert result_event_id == event_id
        assert result_market_id == market_id
        assert mock_coll.update_one.called
