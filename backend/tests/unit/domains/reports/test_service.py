"""Tests for Report Agent."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.analysis.schemas import Signal
from app.domains.reports.generator import generate_report_with_llm
from app.domains.reports.templates import generate_fallback_report, signal_to_dict
from app.orchestration.agents.report import run_report_agent
from app.orchestration.state import AgentState


def test_signal_to_dict_pydantic_model():
    """Test _signal_to_dict with Pydantic model."""
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
        target_take_profit_prob=0.7,
        target_stop_loss_prob=0.4,
        horizon="24h",
        rationale_short="Test",
    )

    result = signal_to_dict(signal)

    assert isinstance(result, dict)
    assert result["market_prob"] == 0.5
    assert result["model_prob"] == 0.6


def test_signal_to_dict_dict():
    """Test _signal_to_dict with dict."""
    signal = {"market_prob": 0.5, "model_prob": 0.6}

    result = signal_to_dict(signal)

    assert result == signal


def test_signal_to_dict_invalid():
    """Test _signal_to_dict with invalid input."""
    result = signal_to_dict("invalid")

    assert result == {}


def test_generate_fallback_report_full_data():
    """Test _generate_fallback_report with full data."""
    market_snapshot = {
        "question": "Will this test pass?",
        "yes_price": 0.5,
        "liquidity": 1000000.0,
    }
    signal = {
        "market_prob": 0.5,
        "model_prob": 0.6,
        "edge_pct": 0.1,
        "confidence_level": "high",
        "recommended_size_fraction": 0.1,
        "target_take_profit_prob": 0.7,
        "target_stop_loss_prob": 0.4,
    }
    decision = {
        "action": "BUY",
        "edge_pct": 0.1,
        "notes": "Test notes",
    }
    event_context = {"title": "Test Event"}
    news_context = {"summary": "Test news"}

    report = generate_fallback_report(
        market_snapshot, signal, decision, event_context, news_context
    )

    assert "headline" in report
    assert "thesis" in report
    assert "bull_case" in report
    assert "bear_case" in report
    assert "key_risks" in report
    assert "execution_notes" in report
    assert "title" in report
    assert "markdown" in report
    assert "BUY" in report["headline"] or "BUY" in report["thesis"]


def test_generate_fallback_report_missing_data():
    """Test _generate_fallback_report with missing data."""
    market_snapshot = {}
    signal = {}
    decision = {}
    event_context = {}
    news_context = None

    report = generate_fallback_report(
        market_snapshot, signal, decision, event_context, news_context
    )

    assert "headline" in report
    assert "thesis" in report


def test_generate_fallback_report_various_combinations():
    """Test _generate_fallback_report with various signal/decision combinations."""
    market_snapshot = {"question": "Test?", "yes_price": 0.5}

    # Test with different actions
    for action in ["BUY", "SELL", "HOLD"]:
        decision = {"action": action, "edge_pct": 0.1}
        signal = {"market_prob": 0.5, "model_prob": 0.6, "edge_pct": 0.1}

        report = generate_fallback_report(market_snapshot, signal, decision, {}, None)

        assert report["headline"] is not None
        assert report["thesis"] is not None


@pytest.mark.anyio(backend="asyncio")
async def test_generate_report_with_openai_success():
    """Test _generate_report_with_openai successful generation."""
    market_snapshot = {"question": "Test?", "yes_price": 0.5}
    signal = {"market_prob": 0.5, "model_prob": 0.6, "edge_pct": 0.1}
    decision = {"action": "BUY", "edge_pct": 0.1}
    event_context = {"title": "Test Event"}
    news_context = {"summary": "Test news"}

    mock_report_data = {
        "headline": "Test headline",
        "thesis": "Test thesis",
        "bull_case": ["Bull 1", "Bull 2"],
        "bear_case": ["Bear 1", "Bear 2"],
        "key_risks": ["Risk 1", "Risk 2"],
        "execution_notes": "Test notes",
    }

    with patch("app.domains.reports.generator.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.api_key = "test-key"
        mock_client.client = MagicMock()
        mock_client._use_new_api = True

        # Mock the OpenAI API call
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_report_data)
        mock_client.client.chat.completions.create = MagicMock(return_value=mock_completion)

        mock_get_client.return_value = mock_client

        with patch("asyncio.get_running_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                return_value=json.dumps(mock_report_data)
            )

            report = await generate_report_with_llm(
                market_snapshot, signal, decision, event_context, news_context
            )

            assert report["headline"] == "Test headline"
            assert report["thesis"] == "Test thesis"


@pytest.mark.anyio(backend="asyncio")
async def test_generate_report_with_openai_error():
    """Test _generate_report_with_openai with OpenAI errors."""
    market_snapshot = {"question": "Test?", "yes_price": 0.5}
    signal = {"market_prob": 0.5}
    decision = {"action": "BUY"}
    event_context = {}
    news_context = None

    with patch("app.domains.reports.generator.get_openai_client") as mock_get_client:
        mock_get_client.side_effect = RuntimeError("OpenAI not available")

        with pytest.raises(RuntimeError):
            await generate_report_with_llm(
                market_snapshot, signal, decision, event_context, news_context
            )


@pytest.mark.anyio(backend="asyncio")
async def test_generate_report_with_openai_circuit_breaker():
    """Test _generate_report_with_openai with circuit breaker open."""
    market_snapshot = {"question": "Test?", "yes_price": 0.5}
    signal = {"market_prob": 0.5}
    decision = {"action": "BUY"}
    event_context = {}
    news_context = None

    with patch("app.domains.reports.generator.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.api_key = None  # Simulates circuit breaker
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError):
            await generate_report_with_llm(
                market_snapshot, signal, decision, event_context, news_context
            )


@pytest.mark.anyio(backend="asyncio")
async def test_run_report_agent_with_openai():
    """Test run_report_agent with OpenAI available."""
    state: AgentState = {
        "market_snapshot": {"question": "Test?", "yes_price": 0.5},
        "signal": {"market_prob": 0.5, "model_prob": 0.6},
        "decision": {"action": "BUY"},
        "event_context": {"title": "Test Event"},
        "news_context": {"summary": "Test news"},
    }

    mock_report = {
        "headline": "Test headline",
        "thesis": "Test thesis",
        "bull_case": [],
        "bear_case": [],
        "key_risks": [],
        "execution_notes": "Test",
    }

    with patch("app.domains.reports.service.generate_report") as mock_gen:
        mock_gen.return_value = mock_report

        result = await run_report_agent(state)

        assert result["report"] == mock_report
        assert "env" in result


@pytest.mark.anyio(backend="asyncio")
async def test_run_report_agent_fallback():
    """Test run_report_agent with fallback scenario."""
    state: AgentState = {
        "market_snapshot": {"question": "Test?", "yes_price": 0.5},
        "signal": {"market_prob": 0.5, "model_prob": 0.6},
        "decision": {"action": "BUY"},
        "event_context": {},
        "news_context": None,
    }

    with patch("app.domains.reports.generator.generate_report") as mock_gen:
        mock_gen.side_effect = Exception("OpenAI error")

        result = await run_report_agent(state)

        assert "report" in result
        assert result["report"]["headline"] is not None


@pytest.mark.anyio(backend="asyncio")
async def test_run_report_agent_missing_signal_decision():
    """Test run_report_agent with missing signal/decision."""
    state: AgentState = {
        "market_snapshot": {"question": "Test?"},
        "event_context": {},
    }

    result = await run_report_agent(state)

    assert "report" in result
    assert result["report"]["headline"] is not None


@pytest.mark.anyio(backend="asyncio")
async def test_run_report_agent_critical_error():
    """Test run_report_agent with critical error (last resort fallback)."""
    state: AgentState = {
        "market_snapshot": {"question": "Test?"},
    }

    with patch("app.domains.reports.generator.generate_report") as mock_gen:
        mock_gen.side_effect = Exception("Critical error")

        # Should still return a report
        result = await run_report_agent(state)

        assert "report" in result
