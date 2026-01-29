"""Tests for Async Repositories."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.db.async_repositories import (
    attach_trace_to_run_async,
    create_run_async,
    create_trace_async,
    ensure_indexes_async,
    events_collection_async,
    get_run_async,
    list_runs_by_market_async,
    markets_collection_async,
    runs_collection_async,
    traces_collection_async,
    upsert_event_async,
    upsert_market_async,
)


@pytest.mark.anyio(backend="asyncio")
async def test_events_collection_async():
    """Test events_collection_async."""
    with patch("app.db.async_repositories.get_async_db") as mock_get_db:
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
    with patch("app.db.async_repositories.get_async_db") as mock_get_db:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_db.return_value = mock_db

        collection = await markets_collection_async()

        assert collection == mock_collection


@pytest.mark.anyio(backend="asyncio")
async def test_runs_collection_async():
    """Test runs_collection_async."""
    with patch("app.db.async_repositories.get_async_db") as mock_get_db:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_get_db.return_value = mock_db

        collection = await runs_collection_async()

        assert collection == mock_collection


@pytest.mark.anyio(backend="asyncio")
async def test_traces_collection_async():
    """Test traces_collection_async."""
    with patch("app.db.async_repositories.get_async_db") as mock_get_db:
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
    import app.db.async_repositories

    app.db.async_repositories._INDEXES_CREATED = False

    with (
        patch("app.db.async_repositories.events_collection_async") as mock_events,
        patch("app.db.async_repositories.markets_collection_async") as mock_markets,
        patch("app.db.async_repositories.runs_collection_async") as mock_runs,
        patch("app.db.async_repositories.traces_collection_async") as mock_traces,
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


@pytest.mark.anyio(backend="asyncio")
async def test_upsert_event_async():
    """Test upsert_event_async insert new."""
    event_doc = {
        "slug": "test-event",
        "title": "Test Event",
        "updated_at": "2025-11-15T00:00:00Z",
    }

    with patch("app.db.async_repositories.events_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_result = {**event_doc, "_id": ObjectId()}
        mock_coll.find_one_and_update = AsyncMock(return_value=mock_result)
        mock_collection.return_value = mock_coll

        result = await upsert_event_async(event_doc)

        assert result["slug"] == "test-event"
        assert mock_coll.find_one_and_update.called


@pytest.mark.anyio(backend="asyncio")
async def test_upsert_event_async_missing_slug():
    """Test upsert_event_async with missing slug."""
    event_doc = {
        "title": "Test Event",
    }

    with patch("app.db.async_repositories.events_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_collection.return_value = mock_coll

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

    with patch("app.db.async_repositories.markets_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_result = {**market_doc, "_id": ObjectId()}
        mock_coll.find_one_and_update = AsyncMock(return_value=mock_result)
        mock_collection.return_value = mock_coll

        result = await upsert_market_async(market_doc)

        assert result["slug"] == "test-market"
        assert mock_coll.find_one_and_update.called


@pytest.mark.anyio(backend="asyncio")
async def test_create_run_async():
    """Test create_run_async successful creation."""
    run_doc = {
        "run_id": "test-run",
        "market_snapshot": {},
    }

    with patch("app.db.async_repositories.runs_collection_async") as mock_collection:
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

    with patch("app.db.async_repositories.traces_collection_async") as mock_collection:
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

    with patch("app.db.async_repositories.runs_collection_async") as mock_collection:
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

    with patch("app.db.async_repositories.runs_collection_async") as mock_collection:
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

    with patch("app.db.async_repositories.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.find_one = AsyncMock(return_value=None)
        mock_collection.return_value = mock_coll

        result = await get_run_async(run_id)

        assert result is None


@pytest.mark.anyio(backend="asyncio")
async def test_get_run_async_invalid_id():
    """Test get_run_async with invalid ID throws exception."""
    with patch("app.db.async_repositories.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()
        mock_coll.find_one = AsyncMock(side_effect=Exception("Invalid ObjectId"))
        mock_collection.return_value = mock_coll

        with pytest.raises(Exception, match="Invalid ObjectId"):
            await get_run_async("invalid-id")


@pytest.mark.anyio(backend="asyncio")
async def test_list_runs_by_market_async():
    """Test list_runs_by_market_async multiple runs."""
    market_id = "507f1f77bcf86cd799439011"
    mock_runs = [
        {"run_id": "run-1", "market_id": ObjectId(market_id)},
        {"run_id": "run-2", "market_id": ObjectId(market_id)},
    ]

    with patch("app.db.async_repositories.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()

        # Create an async iterator class for the cursor
        class AsyncIterator:
            def __init__(self, items):
                self.items = items
                self.index = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index >= len(self.items):
                    raise StopAsyncIteration
                item = self.items[self.index]
                self.index += 1
                return item

        # Create iterator instance
        iterator = AsyncIterator(mock_runs)
        mock_cursor = MagicMock()
        # __aiter__ should return the iterator when called
        mock_cursor.__aiter__ = MagicMock(return_value=iterator)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_coll.find = MagicMock(return_value=mock_cursor)
        mock_collection.return_value = mock_coll

        result = await list_runs_by_market_async(market_id)

        assert len(result) == 2
        assert result[0]["run_id"] == "run-1"


@pytest.mark.anyio(backend="asyncio")
async def test_list_runs_by_market_async_empty():
    """Test list_runs_by_market_async empty results."""
    market_id = "507f1f77bcf86cd799439011"

    with patch("app.db.async_repositories.runs_collection_async") as mock_collection:
        mock_coll = AsyncMock()

        # Create an empty async iterator class for the cursor
        class AsyncIterator:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise StopAsyncIteration

        # Create iterator instance
        iterator = AsyncIterator()
        mock_cursor = MagicMock()
        # __aiter__ should return the iterator when called
        mock_cursor.__aiter__ = MagicMock(return_value=iterator)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_coll.find = MagicMock(return_value=mock_cursor)
        mock_collection.return_value = mock_coll

        result = await list_runs_by_market_async(market_id)

        assert len(result) == 0


@pytest.mark.anyio(backend="asyncio")
async def test_list_runs_by_market_async_invalid_id():
    """Test list_runs_by_market_async with invalid market_id raises ValueError."""
    # Invalid ObjectId validation happens before database call
    with pytest.raises(ValueError, match="must be a valid ObjectId"):
        await list_runs_by_market_async("invalid-id")
