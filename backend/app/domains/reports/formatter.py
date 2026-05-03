# app/domains/reports/formatter.py
"""Report formatting utilities."""

from __future__ import annotations

from textwrap import dedent
from typing import Any, Dict, List


def format_bullet_list(items: List[str], prefix: str = "- ") -> str:
    """Format a list of items as bullet points.

    Args:
        items: List of strings
        prefix: Bullet prefix

    Returns:
        Formatted bullet list string
    """
    return "\n".join(f"{prefix}{item}" for item in items)


def format_report_markdown(report_data: Dict[str, Any]) -> str:
    """Format report data as markdown.

    Args:
        report_data: Report data dict with headline, thesis, etc.

    Returns:
        Formatted markdown string
    """
    headline = report_data.get("headline", "")
    thesis = report_data.get("thesis", "")
    bull_case = report_data.get("bull_case", [])
    bear_case = report_data.get("bear_case", [])
    key_risks = report_data.get("key_risks", [])
    execution_notes = report_data.get("execution_notes", "")

    return dedent(
        f"""
        ## TL;DR
        {headline}

        ## Thesis
        {thesis}

        ## Bull Case
        {format_bullet_list(bull_case)}

        ## Bear Case
        {format_bullet_list(bear_case)}

        ## Key Risks
        {format_bullet_list(key_risks)}

        ## Execution Notes
        {execution_notes}
        """
    ).strip()


def add_legacy_fields(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add legacy fields for backward compatibility.

    Args:
        report_data: Report data dict

    Returns:
        Report data with legacy fields added
    """
    if "title" not in report_data:
        report_data["title"] = report_data.get("headline", "")

    if "markdown" not in report_data:
        report_data["markdown"] = format_report_markdown(report_data)

    return report_data


def format_action_summary(
    action: str,
    edge_pct: float,
    market_question: str = "",
    yes_price: float = 0.0,
    liquidity: float = 0.0,
    notes: str = "",
) -> str:
    """Format a short action summary in markdown.

    Args:
        action: Trading action
        edge_pct: Edge percentage
        market_question: Market question
        yes_price: YES price
        liquidity: Market liquidity
        notes: Additional notes

    Returns:
        Formatted markdown summary
    """
    return dedent(
        f"""
        ## TL;DR
        Action: **{action}** with edge ~{edge_pct:.2%}.

        ## Market snapshot
        - Question: {market_question or "N/A"}
        - Yes price: {yes_price:.2%}
        - Liquidity: {liquidity:,.0f} USDC

        ## Rationale
        {notes or "Strategy placeholder."}
        """
    ).strip()
