"""Request models for API endpoints."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.domains.analysis.schemas import AnalysisConfiguration, StrategyParamsModel
from app.domains.markets.canonicalization import detect_venue
from app.shared.types import Horizon, StrategyPreset


class AnalyzeRequest(BaseModel):
    """Request model for prediction-market analysis."""

    market_url: HttpUrl = Field(..., description="Kalshi or Polymarket market/event URL")
    selected_market_id: Optional[str] = Field(
        None, description="Selected venue-native market id for multi-market events"
    )
    selected_market_slug: Optional[str] = Field(
        None, description="Deprecated Polymarket compatibility field"
    )
    selected_ticker: Optional[str] = Field(
        None, description="Deprecated Kalshi compatibility field"
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
    def validate_supported_market_url(cls, v: HttpUrl) -> HttpUrl:
        detect_venue(str(v))
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "market_url": "https://polymarket.com/event/fed-decision-in-december",
                "selected_market_id": None,
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
