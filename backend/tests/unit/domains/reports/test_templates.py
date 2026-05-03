"""Tests for report templates (venue-aware rendering)."""

from __future__ import annotations

from app.domains.reports.templates import generate_fallback_report


def _base_inputs():
    """Minimal valid kwargs for generate_fallback_report."""
    return {
        "signal": {
            "recommended_action": "hold",
            "edge_pct": 0.0,
            "model_prob": 0.5,
            "market_prob": 0.5,
        },
        "decision": {"action": "hold"},
        "market_snapshot": {
            "question": "Test market?",
            "yes_price": 0.5,
            "liquidity": 100.0,
        },
        "event_context": {},
        "news_context": None,
    }


def _render_markdown(report):
    if isinstance(report, str):
        return report
    if isinstance(report, dict):
        return report.get("markdown", str(report))
    return str(report)


def test_fallback_report_renders_polymarket_liquidity_in_usdc():
    """When venue=polymarket (or absent for backward compat), the fallback
    report's market-snapshot section labels the value as 'Liquidity' with
    a 'USDC' unit suffix."""
    inputs = _base_inputs()
    inputs["market_snapshot"]["venue"] = "polymarket"
    inputs["market_snapshot"]["liquidity"] = 12345.0

    report = generate_fallback_report(**inputs)
    md = _render_markdown(report)

    assert "Liquidity:" in md
    assert "12,345" in md or "12345" in md
    assert "USDC" in md


def test_fallback_report_renders_kalshi_liquidity_as_open_interest_in_contracts():
    """When venue=kalshi, the fallback report's market-snapshot section
    labels the value as 'Open Interest' with a 'contracts' unit suffix
    (Kalshi exposes OI count, not USD liquidity)."""
    inputs = _base_inputs()
    inputs["market_snapshot"]["venue"] = "kalshi"
    inputs["market_snapshot"]["liquidity"] = 300.0  # carries the OI value via the alias

    report = generate_fallback_report(**inputs)
    md = _render_markdown(report)

    assert "Open Interest:" in md
    assert "300" in md
    assert "contracts" in md
    # Should NOT mislabel OI as USDC for Kalshi
    assert "USDC" not in md.split("Open Interest:")[1].split("\n")[0]
