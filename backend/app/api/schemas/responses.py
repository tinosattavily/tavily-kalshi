"""Response models for API endpoints."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.domains.reports.schemas import ReportSection
from app.shared.types import Horizon, StrategyPreset


class MarketSelectionResponse(BaseModel):
    """Response when market selection is required."""

    requires_market_selection: bool = Field(
        True, description="Whether user must pick a market"
    )
    event_context: dict[str, Any] = Field(..., description="Event context for UI")
    market_options: list[dict[str, Any]] = Field(
        ..., description="Available market options"
    )


class AnalyzeResponse(BaseModel):
    """Response model for /api/analyze endpoint."""

    run_id: str = Field(..., description="Unique run identifier")
    market_snapshot: dict[str, Any] = Field(..., description="Market state snapshot")
    event_context: dict[str, Any] = Field(..., description="Event context")
    news_context: dict[str, Any] = Field(..., description="News aggregation context")
    signal: dict[str, Any] = Field(..., description="Generated trading signal")
    decision: dict[str, Any] = Field(..., description="Trading decision")
    report: dict[str, Any] = Field(..., description="Analysis report")
    strategy_preset: StrategyPreset = Field(
        ..., description="Strategy preset used"
    )
    strategy_params: dict[str, Any] = Field(
        ..., description="Strategy parameters used"
    )
    horizon: Horizon = Field(..., description="Analysis horizon")
    snapshot: Optional[dict[str, Any]] = Field(
        None, description="Persisted snapshot metadata"
    )


class RunResponse(BaseModel):
    """Response model for run endpoints."""

    market_id: str = Field(..., description="Market ID")
    runs: list[dict[str, Any]] = Field(..., description="List of runs for the market")


class SingleRunResponse(BaseModel):
    """Response model for single run endpoint."""

    run: dict[str, Any] = Field(..., description="Run document")


__all__ = [
    "AnalyzeResponse",
    "MarketSelectionResponse",
    "RunResponse",
    "SingleRunResponse",
    "ReportSection",
]
