from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId

from app.infrastructure.database.repositories import (
    attach_trace_to_run_async,
    create_run_async,
    create_trace_async,
    runs_collection_async,
    upsert_event_async,
    upsert_market_async,
)
from app.infrastructure.database.utils import serialize_document
from app.orchestration.state import AgentState, TracePayload
from app.shared.types import EventDocument, MarketDocument, RunDocument, TraceDocument


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
    market_snapshot = state.get("market_snapshot") or {}
    event_context = state.get("event_context") or {}
    news_context = state.get("news_context") or {
        "tavily_queries": [],
        "articles": [],
        "summary": "",
    }
    signal_raw = state.get("signal") or {}
    decision = state.get("decision") or {}
    report = state.get("report") or {}
    env = state.get("env") or {}

    # Serialize signal - handle both Pydantic model and dict
    if hasattr(signal_raw, "model_dump"):
        # Pydantic v2
        signal = signal_raw.model_dump()
    elif hasattr(signal_raw, "dict"):
        # Pydantic v1
        signal = signal_raw.dict()
    elif isinstance(signal_raw, dict):
        # Already a dict
        signal = signal_raw
    else:
        # Fallback to empty dict
        signal = {}

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


async def update_run_phase_async(
    run_id: str,
    phase: str,
    status: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Update a specific phase status and optionally update phase data."""
    from app.config import get_logger

    logger = get_logger(__name__)

    collection = await runs_collection_async()
    update_doc: dict[str, Any] = {
        f"status.{phase}": status,
        "updated_at": _utc_now_iso(),
    }

    if data:
        # Update phase-specific data fields
        if phase == "market":
            if "market_snapshot" in data:
                update_doc["market_snapshot"] = data["market_snapshot"]
                logger.info(
                    "Updating market_snapshot",
                    run_id=run_id,
                    has_snapshot=bool(data["market_snapshot"]),
                )
            if "event_context" in data:
                update_doc["event_context"] = data["event_context"]
                logger.info(
                    "Updating event_context",
                    run_id=run_id,
                    has_context=bool(data["event_context"]),
                )
            if "market_options" in data:
                update_doc["market_options"] = data["market_options"]
                logger.info(
                    "Updating market_options",
                    run_id=run_id,
                    options_count=(
                        len(data["market_options"])
                        if isinstance(data["market_options"], list)
                        else 0
                    ),
                )
        elif phase == "news":
            if "news_context" in data:
                update_doc["news_context"] = data["news_context"]
                logger.info(
                    "Updating news_context",
                    run_id=run_id,
                    has_context=bool(data["news_context"]),
                )
        elif phase == "signal":
            if "signal" in data:
                update_doc["signal"] = data["signal"]
                logger.info("Updating signal", run_id=run_id, has_signal=bool(data["signal"]))
            if "decision" in data:
                update_doc["decision"] = data["decision"]
                logger.info("Updating decision", run_id=run_id, has_decision=bool(data["decision"]))
        elif phase == "report":
            if "report" in data:
                update_doc["report"] = data["report"]
                logger.info("Updating report", run_id=run_id, has_report=bool(data["report"]))

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
    await collection.update_one(
        {"run_id": run_id},
        {
            "$set": {
                "event_id": event_id,
                "market_id": market_id,
                "slug": market_doc.get("slug", "unknown-market"),
                "updated_at": _utc_now_iso(),
            }
        },
    )

    return event_id, market_id
