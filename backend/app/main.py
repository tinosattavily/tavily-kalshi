"""Main FastAPI application."""

from __future__ import annotations

import os
from typing import Any

import aiohttp
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.logging_config import configure_logging, get_logger
from app.core.polymarket_utils import get_event_and_markets_by_slug
from app.core.resilience import openai_circuit
from app.db.async_client import check_mongodb_health as check_mongodb_health_async
from app.routes import analyze, runs
from app.schemas import HealthResponse

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
configure_logging(log_level=LOG_LEVEL)
logger = get_logger(__name__)

if openai_circuit.state.value == "open":
    logger.info("Resetting OpenAI circuit breaker on startup")
    openai_circuit.reset()

app = FastAPI(
    title="Tavily Signals API",
    description="Multi-agent prediction market analysis API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

allowed_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(analyze.router, prefix="/api", tags=["analysis"])
app.include_router(runs.router, prefix="/api", tags=["runs"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Tavily Signals API", log_level=LOG_LEVEL)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Tavily Signals API")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for safe error responses."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An internal server error occurred. Please try again later.",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    """Basic liveness check."""
    return HealthResponse(status="ok", message="Service is running")


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
async def health_live():
    """Liveness probe - checks if service is alive."""
    return HealthResponse(status="ok", message="Service is alive")


@app.get("/ping-db", tags=["health"])
async def ping_db():
    """Legacy endpoint - ping MongoDB database."""
    try:
        db_healthy, db_message = await check_mongodb_health_async()
        if not db_healthy:
            return JSONResponse(status_code=500, content={"connected": False, "error": db_message})

        from app.db.async_client import get_async_db
        db = await get_async_db()
        pings_collection = db["pings"]
        await pings_collection.insert_one({"msg": "hello from FastAPI", "ok": True})
        count = await pings_collection.count_documents({})

        return {"connected": True, "collection": "pings", "count": count}
    except Exception as e:
        logger.warning("Database ping failed", error=str(e))
        return JSONResponse(status_code=500, content={"connected": False, "error": str(e)})


@app.get("/health/ready", response_model=HealthResponse, tags=["health"])
async def health_ready():
    """Readiness probe - checks if service is ready to serve requests."""
    checks: dict[str, Any] = {}
    all_healthy = True

    db_healthy, checks["mongodb"] = await _check_mongodb_health()
    if not db_healthy:
        all_healthy = False

    api_checks, apis_healthy = await _check_external_apis()
    checks.update(api_checks)
    if not apis_healthy:
        all_healthy = False

    health_status = "ok" if all_healthy else "degraded"
    message = "Service is ready" if all_healthy else "Service is degraded - some dependencies unavailable"

    return HealthResponse(status=health_status, message=message, checks=checks)


async def _check_mongodb_health() -> tuple[bool, dict[str, str]]:
    """Check MongoDB health status."""
    try:
        db_healthy, db_message = await check_mongodb_health_async()
        return db_healthy, {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": db_message,
        }
    except Exception as e:
        logger.warning("MongoDB health check failed", error=str(e))
        return False, {"status": "unhealthy", "message": str(e)}


async def _check_external_apis() -> tuple[dict[str, dict[str, str]], bool]:
    """Check external API health statuses."""
    external_apis = {
        "polymarket": "https://gamma-api.polymarket.com/markets?slug=test",
        "tavily": "https://api.tavily.com/search",
        "openai": "https://api.openai.com/v1/models",
    }
    checks: dict[str, dict[str, str]] = {}
    all_healthy = True

    async with aiohttp.ClientSession() as session:
        for service_name, url in external_apis.items():
            healthy, check_result = await _check_single_api(session, service_name, url)
            checks[service_name] = check_result
            if not healthy:
                all_healthy = False

    return checks, all_healthy


async def _check_single_api(
    session: aiohttp.ClientSession, service_name: str, url: str
) -> tuple[bool, dict[str, str]]:
    """Check a single external API health."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            healthy = resp.status < 500
            return healthy, {"status": "healthy" if healthy else "unhealthy", "message": f"HTTP {resp.status}"}
    except Exception as e:
        logger.warning(f"{service_name} health check failed", error=str(e))
        return False, {"status": "unhealthy", "message": str(e)}


@app.get("/debug/polymarket/{slug:path}", tags=["debug"])
async def debug_polymarket(slug: str):
    """Debug endpoint to inspect raw Polymarket API responses.

    Development/debugging only - disabled in production.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        logger.warning("Debug endpoint accessed in production", slug=slug)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    try:
        from app.config import PolymarketAPI
        from app.core.cache import polymarket_cache
        from app.core.polymarket_utils import fetch_json_async

        _clear_cache_for_slug(polymarket_cache, PolymarketAPI.GAMMA_API, slug)

        events_response = await fetch_json_async(f"{PolymarketAPI.GAMMA_API}/events", params={"slug": slug})
        markets_response = await fetch_json_async(f"{PolymarketAPI.GAMMA_API}/markets", params={"slug": slug})
        event, markets = await get_event_and_markets_by_slug(slug)

        return _build_debug_response(slug, events_response, markets_response, event, markets)
    except Exception as e:
        logger.error("Debug endpoint error", slug=slug, error=str(e), exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e), "slug": slug})


def _clear_cache_for_slug(cache, api_base: str, slug: str) -> None:
    """Clear cached data for a given slug."""
    params = {"slug": slug}
    cache_key_events = f"polymarket:{api_base}/events:{hash(str(params))}"
    cache_key_markets = f"polymarket:{api_base}/markets:{hash(str(params))}"
    cache._cache.pop(cache_key_events, None)
    cache._cache.pop(cache_key_markets, None)


def _build_debug_response(
    slug: str,
    events_response: Any,
    markets_response: Any,
    event: dict | None,
    markets: list | None,
) -> dict[str, Any]:
    """Build debug response with raw and processed data."""
    raw_comment_count = _extract_comment_count(events_response)

    return {
        "slug": slug,
        "raw_events_response": events_response,
        "raw_markets_response": markets_response,
        "processed_event": event,
        "processed_markets_count": len(markets) if markets else 0,
        "processed_markets_sample": markets[:2] if markets else [],
        "commentCount_from_event": event.get("commentCount") if event else None,
        "commentCount_from_raw_events": raw_comment_count,
        "pydantic_validation_attempted": True,
        "raw_event_commentCount": raw_comment_count,
    }


def _extract_comment_count(events_response: Any) -> int | None:
    """Extract comment count from events response."""
    if isinstance(events_response, dict) and events_response.get("data"):
        return events_response["data"][0].get("commentCount") if events_response["data"] else None
    if isinstance(events_response, list) and events_response:
        return events_response[0].get("commentCount")
    return None
