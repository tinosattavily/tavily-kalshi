from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId

from app.agents.state import AgentState, TracePayload
from app.core.logging_config import get_logger
from app.db.async_repositories import (
    attach_trace_to_run_async,
    create_run_async,
    create_trace_async,
    runs_collection_async,
    upsert_event_async,
    upsert_market_async,
)
from app.db.models import EventDocument, MarketDocument, RunDocument, TraceDocument
from app.db.utils import serialize_document

logger = get_logger(__name__)


def serialize_signal(signal_raw: Any) -> dict[str, Any]:
    """Serialize a signal to dict, handling both Pydantic models and dicts."""
    if hasattr(signal_raw, "model_dump"):
        return signal_raw.model_dump()
    if hasattr(signal_raw, "dict"):
        return signal_raw.dict()
    if isinstance(signal_raw, dict):
        return signal_raw
    return {}


def build_event_document(state: AgentState, timestamp: str) -> EventDocument:
    event_state = state.get("event", {})
    updated_at = event_state.get("updated_at") or timestamp
    created_at = event_state.get("created_at") or updated_at

    return {
        "gamma_event_id": event_state.get("gamma_event_id")
        or state.get("gamma_event_id")
        or "unknown-event",
        "slug": event_state.get("slug") or state.get("event_slug") or "unknown-event",
        "title": (
            event_state.get("title")
            or state.get("event_context", {}).get("title")
            or "Untitled event"
        ),
        "description": event_state.get("description")
        or state.get("event_description")
        or "No description provided.",
        "category": event_state.get("category") or "Macro",
        "image": event_state.get("image"),
        "end_date": event_state.get("end_date") or timestamp,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def build_market_document(state: AgentState, timestamp: str, event_id: ObjectId) -> MarketDocument:
    market_state = state.get("market", {})
    updated_at = market_state.get("updated_at") or timestamp
    created_at = market_state.get("created_at") or updated_at
    slug = market_state.get("slug") or state.get("slug") or "unknown-market"

    return {
        "event_id": event_id,
        "gamma_market_id": market_state.get("gamma_market_id")
        or state.get("gamma_market_id")
        or f"market-{slug}",
        "slug": slug,
        "polymarket_url": market_state.get("polymarket_url")
        or state.get("polymarket_url")
        or state.get("market_url")
        or "",
        "question": (
            market_state.get("question") or state.get("market_snapshot", {}).get("question", "")
        ),
        "outcomes": (
            market_state.get("outcomes") or state.get("market_snapshot", {}).get("outcomes", [])
        ),
        "yes_index": market_state.get("yes_index", 0),
        "group_item_title": market_state.get("group_item_title"),
        "created_at": created_at,
        "updated_at": updated_at,
    }


def build_run_document(
    state: AgentState,
    timestamp: str,
    event_id: ObjectId,
    market_id: ObjectId,
) -> RunDocument:
    default_news_context = {"tavily_queries": [], "articles": [], "summary": ""}
    market_snapshot = state.get("market_snapshot") or {}
    event_context = state.get("event_context") or {}
    news_context = state.get("news_context") or default_news_context
    signal = serialize_signal(state.get("signal") or {})
    decision = state.get("decision") or {}
    report = state.get("report") or {}
    env = state.get("env") or {}

    run_doc: RunDocument = {
        "market_id": market_id,
        "event_id": event_id,
        "polymarket_url": state.get("polymarket_url") or state.get("market_url") or "",
        "slug": state.get("slug") or market_snapshot.get("slug", "unknown-market"),
        "run_at": state.get("run_at") or timestamp,
        "horizon": state.get("horizon") or "24h",
        "strategy_preset": state.get("strategy_preset") or "Balanced",
        "strategy_params": state.get("strategy_params") or {},
        "market_snapshot": market_snapshot,
        "event_context": event_context,
        "news_context": news_context,
        "signal": signal,
        "decision": decision,
        "report": report,
        "env": env,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    return run_doc


def build_trace_document(
    trace_payload: TracePayload, run_id: ObjectId, timestamp: str
) -> TraceDocument:
    return {
        "run_id": run_id,
        "created_at": timestamp,
        "steps": trace_payload.get("steps", []),
        "raw_state": trace_payload.get("raw_state"),
        "metadata": trace_payload.get("metadata"),
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def persist_run_snapshot_async(state: AgentState) -> Dict[str, Any]:
    """Store the event, market, and run documents plus optional trace (async)."""

    run_timestamp = state.get("run_at") or _utc_now_iso()
    event_doc = await upsert_event_async(build_event_document(state, run_timestamp))
    event_id = event_doc["_id"]

    market_doc = await upsert_market_async(build_market_document(state, run_timestamp, event_id))
    market_id = market_doc["_id"]

    run_doc = build_run_document(state, run_timestamp, event_id, market_id)
    run_object_id = await create_run_async(run_doc)

    trace_id = None
    trace_payload = state.get("trace")
    if isinstance(trace_payload, dict):
        trace_doc = build_trace_document(trace_payload, run_object_id, run_timestamp)
        trace_id = await create_trace_async(trace_doc)
        await attach_trace_to_run_async(run_object_id, trace_id)

    run_doc_for_return = {**run_doc, "_id": run_object_id}
    if trace_id:
        run_doc_for_return["trace_id"] = trace_id

    payload = {
        "run_id": str(run_object_id),
        "event": serialize_document(event_doc),
        "market": serialize_document(market_doc),
        "run": serialize_document(run_doc_for_return),
    }
    if trace_id:
        payload["trace_id"] = str(trace_id)
    return payload


async def init_run_document_async(
    run_id: str,
    market_url: str,
    horizon: str = "24h",
    strategy_preset: str = "Balanced",
    strategy_params: dict[str, Any] | None = None,
) -> ObjectId:
    """Initialize a run document with pending statuses for phased execution."""
    timestamp = _utc_now_iso()

    # Create a minimal run document with pending statuses
    run_doc: RunDocument = {
        "run_id": run_id,
        "polymarket_url": market_url,
        "slug": "pending",  # Will be updated when market is fetched
        "run_at": timestamp,
        "horizon": horizon,
        "strategy_preset": strategy_preset,
        "strategy_params": strategy_params or {},
        "market_snapshot": {},
        "event_context": {},
        "news_context": {
            "tavily_queries": [],
            "articles": [],
            "summary": "",
        },
        "signal": {},
        "decision": {},
        "report": {},
        "env": {},
        "created_at": timestamp,
        "updated_at": timestamp,
        "status": {
            "market": "pending",
            "news": "pending",
            "signal": "pending",
            "report": "pending",
        },
    }

    run_object_id = await create_run_async(run_doc)
    return run_object_id


PHASE_DATA_FIELDS: dict[str, list[str]] = {
    "market": ["market_snapshot", "event_context", "market_options"],
    "news": ["news_context"],
    "signal": ["signal", "decision"],
    "report": ["report"],
}


async def update_run_phase_async(
    run_id: str,
    phase: str,
    status: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Update a specific phase status and optionally update phase data."""
    collection = await runs_collection_async()
    update_doc: dict[str, Any] = {
        f"status.{phase}": status,
        "updated_at": _utc_now_iso(),
    }

    if data:
        allowed_fields = PHASE_DATA_FIELDS.get(phase, [])
        for field in allowed_fields:
            if field in data:
                update_doc[field] = data[field]
                logger.info(f"Updating {field}", run_id=run_id, has_data=bool(data[field]))

    result = await collection.update_one({"run_id": run_id}, {"$set": update_doc})
    logger.info(
        "Run phase updated",
        run_id=run_id,
        phase=phase,
        status=status,
        matched_count=result.matched_count,
        modified_count=result.modified_count,
    )

    if result.matched_count == 0:
        logger.warning("Run document not found for update", run_id=run_id, phase=phase)


async def update_run_with_event_and_market_async(
    run_id: str,
    state: AgentState,
) -> tuple[ObjectId, ObjectId]:
    """Update run document with event and market IDs after they're created."""
    timestamp = state.get("run_at") or _utc_now_iso()
    event_doc = await upsert_event_async(build_event_document(state, timestamp))
    event_id = event_doc["_id"]

    market_doc = await upsert_market_async(build_market_document(state, timestamp, event_id))
    market_id = market_doc["_id"]

    collection = await runs_collection_async()
    
    # Prepare update data
    update_data = {
        "event_id": event_id,
        "market_id": market_id,
        "slug": market_doc.get("slug", "unknown-market"),
        "updated_at": _utc_now_iso(),
    }
    
    # Include selected_market_slug if available (for multi-market events)
    selected_market_slug = state.get("selected_market_slug")
    if selected_market_slug:
        update_data["selected_market_slug"] = selected_market_slug
    
    await collection.update_one(
        {"run_id": run_id},
        {"$set": update_data},
    )

    return event_id, market_id
