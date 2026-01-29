"""Run retrieval routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.core.logging_config import get_logger
from app.db.async_repositories import (
    get_run_async,
    list_recent_runs_async,
    list_runs_by_market_async,
)
from app.schemas import RunResponse, SingleRunResponse
from app.services.resolution_service import (
    check_and_update_run_resolution,
    check_pending_resolutions,
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
    except Exception as e:
        logger.error("Failed to list runs", market_id=market_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve runs. Please try again later.",
        ) from e


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
    except Exception as e:
        logger.error("Failed to list recent runs", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent runs. Please try again later.",
        ) from e


@router.get("/run/{run_id}", response_model=SingleRunResponse)
async def get_run_detail(run_id: str):
    """Get a single run by run_id."""
    logger.debug("Retrieving run", run_id=run_id)

    try:
        doc = await get_run_async(run_id)
        if not doc:
            logger.debug("Run not found", run_id=run_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

        # Check resolution if not already resolved
        existing_resolution = doc.get("resolution", {})
        existing_status = existing_resolution.get("status")
        if existing_status not in ("resolved_yes", "resolved_no", "voided"):
            # Try to check resolution in the background
            try:
                resolution = await check_and_update_run_resolution(run_id)
                if resolution:
                    doc["resolution"] = resolution
            except Exception as res_err:
                logger.debug("Resolution check failed", run_id=run_id, error=str(res_err))

        _log_run_status(run_id, doc)
        return SingleRunResponse(run=doc)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Invalid run ID", run_id=run_id, error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as e:
        logger.error(
            "Failed to retrieve run",
            run_id=run_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve run. Please try again later.",
        ) from e


def _log_run_status(run_id: str, doc: dict) -> None:
    """Log run retrieval with status details."""
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


@router.post("/runs/check-resolutions")
async def check_resolutions(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of runs to check"),
):
    """Check and update resolutions for pending runs.
    
    Scans runs where the market end_date has passed but resolution status is unknown,
    fetches current market status from Polymarket, and updates the resolution field.
    """
    logger.info("Starting resolution check", limit=limit)
    
    try:
        result = await check_pending_resolutions(limit=limit)
        logger.info(
            "Resolution check complete",
            checked=result.get("checked"),
            updated=result.get("updated"),
            errors=result.get("errors"),
        )
        return {
            "checked": result.get("checked", 0),
            "updated": result.get("updated", 0),
            "errors": result.get("errors", 0),
        }
    except Exception as e:
        logger.error("Failed to check resolutions", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check resolutions. Please try again later.",
        ) from e


@router.post("/run/{run_id}/check-resolution")
async def check_single_resolution(run_id: str):
    """Check resolution for a specific run.
    
    Fetches the current market status from Polymarket and updates the run's
    resolution field if the market has resolved.
    """
    logger.info("Checking resolution for run", run_id=run_id)
    
    try:
        resolution = await check_and_update_run_resolution(run_id)
        if not resolution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Run not found or market data unavailable",
            )
        
        return {"resolution": resolution}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to check resolution", run_id=run_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check resolution. Please try again later.",
        ) from e
