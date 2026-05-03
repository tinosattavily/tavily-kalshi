"""Main FastAPI application."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.analyze import router as analyze_router
from app.api.routes.health import router as health_router
from app.api.routes.runs import router as runs_router
from app.config import get_logger
from app.config.logging import configure_logging
from app.infrastructure.http.resilience import openai_circuit

# Configure logging on startup
log_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(log_level=log_level)
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage application startup/shutdown lifecycle."""
    logger.info("Starting Tavily Signals API", log_level=log_level)
    if openai_circuit.state.value == "open":
        logger.info("Resetting OpenAI circuit breaker on startup")
        openai_circuit.reset()
    try:
        yield
    finally:
        logger.info("Shutting down Tavily Signals API")


# Create FastAPI app
app = FastAPI(
    title="Tavily Signals API",
    description="Multi-agent prediction market analysis API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
# Get allowed origins from environment or default to localhost for development
allowed_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
# Regex allows any Vercel preview/prod URL without explicit listing
allowed_origin_regex = os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app$")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(analyze_router, prefix="/api", tags=["analysis"])
app.include_router(runs_router, prefix="/api", tags=["runs"])
app.include_router(health_router, tags=["health"])


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


