"""Request models for API endpoints."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.domains.analysis.schemas import AnalysisConfiguration, StrategyParamsModel
from app.domains.markets.parsing import is_kalshi_url, parse_kalshi_url
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


class KalshiAnalyzeRequest(BaseModel):
    """Request model for Kalshi market analysis."""

    url: str = Field(..., description="Kalshi market or event URL")
    selected_ticker: Optional[str] = Field(
        None, description="Selected market ticker when analyzing multi-market events"
    )
    strategy_preset: Optional[StrategyPreset] = Field(
        "Balanced", description="Strategy risk preset"
    )
    configuration: Optional[AnalysisConfiguration] = Field(
        None, description="Analysis configuration options"
    )

    @field_validator("url")
    @classmethod
    def validate_kalshi_url(cls, v: str) -> str:
        """Validate that URL is a valid Kalshi URL."""
        if not is_kalshi_url(v):
            raise ValueError("URL must be a valid Kalshi market or event URL")

        ticker, event_ticker, url_type = parse_kalshi_url(v)
        if url_type == "unknown":
            raise ValueError("Could not parse market or event from URL")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://kalshi.com/markets/INXD-25JAN17-B24999",
                "selected_ticker": None,
                "strategy_preset": "Balanced",
            }
        }
    )


class MarketSelectionRequest(BaseModel):
    """Request to select a specific market from a multi-market event."""

    event_ticker: str = Field(..., description="Kalshi event ticker")
    selected_ticker: str = Field(..., description="Selected market ticker")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_ticker": "INXD-25JAN17",
                "selected_ticker": "INXD-25JAN17-B24999",
            }
        }
    )


__all__ = [
    "AnalyzeRequest",
    "KalshiAnalyzeRequest",
    "MarketSelectionRequest",
    "AnalysisConfiguration",
    "StrategyParamsModel",
]
