# app/domains/analysis/schemas.py
"""Pydantic models for analysis domain."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.shared.types import ConfidenceLevel, Horizon


class Signal(BaseModel):
    """Comprehensive trading signal with probabilities, edge, Kelly sizing, and recommendations."""

    # Beliefs
    market_prob: float = Field(
        ..., ge=0.0, le=1.0, description="p_mkt (implied by Polymarket price)"
    )
    model_prob: float = Field(
        ..., ge=0.0, le=1.0, description="p_model (posterior after news/analysis)"
    )
    edge_pct: float = Field(..., description="model_prob - market_prob (in probability points)")

    # Value & sizing
    expected_value_per_dollar: float = Field(..., description="Same as edge_pct in a $1 binary")
    kelly_fraction_yes: float = Field(
        ..., description="Unconstrained Kelly stake on YES in [0,1] (can be negative)"
    )
    kelly_fraction_no: float = Field(
        ..., description="Unconstrained Kelly stake on NO in [0,1] (can be negative)"
    )

    # Uncertainty / confidence
    confidence_level: ConfidenceLevel = Field(
        ..., description="Confidence level: low, medium, or high"
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score in [0,1]")

    # Action & targets
    recommended_action: Literal["buy_yes", "buy_no", "reduce_yes", "reduce_no", "hold"] = Field(
        ..., description="Recommended trading action"
    )
    recommended_size_fraction: float = Field(
        ..., ge=0.0, le=1.0, description="Final, capped fraction, e.g. max 0.15"
    )
    target_take_profit_prob: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Take profit if market_prob >= this value"
    )
    target_stop_loss_prob: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Stop out if market_prob <= this value"
    )

    # Metadata
    horizon: Horizon = Field(..., description="Time horizon: intraday, 24h, or to_resolution")
    rationale_short: Optional[str] = Field(None, description="One-line explanation")
    rationale_long: Optional[str] = Field(None, description="Paragraph explanation (optional)")


class StrategyParamsModel(BaseModel):
    """Strategy parameters model."""

    min_edge_pct: float = Field(..., ge=0.0, le=1.0, description="Minimum edge percentage")
    min_confidence: ConfidenceLevel = Field(..., description="Minimum confidence level")
    max_capital_pct: float = Field(..., ge=0.0, le=1.0, description="Maximum capital percentage")
    max_kelly_fraction: float = Field(
        0.25, ge=0.0, le=1.0, description="Maximum Kelly fraction to use"
    )
    risk_off: bool = Field(False, description="If True, no new positions")


class AnalysisConfiguration(BaseModel):
    """Configuration options for analysis agents and behavior."""

    use_tavily_prompt_agent: bool = Field(
        True, description="Use Tavily prompt agent (if False, use fallback queries)"
    )
    use_news_summary_agent: bool = Field(
        True, description="Use news summary agent (if False, use fallback summary)"
    )
    max_articles: int = Field(
        15, ge=5, le=30, description="Maximum number of articles to include in analysis"
    )
    max_articles_per_query: int = Field(
        8, ge=5, le=12, description="Maximum results per Tavily search query"
    )
    min_confidence: ConfidenceLevel = Field(
        "medium", description="Minimum confidence level for trading signals"
    )
    enable_sentiment_analysis: bool = Field(
        True, description="Enable sentiment analysis on articles"
    )
