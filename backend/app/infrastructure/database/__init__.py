# app/infrastructure/database/__init__.py
"""Database infrastructure exports."""

from app.infrastructure.database.client import (
    check_mongodb_health,
    close_async_client,
    get_async_client,
    get_async_db,
)
from app.infrastructure.database.repositories import (
    attach_trace_to_run_async,
    create_run_async,
    create_trace_async,
    ensure_indexes_async,
    events_collection_async,
    get_run_async,
    list_recent_runs_async,
    list_runs_by_market_async,
    markets_collection_async,
    runs_collection_async,
    traces_collection_async,
    upsert_event_async,
    upsert_market_async,
)
from app.infrastructure.database.utils import ensure_object_id, serialize_document

__all__ = [
    # Client
    "check_mongodb_health",
    "close_async_client",
    "get_async_client",
    "get_async_db",
    # Repositories
    "attach_trace_to_run_async",
    "create_run_async",
    "create_trace_async",
    "ensure_indexes_async",
    "events_collection_async",
    "get_run_async",
    "list_recent_runs_async",
    "list_runs_by_market_async",
    "markets_collection_async",
    "runs_collection_async",
    "traces_collection_async",
    "upsert_event_async",
    "upsert_market_async",
    # Utils
    "ensure_object_id",
    "serialize_document",
]
