"""Async database repository functions using motor."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from app.core.logging_config import get_logger
from app.db.async_client import get_async_db
from app.db.models import EventDocument, MarketDocument, RunDocument, TraceDocument
from app.db.utils import serialize_document

logger = get_logger(__name__)

_INDEXES_CREATED = False


async def events_collection_async() -> AsyncIOMotorCollection:
    db = await get_async_db()
    return db["events"]


async def markets_collection_async() -> AsyncIOMotorCollection:
    db = await get_async_db()
    return db["markets"]


async def runs_collection_async() -> AsyncIOMotorCollection:
    db = await get_async_db()
    return db["runs"]


async def traces_collection_async() -> AsyncIOMotorCollection:
    db = await get_async_db()
    return db["traces"]


async def ensure_indexes_async() -> None:
    global _INDEXES_CREATED
    if _INDEXES_CREATED:
        return
    events_coll = await events_collection_async()
    markets_coll = await markets_collection_async()
    runs_coll = await runs_collection_async()
    traces_coll = await traces_collection_async()

    await events_coll.create_index("slug", unique=True)
    await markets_coll.create_index("slug", unique=True)
    await markets_coll.create_index("polymarket_url", unique=True)
    await markets_coll.create_index("event_id")
    await runs_coll.create_index([("market_id", 1), ("run_at", -1)])
    await runs_coll.create_index([("event_id", 1), ("run_at", -1)])
    await runs_coll.create_index("slug")
    await traces_coll.create_index("run_id")
    _INDEXES_CREATED = True


async def _upsert_by_slug(
    collection: AsyncIOMotorCollection,
    doc: Dict[str, Any],
    doc_type: str,
) -> Dict[str, Any]:
    """Generic upsert operation by slug field."""
    slug = doc.get("slug")
    if not slug:
        raise ValueError(f"{doc_type} slug is required to upsert.")

    insert_doc = {k: v for k, v in doc.items() if k != "updated_at"}
    updated_at = doc.get("updated_at")
    update_doc = {"updated_at": updated_at} if updated_at else {}

    result = await collection.find_one_and_update(
        {"slug": slug},
        {"$setOnInsert": insert_doc, "$set": update_doc},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return result  # type: ignore[return-value]


async def upsert_event_async(doc: EventDocument) -> EventDocument:
    """Upsert an event document (async)."""
    await ensure_indexes_async()
    collection = await events_collection_async()
    return await _upsert_by_slug(collection, doc, "Event")  # type: ignore[return-value]


async def upsert_market_async(doc: MarketDocument) -> MarketDocument:
    """Upsert a market document (async)."""
    await ensure_indexes_async()
    collection = await markets_collection_async()
    return await _upsert_by_slug(collection, doc, "Market")  # type: ignore[return-value]


async def create_run_async(doc: RunDocument) -> ObjectId:
    """Create a run document (async)."""
    await ensure_indexes_async()
    collection = await runs_collection_async()
    result = await collection.insert_one(doc)
    return result.inserted_id


async def create_trace_async(doc: TraceDocument) -> ObjectId:
    """Create a trace document (async)."""
    await ensure_indexes_async()
    collection = await traces_collection_async()
    result = await collection.insert_one(doc)
    return result.inserted_id


async def attach_trace_to_run_async(run_id: ObjectId, trace_id: ObjectId) -> None:
    """Attach a trace to a run (async)."""
    collection = await runs_collection_async()
    await collection.update_one({"_id": run_id}, {"$set": {"trace_id": trace_id}})


async def get_run_async(run_id: str) -> Optional[Dict[str, Any]]:
    """Get a run by ID (async). Supports both ObjectId and run_id string."""
    try:
        await ensure_indexes_async()
    except Exception as e:
        logger.warning("Failed to ensure indexes", error=str(e))

    try:
        collection = await runs_collection_async()

        # Try ObjectId first (for backward compatibility)
        try:
            object_id = ObjectId(run_id)
            doc = await collection.find_one({"_id": object_id})
            if doc:
                return serialize_document(doc)
        except (InvalidId, TypeError):
            pass

        # Try run_id string (for new phased analysis)
        doc = await collection.find_one({"run_id": run_id})
        if doc:
            return serialize_document(doc)

        return None
    except Exception as e:
        logger.error("Error retrieving run", run_id=run_id, error=str(e), exc_info=True)
        raise


async def list_runs_by_market_async(market_id: str) -> List[Dict[str, Any]]:
    """List runs for a market (async)."""
    await ensure_indexes_async()
    try:
        market_object_id = ObjectId(market_id)
    except (InvalidId, TypeError) as err:
        raise ValueError("market_id must be a valid ObjectId string.") from err

    collection = await runs_collection_async()
    cursor = collection.find({"market_id": market_object_id}).sort("run_at", -1)
    return [serialize_document(doc) async for doc in cursor]


async def list_recent_runs_async(limit: int = 20) -> List[Dict[str, Any]]:
    """List recent complete runs across all markets (async), sorted by run_at descending.
    
    Only returns runs where all phases (market, news, signal, report) have status "done".
    Incomplete runs are filtered out since they cannot be properly rendered.
    """
    await ensure_indexes_async()
    collection = await runs_collection_async()
    # Filter for complete runs: all four phases must be "done"
    # Ensure status field exists and all required phases are done
    query = {
        "status": {"$exists": True},
        "status.market": "done",
        "status.news": "done",
        "status.signal": "done",
        "status.report": "done",
    }
    cursor = collection.find(query).sort("run_at", -1).limit(limit)
    return [serialize_document(doc) async for doc in cursor]


async def get_runs_pending_resolution(limit: int = 50) -> List[Dict[str, Any]]:
    """Get runs that need resolution checking.
    
    Returns runs where:
    - resolution.status is None, "pending", or doesn't exist
    - All phases are complete (status.report = "done")
    - Has a valid slug
    
    Args:
        limit: Maximum number of runs to return
        
    Returns:
        List of run documents needing resolution check
    """
    await ensure_indexes_async()
    collection = await runs_collection_async()
    
    query = {
        # Must be a complete run
        "status.report": "done",
        # Has a valid slug
        "slug": {"$exists": True, "$ne": "pending"},
        # Resolution not yet determined (or pending)
        "$or": [
            {"resolution": {"$exists": False}},
            {"resolution.status": {"$exists": False}},
            {"resolution.status": "pending"},
        ],
    }
    
    cursor = collection.find(query).sort("run_at", -1).limit(limit)
    return [serialize_document(doc) async for doc in cursor]


async def update_run_resolution(run_id: str, resolution: Dict[str, Any]) -> bool:
    """Update a run's resolution data.
    
    Args:
        run_id: Run ID (string identifier)
        resolution: Resolution data to set
        
    Returns:
        True if update was successful, False otherwise
    """
    from datetime import datetime, timezone
    
    collection = await runs_collection_async()
    
    update_doc = {
        "resolution": resolution,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    
    # Try by run_id string first
    result = await collection.update_one(
        {"run_id": run_id},
        {"$set": update_doc},
    )
    
    if result.matched_count > 0:
        logger.info("Updated run resolution", run_id=run_id, modified=result.modified_count)
        return True
    
    # Try by ObjectId
    try:
        object_id = ObjectId(run_id)
        result = await collection.update_one(
            {"_id": object_id},
            {"$set": update_doc},
        )
        if result.matched_count > 0:
            logger.info("Updated run resolution by ObjectId", run_id=run_id, modified=result.modified_count)
            return True
    except (InvalidId, TypeError):
        pass
    
    logger.warning("Run not found for resolution update", run_id=run_id)
    return False