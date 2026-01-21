"""Request models for API endpoints."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.domains.analysis.schemas import AnalysisConfiguration, StrategyParamsModel
from app.shared.types import Horizon, StrategyPreset


class AnalyzeRequest(BaseModel):
    """Request model for /api/analyze endpoint."""

    market_url: HttpUrl = Field(..., description="Polymarket event or market URL")
    selected_market_slug: Optional[str] = Field(
        None, description="Selected market slug when multiple markets exist"
    )
    horizon: Optional[Horizon] = Field("24h", description="Analysis time horizon")
    strategy_preset: Optional[StrategyPreset] = Field(
        "Balanced", description="Strategy risk preset"
    )
    strategy_params: Optional[dict[str, Any]] = Field(
        None, description="Optional strategy parameter overrides"
    )
    configuration: Optional[AnalysisConfiguration] = Field(
        None, description="Analysis configuration options"
    )

    @field_validator("market_url")
    @classmethod
    def validate_polymarket_url(cls, v: HttpUrl) -> HttpUrl:
        """Validate that URL is a Polymarket URL."""
        url_str = str(v)
        if "polymarket.com" not in url_str.lower():
            raise ValueError("URL must be from polymarket.com domain")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "market_url": "https://polymarket.com/event/fed-decision-in-december",
                "selected_market_slug": None,
                "horizon": "24h",
                "strategy_preset": "Balanced",
            }
        }
    )


__all__ = [
    "AnalyzeRequest",
    "AnalysisConfiguration",
    "StrategyParamsModel",
]
