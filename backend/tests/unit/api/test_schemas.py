"""Tests for API Schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from pydantic import ValidationError as PydanticValidationError

from app.api.schemas.common import ErrorResponse, HealthResponse
from app.api.schemas.requests import AnalyzeRequest
from app.api.schemas.responses import MarketSelectionResponse
from app.domains.analysis.schemas import Signal
from app.domains.reports.schemas import ReportSection


def test_signal_validation():
    """Test Signal model validation."""
    signal = Signal(
        market_prob=0.5,
        model_prob=0.6,
        edge_pct=0.1,
        expected_value_per_dollar=0.1,
        kelly_fraction_yes=0.2,
        kelly_fraction_no=0.0,
        confidence_level="high",
        confidence_score=0.8,
        recommended_action="buy_yes",
        recommended_size_fraction=0.1,
        horizon="24h",
    )

    assert signal.market_prob == 0.5
    assert signal.model_prob == 0.6
    assert signal.confidence_level == "high"


def test_signal_invalid_probability():
    """Test Signal with invalid probability."""
    with pytest.raises(ValidationError):
        Signal(
            market_prob=1.5,  # Invalid: > 1.0
            model_prob=0.6,
            edge_pct=0.1,
            expected_value_per_dollar=0.1,
            kelly_fraction_yes=0.2,
            kelly_fraction_no=0.0,
            confidence_level="high",
            confidence_score=0.8,
            recommended_action="buy_yes",
            recommended_size_fraction=0.1,
            horizon="24h",
        )


def test_analyze_request_validation():
    """Test AnalyzeRequest validation."""
    request = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
        horizon="24h",
        strategy_preset="Balanced",
    )

    assert str(request.market_url) == "https://polymarket.com/market/test"
    assert request.horizon == "24h"


def test_analyze_request_accepts_polymarket_url():
    req = AnalyzeRequest(market_url="https://polymarket.com/event/fed-decision")
    assert str(req.market_url).startswith("https://polymarket.com")


def test_analyze_request_accepts_kalshi_url():
    req = AnalyzeRequest(market_url="https://kalshi.com/markets/INXD-25JAN17-B24999")
    assert str(req.market_url).startswith("https://kalshi.com")


def test_analyze_request_invalid_url():
    """Test AnalyzeRequest with invalid URL (not Polymarket)."""
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            market_url="https://example.com/market/test",  # Not Polymarket
        )


def test_analyze_request_rejects_unknown_url():
    try:
        AnalyzeRequest(market_url="https://example.com/event/foo")
    except PydanticValidationError as exc:
        assert "Kalshi" in str(exc)
        assert "Polymarket" in str(exc)
    else:
        raise AssertionError("expected validation error")


def test_analyze_request_accepts_selected_market_id():
    req = AnalyzeRequest(
        market_url="https://polymarket.com/event/fed-decision",
        selected_market_id="fed-decision-yes",
    )
    assert req.selected_market_id == "fed-decision-yes"


def test_market_selection_response():
    """Test MarketSelectionResponse."""
    response = MarketSelectionResponse(
        event_context={"title": "Test Event"},
        market_options=[{"slug": "market-1"}],
    )

    assert response.requires_market_selection is True
    assert len(response.market_options) == 1


def test_health_response():
    """Test HealthResponse."""
    response = HealthResponse(
        status="ok",
        message="Service is running",
    )

    assert response.status == "ok"
    assert response.message == "Service is running"


def test_error_response():
    """Test ErrorResponse."""
    response = ErrorResponse(
        error="ValidationError",
        detail="Invalid input",
        request_id="test-request-id",
    )

    assert response.error == "ValidationError"
    assert response.detail == "Invalid input"
    assert response.request_id == "test-request-id"


def test_report_section():
    """Test ReportSection."""
    section = ReportSection(
        headline="Test headline",
        thesis="Test thesis",
        bull_case=["Bull 1", "Bull 2"],
        bear_case=["Bear 1", "Bear 2"],
        key_risks=["Risk 1", "Risk 2"],
        execution_notes="Test notes",
    )

    assert section.headline == "Test headline"
    assert len(section.bull_case) == 2
    assert len(section.bear_case) == 2
