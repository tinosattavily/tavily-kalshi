"""Tests for Async Repositories."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.infrastructure.database.repositories import (
    attach_trace_to_run_async,
    create_run_async,
    create_trace_async,
    ensure_indexes_async,
    events_collection_async,
    get_run_async,
    markets_collection_async,
    runs_collection_async,
    traces_collection_async,
    upsert_event_async,
    upsert_market_async,
)


@pytest.mark.anyio(backend="asyncio")
async def test_events_collection_async():
    """Test events_collection_async."""
    with patch("app.infrastructure.database.repositories.get_async_db") as mock_get_db:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_db.return_value = mock_db

        collection = await events_collection_async()

        assert collection == mock_collection
        mock_db.__getitem__.assert_called_with("events")


@pytest.mark.anyio(backend="asyncio")
async def test_markets_collection_async():
    """Test markets_collection_async."""
    with patch("app.infrastructure.database.repositories.get_async_db") as mock_get_db:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_db.return_value = mock_db

        collection = await markets_collection_async()

        assert collection == mock_collection


@pytest.mark.anyio(backend="asyncio")
async def test_runs_collection_async():
    """Test runs_collection_async."""
    with patch("app.infrastructure.database.repositories.get_async_db") as mock_get_db:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_db.return_value = mock_db

        collection = await runs_collection_async()

        assert collection == mock_collection


@pytest.mark.anyio(backend="asyncio")
async def test_traces_collection_async():
    """Test traces_collection_async."""
    with patch("app.infrastructure.database.repositories.get_async_db") as mock_get_db:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_db.return_value = mock_db

        collection = await traces_collection_async()

        assert collection == mock_collection


@pytest.mark.anyio(backend="asyncio")
async def test_ensure_indexes_async():
    """Test ensure_indexes_async index creation."""
    # Reset the global flag to ensure indexes are created
    import app.infrastructure.database.repositories

    app.infrastructure.database.repositories._INDEXES_CREATED = False

    with (
        patch("app.infrastructure.database.repositories.events_collection_async") as mock_events,
        patch("app.infrastructure.database.repositories.markets_collection_async") as mock_markets,
        patch("app.infrastructure.database.repositories.runs_collection_async") as mock_runs,
        patch("app.infrastructure.database.repositories.traces_collection_async") as mock_traces,
    ):
        mock_events_coll = AsyncMock()
        mock_markets_coll = AsyncMock()
        mock_runs_coll = AsyncMock()
        mock_traces_coll = AsyncMock()
        mock_events.return_value = mock_events_coll
        mock_markets.return_value = mock_markets_coll
        mock_runs.return_value = mock_runs_coll
        mock_traces.return_value = mock_traces_coll

        await ensure_indexes_async()

        # Verify indexes were created
        assert mock_events_coll.create_index.called
        assert mock_markets_coll.create_index.called
        assert mock_runs_coll.create_index.called
        assert mock_traces_coll.create_index.called
        mock_markets_coll.create_index.assert_any_call(
            "polymarket_url",
            unique=True,
            partialFilterExpression={"polymarket_url": {"$exists": True, "$type": "string"}},
        )
        mock_markets_coll.create_index.assert_any_call(
            [("venue", 1), ("venue_market_id", 1)],
            unique=True,
        )


@pytest.mark.anyio(backend="asyncio")
async def test_upsert_event_async():
    """Test upsert_event_async insert new."""
    event_doc = {
        "slug": "test-event",
        "title": "Test Event",
        "updated_at": "2025-11-15T00:00:00Z",
    }

    with patch(
        "app.infrastructure.database.repositories.events_collection_async"
    ) as mock_collection:
        mock_coll = AsyncMock()
        mock_result = {**event_doc, "_id": ObjectId()}
        mock_coll.find_one_and_update = AsyncMock(return_value=mock_result)
        mock_collection.return_value = mock_coll

        result = await upsert_event_async(event_doc)

        assert result["slug"] == "test-event"
        assert mock_coll.find_one_and_update.called


@pytest.mark.anyio(backend="asyncio")
async def test_upsert_event_async_prefers_venue_identity():
    """Test upsert_event_async uses venue-native identity when available."""
    event_doc = {
        "slug": "AAA-25JAN",
        "venue": "kalshi",
        "venue_event_id": "AAA-25JAN",
        "title": "Test Event",
    }

    with patch(
        "app.infrastructure.database.repositories.events_collection_async"
    ) as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.find_one_and_update = AsyncMock(return_value={**event_doc, "_id": ObjectId()})
        mock_collection.return_value = mock_coll

        await upsert_event_async(event_doc)

        assert mock_coll.find_one_and_update.call_args.args[0] == {
            "venue": "kalshi",
            "venue_event_id": "AAA-25JAN",
        }


@pytest.mark.anyio(backend="asyncio")
async def test_upsert_event_async_missing_slug():
    """Test upsert_event_async with missing slug."""
    event_doc = {
        "title": "Test Event",
    }

    with pytest.raises(ValueError, match="slug is required"):
        await upsert_event_async(event_doc)


@pytest.mark.anyio(backend="asyncio")
async def test_upsert_market_async():
    """Test upsert_market_async insert new."""
    market_doc = {
        "slug": "test-market",
        "question": "Test?",
        "updated_at": "2025-11-15T00:00:00Z",
    }

    with patch(
        "app.infrastructure.database.repositories.markets_collection_async"
    ) as mock_collection:
        mock_coll = AsyncMock()
        mock_result = {**market_doc, "_id": ObjectId()}
        mock_coll.find_one_and_update = AsyncMock(return_value=mock_result)
        mock_collection.return_value = mock_coll

        result = await upsert_market_async(market_doc)

        assert result["slug"] == "test-market"
        assert mock_coll.find_one_and_update.called


@pytest.mark.anyio(backend="asyncio")
async def test_upsert_market_async_prefers_venue_identity():
    """Test upsert_market_async uses venue-native identity when available."""
    market_doc = {
        "slug": "AAA-25JAN-B1",
        "venue": "kalshi",
        "venue_market_id": "AAA-25JAN-B1",
        "question": "Test?",
    }

    with patch(
        "app.infrastructure.database.repositories.markets_collection_async"
    ) as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.find_one_and_update = AsyncMock(return_value={**market_doc, "_id": ObjectId()})
        mock_collection.return_value = mock_coll

        await upsert_market_async(market_doc)

        assert mock_coll.find_one_and_update.call_args.args[0] == {
            "venue": "kalshi",
            "venue_market_id": "AAA-25JAN-B1",
        }


@pytest.mark.anyio(backend="asyncio")
async def test_create_run_async():
    """Test create_run_async successful creation."""
    run_doc = {
        "run_id": "test-run",
        "market_snapshot": {},
    }

    with patch("app.infrastructure.database.repositories.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_coll.insert_one = AsyncMock(return_value=mock_result)
        mock_collection.return_value = mock_coll

        run_id = await create_run_async(run_doc)

        assert isinstance(run_id, ObjectId)
        assert mock_coll.insert_one.called


@pytest.mark.anyio(backend="asyncio")
async def test_create_trace_async():
    """Test create_trace_async successful creation."""
    trace_doc = {
        "run_id": ObjectId(),
        "steps": [],
    }

    with patch(
        "app.infrastructure.database.repositories.traces_collection_async"
    ) as mock_collection:
        mock_coll = AsyncMock()
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_coll.insert_one = AsyncMock(return_value=mock_result)
        mock_collection.return_value = mock_coll

        trace_id = await create_trace_async(trace_doc)

        assert isinstance(trace_id, ObjectId)


@pytest.mark.anyio(backend="asyncio")
async def test_attach_trace_to_run_async():
    """Test attach_trace_to_run_async successful attachment."""
    run_id = ObjectId()
    trace_id = ObjectId()

    with patch("app.infrastructure.database.repositories.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.update_one = AsyncMock()
        mock_collection.return_value = mock_coll

        await attach_trace_to_run_async(run_id, trace_id)

        assert mock_coll.update_one.called


@pytest.mark.anyio(backend="asyncio")
async def test_get_run_async_found():
    """Test get_run_async found run."""
    run_id = "507f1f77bcf86cd799439011"
    mock_run = {
        "_id": ObjectId(run_id),
        "run_id": "test-run",
        "market_snapshot": {},
    }

    with patch("app.infrastructure.database.repositories.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.find_one = AsyncMock(return_value=mock_run)
        mock_collection.return_value = mock_coll

        result = await get_run_async(run_id)

        assert result is not None
        assert result["run_id"] == "test-run"


@pytest.mark.anyio(backend="asyncio")
async def test_get_run_async_not_found():
    """Test get_run_async not found."""
    run_id = "507f1f77bcf86cd799439011"

    with patch("app.infrastructure.database.repositories.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.find_one = AsyncMock(return_value=None)
        mock_collection.return_value = mock_coll

        result = await get_run_async(run_id)

        assert result is None


@pytest.mark.anyio(backend="asyncio")
async def test_get_run_async_invalid_id():
    """Test get_run_async with invalid ID."""
    with patch("app.infrastructure.database.repositories.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.find_one = AsyncMock(side_effect=Exception("Invalid ObjectId"))
        mock_collection.return_value = mock_coll

        with pytest.raises(RuntimeError):
            await get_run_async("invalid-id")


