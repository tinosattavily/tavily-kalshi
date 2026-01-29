"""Analysis routes."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.agents.graph import run_analysis_graph
from app.agents.state import AgentState
from app.core.logging_config import get_logger
from app.core.resilience import openai_circuit
from app.schemas import (
    AnalyzeRequest,
    ErrorResponse,
    MarketSelectionResponse,
)
from app.services.phased_analysis import run_analysis_for_run_id
from app.services.run_snapshot import init_run_document_async, persist_run_snapshot_async

logger = get_logger(__name__)
router = APIRouter()

MAX_REQUEST_SIZE = 1024 * 1024  # 1MB


def _check_request_size(request: Request) -> None:
    """Validate request size is within limits."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_SIZE:
        logger.warning("Request too large", size=content_length, limit=MAX_REQUEST_SIZE)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Request body exceeds maximum size of {MAX_REQUEST_SIZE} bytes",
        )


def _build_agent_state(payload: AnalyzeRequest) -> AgentState:
    """Build AgentState dict from request payload."""
    config = payload.configuration
    strategy_params = payload.strategy_params or {}

    if config and config.min_confidence:
        strategy_params = {**strategy_params, "min_confidence": config.min_confidence}

    state_dict: AgentState = {
        "market_url": str(payload.market_url),
        "polymarket_url": str(payload.market_url),
        "selected_market_slug": payload.selected_market_slug,
        "horizon": payload.horizon or "24h",
        "strategy_preset": payload.strategy_preset or "Balanced",
        "strategy_params": strategy_params,
        "config": _build_config_dict(config) if config else {},
    }
    return state_dict


def _build_config_dict(config) -> dict[str, Any]:
    """Build configuration dict with defaults."""
    return {
        "use_tavily_prompt_agent": config.use_tavily_prompt_agent if config else True,
        "use_news_summary_agent": config.use_news_summary_agent if config else True,
        "max_articles": config.max_articles if config else 15,
        "max_articles_per_query": config.max_articles_per_query if config else 8,
        "min_confidence": config.min_confidence if config else "medium",
        "enable_sentiment_analysis": config.enable_sentiment_analysis if config else True,
    }


def _serialize_signal(signal_raw: Any) -> dict:
    """Serialize signal to dict, handling Pydantic models."""
    if hasattr(signal_raw, "model_dump"):
        return signal_raw.model_dump()
    if hasattr(signal_raw, "dict"):
        return signal_raw.dict()
    if isinstance(signal_raw, dict):
        return signal_raw
    return {}


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
    _check_request_size(request)
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        "Analysis request received",
        request_id=request_id,
        market_url=str(payload.market_url),
        horizon=payload.horizon,
        strategy_preset=payload.strategy_preset,
    )

    try:
        state_dict = _build_agent_state(payload)
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
            ).dict()

        run_id, snapshot = await _persist_run_snapshot(state, request_id)

        response_payload = {
            "run_id": run_id,
            "market_snapshot": state.get("market_snapshot", {}),
            "event_context": state.get("event_context", {}),
            "news_context": state.get("news_context", {}),
            "signal": _serialize_signal(state.get("signal", {})),
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
    except ValueError as e:
        logger.warning("Validation error in analysis", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            "Analysis failed",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again later or contact support if the issue persists.",
        ) from e


async def _persist_run_snapshot(state: dict, request_id: str | None) -> tuple[str, dict | None]:
    """Persist run snapshot to database, returning (run_id, snapshot)."""
    try:
        logger.debug("Persisting run snapshot", request_id=request_id)
        snapshot = await persist_run_snapshot_async(state)
        run_id = snapshot["run_id"]
        logger.info("Run snapshot persisted", request_id=request_id, run_id=run_id)
        return run_id, snapshot
    except Exception as db_error:
        logger.warning(
            "Failed to persist run snapshot",
            request_id=request_id,
            error=str(db_error),
            exc_info=True,
        )
        return "no-db", None


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
    """Start a phased analysis in the background and return a run_id immediately.

    Use GET /api/run/{run_id} to poll for status and partial results.
    """
    _check_request_size(request)
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
        await _init_run_document(run_id, payload, request_id)

        background_tasks.add_task(run_analysis_for_run_id, run_id, payload)
        logger.info("Analysis started in background", request_id=request_id, run_id=run_id)
        return {"run_id": run_id}

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Validation error in analysis start", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            "Failed to start analysis",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start analysis. Please try again later or contact support if the issue persists.",
        ) from e


async def _init_run_document(run_id: str, payload: AnalyzeRequest, request_id: str | None) -> None:
    """Initialize run document in database."""
    try:
        await init_run_document_async(
            run_id=run_id,
            market_url=str(payload.market_url),
            horizon=payload.horizon or "24h",
            strategy_preset=payload.strategy_preset or "Balanced",
            strategy_params=payload.strategy_params or {},
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
