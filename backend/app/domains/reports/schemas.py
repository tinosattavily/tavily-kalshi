# app/domains/reports/schemas.py
"""Pydantic models for reports domain."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    """Structured report section with AI-generated narrative fields."""

    headline: str = Field(
        ...,
        description="1 sentence, punchy headline mentioning model vs market if relevant",
    )
    thesis: str = Field(
        ..., description="3-5 sentences tying together market context, news, and model edge"
    )
    bull_case: List[str] = Field(..., description="2-4 short bullet points for bullish case")
    bear_case: List[str] = Field(..., description="2-4 short bullet points for bearish case")
    key_risks: List[str] = Field(..., description="2-4 short bullet points for key risks")
    execution_notes: str = Field(
        ..., description="2-3 sentences on sizing, TP/SL usage, and when to re-check"
    )

    # Legacy fields for backward compatibility
    title: Optional[str] = Field(None, description="Same as headline (legacy)")
    markdown: Optional[str] = Field(None, description="Full markdown report (legacy)")


class ReportData(BaseModel):
    """Complete report data structure."""

    headline: str
    thesis: str
    bull_case: List[str]
    bear_case: List[str]
    key_risks: List[str]
    execution_notes: str
    title: Optional[str] = None
    markdown: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict for backward compatibility."""
        data = self.model_dump()
        if not data.get("title"):
            data["title"] = data["headline"]
        return data
