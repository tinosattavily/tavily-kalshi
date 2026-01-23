"""Health and debug routes."""

from __future__ import annotations

from typing import Any

import aiohttp
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.schemas.common import HealthResponse
from app.config import KalshiAPI, get_logger
from app.infrastructure.database.client import check_mongodb_health, get_async_db

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
        "kalshi": f"{KalshiAPI.DEMO_BASE}/exchange/status",
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
