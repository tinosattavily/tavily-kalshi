"""Health and debug routes."""

from __future__ import annotations

import os
from typing import Any

import aiohttp
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.schemas.common import HealthResponse
from app.config import PolymarketAPI, get_logger
from app.domains.markets.fetcher import get_event_and_markets_by_slug
from app.infrastructure.database.client import check_mongodb_health, get_async_db
from app.infrastructure.http.cache import polymarket_cache
from app.infrastructure.http.polymarket import fetch_json_async

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    """Basic liveness check."""
    return HealthResponse(status="ok", message="Service is running")


@router.get("/health/live", response_model=HealthResponse, tags=["health"])
async def health_live():
    """Liveness probe - checks if service is alive."""
    return HealthResponse(status="ok", message="Service is alive")


@router.get("/ping-db", tags=["health"])
async def ping_db():
    """Legacy endpoint - ping MongoDB database."""
    try:
        db_healthy, db_message = await check_mongodb_health()
        if not db_healthy:
            return JSONResponse(
                status_code=500,
                content={"connected": False, "error": db_message},
            )

        db = await get_async_db()
        pings_collection = db["pings"]
        await pings_collection.insert_one({"msg": "hello from FastAPI", "ok": True})
        count = await pings_collection.count_documents({})

        return {
            "connected": True,
            "collection": "pings",
            "count": count,
        }
    except Exception as exc:
        logger.warning("Database ping failed", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"connected": False, "error": str(exc)},
        )


@router.get("/health/ready", response_model=HealthResponse, tags=["health"])
async def health_ready():
    """Readiness probe - checks if service is ready to serve requests."""
    checks: dict[str, Any] = {}
    all_healthy = True

    try:
        db_healthy, db_message = await check_mongodb_health()
        checks["mongodb"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": db_message,
        }
        if not db_healthy:
            all_healthy = False
    except Exception as exc:
        logger.warning("MongoDB health check failed", error=str(exc))
        checks["mongodb"] = {"status": "unhealthy", "message": str(exc)}
        all_healthy = False

    external_apis = {
        "polymarket": f"{PolymarketAPI.GAMMA_API}/markets?slug=test",
        "tavily": "https://api.tavily.com/search",
        "openai": "https://api.openai.com/v1/models",
    }

    async with aiohttp.ClientSession() as session:
        for service_name, url in external_apis.items():
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    checks[service_name] = {
                        "status": "healthy" if resp.status < 500 else "unhealthy",
                        "message": f"HTTP {resp.status}",
                    }
                    if resp.status >= 500:
                        all_healthy = False
            except Exception as exc:
                logger.warning(f"{service_name} health check failed", error=str(exc))
                checks[service_name] = {"status": "unhealthy", "message": str(exc)}
                all_healthy = False

    status_value = "ok" if all_healthy else "degraded"
    message = (
        "Service is ready"
        if all_healthy
        else "Service is degraded - some dependencies unavailable"
    )

    return HealthResponse(status=status_value, message=message, checks=checks)


@router.get("/debug/polymarket/{slug:path}", tags=["debug"])
async def debug_polymarket(slug: str):
    """Debug endpoint to inspect raw Polymarket API responses."""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        logger.warning("Debug endpoint accessed in production", slug=slug)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    try:
        params_events = {"slug": slug}
        params_markets = {"slug": slug}
        cache_key_events = f"polymarket:{PolymarketAPI.GAMMA_API}/events:{hash(str(params_events))}"
        cache_key_markets = (
            f"polymarket:{PolymarketAPI.GAMMA_API}/markets:{hash(str(params_markets))}"
        )
        polymarket_cache._cache.pop(cache_key_events, None)
        polymarket_cache._cache.pop(cache_key_markets, None)

        events_response = await fetch_json_async(
            f"{PolymarketAPI.GAMMA_API}/events", params={"slug": slug}
        )
        markets_response = await fetch_json_async(
            f"{PolymarketAPI.GAMMA_API}/markets", params={"slug": slug}
        )

        event, markets = await get_event_and_markets_by_slug(slug)

        return {
            "slug": slug,
            "raw_events_response": events_response,
            "raw_markets_response": markets_response,
            "processed_event": event,
            "processed_markets_count": len(markets) if markets else 0,
            "processed_markets_sample": markets[:2] if markets else [],
            "commentCount_from_event": event.get("commentCount") if event else None,
            "commentCount_from_raw_events": (
                events_response.get("data", [{}])[0].get("commentCount")
                if isinstance(events_response, dict) and events_response.get("data")
                else (
                    events_response[0].get("commentCount")
                    if isinstance(events_response, list) and len(events_response) > 0
                    else None
                )
            ),
            "pydantic_validation_attempted": True,
            "raw_event_commentCount": (
                events_response[0].get("commentCount")
                if isinstance(events_response, list) and len(events_response) > 0
                else None
            ),
        }
    except Exception as exc:
        logger.error("Debug endpoint error", slug=slug, error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "slug": slug},
        )
