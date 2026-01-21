"""Tests for Probability Agent."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.analysis.probability import create_fallback_signal
from app.orchestration.agents.probability import run_probability_agent
from app.orchestration.state import AgentState


def test_fallback_signal():
    """Test _fallback_signal with various configurations."""
    signal = create_fallback_signal(0.5, "24h", "Test rationale")

    assert signal.market_prob == 0.5
    assert signal.model_prob > 0.5  # Should add default delta
    assert signal.edge_pct > 0
    assert signal.confidence_level == "medium"
    assert signal.recommended_action == "hold"
    assert signal.horizon == "24h"
    assert "Test rationale" in signal.rationale_short


def test_fallback_signal_missing_rationale():
    """Test _fallback_signal with missing rationale."""
    signal = create_fallback_signal(0.3, "24h", None)

    assert signal.rationale_short is not None
    assert len(signal.rationale_short) > 0


def test_fallback_signal_various_probabilities():
    """Test _fallback_signal with various market probabilities."""
    # Low probability
    signal_low = create_fallback_signal(0.1, "24h")
    assert signal_low.market_prob == 0.1
    assert signal_low.model_prob > 0.1

    # High probability
    signal_high = create_fallback_signal(0.9, "24h")
    assert signal_high.market_prob == 0.9
    assert signal_high.model_prob <= 1.0  # Should be clamped


@pytest.mark.anyio(backend="asyncio")
async def test_run_prob_agent_with_openai():
    """Test run_prob_agent with OpenAI client available."""
    state: AgentState = {
        "market_snapshot": {
            "question": "Will this test pass?",
            "yes_price": 0.5,
        },
        "event_context": {
            "title": "Test Event",
        },
        "news_context": {
            "summary": "Test news summary",
            "articles": [
                {"title": "Article 1"},
                {"title": "Article 2"},
            ],
        },
        "horizon": "24h",
    }

    mock_openai_data = {
        "model_prob_abs": 0.6,
        "confidence": "high",
        "rationale": "Test rationale",
    }

    with patch("app.domains.analysis.probability.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate_signal = AsyncMock(return_value=mock_openai_data)
        mock_get_client.return_value = mock_client

        result = await run_probability_agent(state)

        assert "signal" in result
        assert result["signal"].market_prob == 0.5
        assert result["signal"].model_prob == 0.6
        assert result["signal"].confidence_level == "high"


@pytest.mark.anyio(backend="asyncio")
async def test_run_prob_agent_without_openai():
    """Test run_prob_agent without OpenAI client (fallback)."""
    state: AgentState = {
        "market_snapshot": {
            "yes_price": 0.4,
        },
        "event_context": {},
        "news_context": {},
        "horizon": "24h",
    }

    with patch("app.domains.analysis.probability.get_openai_client") as mock_get_client:
        mock_get_client.side_effect = RuntimeError("OpenAI not available")

        result = await run_probability_agent(state)

        assert "signal" in result
        assert result["signal"].market_prob == 0.4
        assert result["signal"].confidence_level == "medium"


@pytest.mark.anyio(backend="asyncio")
async def test_run_prob_agent_circuit_breaker_open():
    """Test run_prob_agent with circuit breaker open (fallback)."""
    state: AgentState = {
        "market_snapshot": {
            "yes_price": 0.3,
        },
        "event_context": {},
        "news_context": {},
        "horizon": "24h",
    }

    with patch("app.domains.analysis.probability.get_openai_client") as mock_get_client:
        mock_get_client.side_effect = RuntimeError("Circuit breaker open")

        result = await run_probability_agent(state)

        assert "signal" in result
        assert result["signal"].confidence_level == "medium"


@pytest.mark.anyio(backend="asyncio")
async def test_run_prob_agent_openai_error():
    """Test run_prob_agent with OpenAI error (fallback)."""
    state: AgentState = {
        "market_snapshot": {
            "yes_price": 0.5,
        },
        "event_context": {},
        "news_context": {},
        "horizon": "24h",
    }

    with patch("app.domains.analysis.probability.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate_signal = AsyncMock(side_effect=Exception("API Error"))
        mock_get_client.return_value = mock_client

        result = await run_probability_agent(state)

        assert "signal" in result
        assert result["signal"].confidence_level == "medium"


@pytest.mark.anyio(backend="asyncio")
async def test_run_prob_agent_parsing_error():
    """Test run_prob_agent with parsing error (fallback)."""
    state: AgentState = {
        "market_snapshot": {
            "yes_price": 0.5,
        },
        "event_context": {},
        "news_context": {},
        "horizon": "24h",
    }

    mock_openai_data = {
        "model_prob_abs": "invalid",  # Invalid type
    }

    with patch("app.domains.analysis.probability.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate_signal = AsyncMock(return_value=mock_openai_data)
        mock_get_client.return_value = mock_client

        result = await run_probability_agent(state)

        assert "signal" in result
        assert result["signal"].confidence_level == "medium"


@pytest.mark.anyio(backend="asyncio")
async def test_run_prob_agent_confidence_override():
    """Test run_prob_agent with LLM confidence override."""
    state: AgentState = {
        "market_snapshot": {
            "yes_price": 0.5,
        },
        "event_context": {},
        "news_context": {
            "articles": [{"title": "Test"}],
        },
        "horizon": "24h",
    }

    mock_openai_data = {
        "model_prob_abs": 0.6,
        "confidence": "low",
    }

    with patch("app.domains.analysis.probability.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate_signal = AsyncMock(return_value=mock_openai_data)
        mock_get_client.return_value = mock_client

        result = await run_probability_agent(state)

        assert result["signal"].confidence_level == "low"


@pytest.mark.anyio(backend="asyncio")
async def test_run_prob_agent_missing_yes_price():
    """Test run_prob_agent with missing yes_price."""
    state: AgentState = {
        "market_snapshot": {},
        "event_context": {},
        "news_context": {},
        "horizon": "24h",
    }

    with patch("app.domains.analysis.probability.get_openai_client") as mock_get_client:
        mock_get_client.side_effect = RuntimeError("OpenAI not available")

        result = await run_probability_agent(state)

        assert "signal" in result
        # Should still create a signal with inferred probability


@pytest.mark.anyio(backend="asyncio")
async def test_run_prob_agent_top_headlines():
    """Test run_prob_agent extracts top headlines correctly."""
    state: AgentState = {
        "market_snapshot": {
            "yes_price": 0.5,
        },
        "event_context": {},
        "news_context": {
            "articles": [
                {"title": "Headline 1"},
                {"title": "Headline 2"},
                {"title": "Headline 3"},
                {"title": "Headline 4"},  # Should be ignored (only first 3)
            ],
        },
        "horizon": "24h",
    }

    with patch("app.domains.analysis.probability.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate_signal = AsyncMock(return_value={"model_prob_abs": 0.6})
        mock_get_client.return_value = mock_client

        await run_probability_agent(state)

        # Verify OpenAI was called (headlines should be included)
        assert mock_client.generate_signal.called


@pytest.mark.anyio(backend="asyncio")
async def test_run_prob_agent_tag_label():
    """Test run_prob_agent uses tag_label from snapshot."""
    state: AgentState = {
        "market_snapshot": {
            "yes_price": 0.5,
            "label": "Test Label",
        },
        "event_context": {},
        "news_context": {},
        "horizon": "24h",
    }

    with patch("app.domains.analysis.probability.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.generate_signal = AsyncMock(return_value={"model_prob_abs": 0.6})
        mock_get_client.return_value = mock_client

        await run_probability_agent(state)

        # Verify OpenAI was called with tag_label
        call_args = mock_client.generate_signal.call_args
        assert call_args is not None
        assert "tag_label" in call_args.kwargs or "Test Label" in str(call_args)
