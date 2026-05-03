"""Analysis routes."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.api.schemas.common import ErrorResponse
from app.api.schemas.requests import AnalyzeRequest
from app.api.schemas.responses import MarketSelectionResponse
from app.config import get_logger
from app.domains.markets.canonicalization import detect_venue
from app.infrastructure.http.resilience import openai_circuit
from app.orchestration.graph import run_analysis_graph
from app.orchestration.initial_state import build_initial_state
from app.orchestration.phased import run_analysis_for_run_id
from app.orchestration.snapshot import init_run_document_async, persist_run_snapshot_async
from app.shared.exceptions import (
    EventNotFoundError,
    MarketNotFoundError,
    UnsupportedVenueError,
    VenueUrlParseError,
)

logger = get_logger(__name__)
router = APIRouter()

# Request size limit: 1MB
MAX_REQUEST_SIZE = 1024 * 1024


def _clear_structlog_context() -> None:
    try:
        import structlog
    except ImportError:
        return
    structlog.contextvars.clear_contextvars()


def _raise_venue_http_error(exc: Exception) -> None:
    if isinstance(exc, UnsupportedVenueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "UnsupportedVenue", "detail": str(exc)},
        ) from exc
    if isinstance(exc, VenueUrlParseError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "VenueUrlParseError", "detail": str(exc)},
        ) from exc
    if isinstance(exc, (MarketNotFoundError, EventNotFoundError)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": type(exc).__name__, "detail": str(exc)},
        ) from exc


@router.post(
    "/analyze",
    response_model=None,
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        413: {"model": ErrorResponse, "description": "Request too large"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def analyze(request: Request, payload: AnalyzeRequest) -> dict[str, Any]:
    """Run the multi-agent analysis for a given market + strategy params."""
    _clear_structlog_context()
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_SIZE:
        logger.warning("Request too large", size=content_length, limit=MAX_REQUEST_SIZE)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Request body exceeds maximum size of {MAX_REQUEST_SIZE} bytes",
        )

    request_id = getattr(request.state, "request_id", None)
    logger.info(
        "Analysis request received",
        request_id=request_id,
        market_url=str(payload.market_url),
        horizon=payload.horizon,
        strategy_preset=payload.strategy_preset,
    )

    try:
        state_dict = build_initial_state(payload)

        logger.debug("Starting analysis graph", request_id=request_id)
        state = await run_analysis_graph(state_dict)

        logger.debug(
            "Analysis graph completed",
            request_id=request_id,
            has_signal=bool(state.get("signal")),
            has_decision=bool(state.get("decision")),
            has_report=bool(state.get("report")),
        )

        if state.get("requires_market_selection"):
            logger.info("Market selection required", request_id=request_id)
            return MarketSelectionResponse(
                requires_market_selection=True,
                event_context=state.get("event_context", {}),
                market_options=state.get("market_options", []),
            ).model_dump()

        run_id = "no-db"
        snapshot = None
        try:
            logger.debug("Persisting run snapshot", request_id=request_id)
            snapshot = await persist_run_snapshot_async(state)
            run_id = snapshot["run_id"]
            logger.info("Run snapshot persisted", request_id=request_id, run_id=run_id)
        except Exception as db_error:
            logger.warning(
                "Failed to persist run snapshot",
                request_id=request_id,
                error=str(db_error),
                exc_info=True,
            )

        signal_raw = state.get("signal", {})
        if hasattr(signal_raw, "model_dump"):
            signal = signal_raw.model_dump()
        elif hasattr(signal_raw, "dict"):
            signal = signal_raw.dict()
        elif isinstance(signal_raw, dict):
            signal = signal_raw
        else:
            signal = {}

        response_payload = {
            "run_id": run_id,
            "market_snapshot": state.get("market_snapshot", {}),
            "event_context": state.get("event_context", {}),
            "news_context": state.get("news_context", {}),
            "signal": signal,
            "decision": state.get("decision", {}),
            "report": state.get("report", {}),
            "strategy_preset": state.get("strategy_preset", "Balanced"),
            "strategy_params": state.get("strategy_params", {}),
            "horizon": state.get("horizon", "24h"),
        }

        if snapshot:
            response_payload["snapshot"] = snapshot

        logger.info("Analysis completed successfully", request_id=request_id, run_id=run_id)
        return response_payload

    except HTTPException:
        raise
    except (UnsupportedVenueError, VenueUrlParseError, MarketNotFoundError, EventNotFoundError) as exc:
        _raise_venue_http_error(exc)
    except ValueError as exc:
        logger.warning("Validation error in analysis", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.error(
            "Analysis failed",
            request_id=request_id,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Analysis failed. Please try again later or contact support if the issue persists."
            ),
        ) from exc


@router.post(
    "/analyze/start",
    response_model=None,
    responses={
        200: {"description": "Analysis started successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        413: {"model": ErrorResponse, "description": "Request too large"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def analyze_start(
    request: Request,
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Start a phased analysis in the background and return a run_id immediately."""
    _clear_structlog_context()
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_SIZE:
        logger.warning("Request too large", size=content_length, limit=MAX_REQUEST_SIZE)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Request body exceeds maximum size of {MAX_REQUEST_SIZE} bytes",
        )

    request_id = getattr(request.state, "request_id", None)
    logger.info(
        "Analysis start request received",
        request_id=request_id,
        market_url=str(payload.market_url),
        horizon=payload.horizon,
        strategy_preset=payload.strategy_preset,
    )

    try:
        run_id = f"run-{uuid4().hex}"

        try:
            venue = detect_venue(str(payload.market_url))
        except UnsupportedVenueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "UnsupportedVenue", "detail": str(exc)},
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "UnsupportedVenue", "detail": str(exc)},
            ) from exc

        try:
            await init_run_document_async(
                run_id=run_id,
                market_url=str(payload.market_url),
                horizon=payload.horizon or "24h",
                strategy_preset=payload.strategy_preset or "Balanced",
                strategy_params=payload.strategy_params or {},
                venue=venue,
            )
            logger.debug("Run document initialized", request_id=request_id, run_id=run_id)
        except Exception as db_error:
            logger.warning(
                "Failed to initialize run document",
                request_id=request_id,
                run_id=run_id,
                error=str(db_error),
                exc_info=True,
            )

        background_tasks.add_task(run_analysis_for_run_id, run_id, payload)

        logger.info("Analysis started in background", request_id=request_id, run_id=run_id)
        return {"run_id": run_id}

    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning(
            "Validation error in analysis start", request_id=request_id, error=str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to start analysis",
            request_id=request_id,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Failed to start analysis. Please try again later "
                "or contact support if the issue persists."
            ),
        ) from exc


@router.post("/reset-circuit-breaker", tags=["admin"])
async def reset_circuit_breaker():
    """Reset the OpenAI circuit breaker to allow API calls again."""
    old_state = openai_circuit.state.value
    openai_circuit.reset()
    logger.info("Circuit breaker reset via API", old_state=old_state)
    return {
        "message": "Circuit breaker reset successfully",
        "old_state": old_state,
        "new_state": openai_circuit.state.value,
    }
