"""Run retrieval routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.schemas.responses import RunResponse, SingleRunResponse
from app.config import get_logger
from app.infrastructure.database.repositories import (
    get_run_async,
    list_recent_runs_async,
    list_runs_by_market_async,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/runs", response_model=RunResponse)
async def list_runs(market_id: str = Query(..., description="MongoDB ObjectId for the market")):
    """List runs for a given market ID."""
    logger.debug("Listing runs for market", market_id=market_id)
    try:
        runs = await list_runs_by_market_async(market_id)
        logger.info("Runs retrieved", market_id=market_id, count=len(runs))
        return RunResponse(market_id=market_id, runs=runs)
    except ValueError as exc:
        logger.warning("Invalid market ID", market_id=market_id, error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Failed to list runs", market_id=market_id, error=str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve runs. Please try again later.",
        ) from exc


@router.get("/runs/recent", response_model=RunResponse)
async def list_recent_runs(
    limit: int = Query(20, ge=1, le=50, description="Maximum number of runs to return"),
):
    """List recent runs across all markets, sorted by run_at descending."""
    logger.debug("Listing recent runs", limit=limit)
    try:
        runs = await list_recent_runs_async(limit=limit)
        logger.info("Recent runs retrieved", count=len(runs))
        return RunResponse(market_id="all", runs=runs)
    except Exception as exc:
        logger.error("Failed to list recent runs", error=str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent runs. Please try again later.",
        ) from exc


@router.get("/run/{run_id}", response_model=SingleRunResponse)
async def get_run_detail(run_id: str):
    """Get a single run by run_id."""
    logger.debug("Retrieving run", run_id=run_id)
    try:
        doc = await get_run_async(run_id)
        if not doc:
            logger.debug("Run not found", run_id=run_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

        run_status = doc.get("status", {})
        logger.info(
            "Run retrieved",
            run_id=run_id,
            has_status=bool(run_status),
            market_status=run_status.get("market"),
            news_status=run_status.get("news"),
            signal_status=run_status.get("signal"),
            report_status=run_status.get("report"),
            has_market_snapshot=bool(doc.get("market_snapshot")),
            has_news_context=bool(doc.get("news_context")),
            has_signal=bool(doc.get("signal")),
            has_report=bool(doc.get("report")),
        )
        return SingleRunResponse(run=doc)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Invalid run ID", run_id=run_id, error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(
            "Failed to retrieve run",
            run_id=run_id,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve run: {str(exc)}",
        ) from exc
