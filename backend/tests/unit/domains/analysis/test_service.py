"""Tests for Strategy Agent."""

from __future__ import annotations

import pytest

from app.domains.analysis.decision import decide_action
from app.domains.analysis.presets import get_preset
from app.domains.analysis.schemas import Signal
from app.orchestration.agents.strategy import run_strategy_agent
from app.orchestration.state import AgentState


def test_preset_defaults_conservative():
    """Test _preset_defaults with Conservative preset."""
    params = get_preset("Conservative")

    assert params["min_edge_pct"] == 0.08
    assert params["min_confidence"] == "high"
    assert params["max_capital_pct"] == 0.08
    assert params["max_kelly_fraction"] == 0.15


def test_preset_defaults_balanced():
    """Test _preset_defaults with Balanced preset."""
    params = get_preset("Balanced")

    assert params["min_edge_pct"] == 0.05
    assert params["min_confidence"] == "medium"
    assert params["max_capital_pct"] == 0.15
    assert params["max_kelly_fraction"] == 0.25


def test_preset_defaults_aggressive():
    """Test _preset_defaults with Aggressive preset."""
    params = get_preset("Aggressive")

    assert params["min_edge_pct"] == 0.03
    assert params["min_confidence"] == "low"
    assert params["max_capital_pct"] == 0.25
    assert params["max_kelly_fraction"] == 0.5


def test_preset_defaults_invalid():
    """Test _preset_defaults with invalid preset (fallback to Balanced)."""
    params = get_preset("Invalid")

    assert params["min_edge_pct"] == 0.05
    assert params["min_confidence"] == "medium"


def test_preset_defaults_case_insensitive():
    """Test _preset_defaults is case insensitive."""
    params1 = get_preset("CONSERVATIVE")
    params2 = get_preset("conservative")

    assert params1 == params2


def test_decide_action_buy_scenario():
    """Test decide_action with BUY scenario (edge > min_edge, confidence sufficient)."""
    signal = Signal(
        market_prob=0.5,
        model_prob=0.6,
        edge_pct=0.1,
        expected_value_per_dollar=0.1,
        kelly_fraction_yes=0.2,
        kelly_fraction_no=0.0,
        confidence_level="high",
        confidence_score=0.8,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon="24h",
        rationale_short="Test",
    )

    state: AgentState = {
        "position_side": "flat",
        "position_size_fraction": 0.0,
    }

    params = {
        "min_edge_pct": 0.05,
        "min_confidence": "medium",
        "max_capital_pct": 0.15,
        "max_kelly_fraction": 0.25,
        "risk_off": False,
    }

    result = decide_action(
        signal,
        position_side=state["position_side"],
        position_size=state["position_size_fraction"],
        params=params,
    )

    assert result.recommended_action == "buy_yes"
    assert result.recommended_size_fraction > 0


def test_decide_action_sell_scenario():
    """Test decide_action with SELL scenario (negative edge)."""
    signal = Signal(
        market_prob=0.6,
        model_prob=0.5,
        edge_pct=-0.1,
        expected_value_per_dollar=-0.1,
        kelly_fraction_yes=0.0,
        kelly_fraction_no=0.2,
        confidence_level="high",
        confidence_score=0.8,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon="24h",
        rationale_short="Test",
    )

    state: AgentState = {
        "position_side": "flat",
        "position_size_fraction": 0.0,
    }

    params = {
        "min_edge_pct": 0.05,
        "min_confidence": "medium",
        "max_capital_pct": 0.15,
        "max_kelly_fraction": 0.25,
        "risk_off": False,
    }

    result = decide_action(
        signal,
        position_side=state["position_side"],
        position_size=state["position_size_fraction"],
        params=params,
    )

    assert result.recommended_action == "buy_no"
    assert result.recommended_size_fraction > 0


def test_decide_action_hold_low_confidence():
    """Test decide_action with HOLD due to low confidence."""
    signal = Signal(
        market_prob=0.5,
        model_prob=0.6,
        edge_pct=0.1,
        expected_value_per_dollar=0.1,
        kelly_fraction_yes=0.2,
        kelly_fraction_no=0.0,
        confidence_level="low",
        confidence_score=0.3,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon="24h",
        rationale_short="Test",
    )

    state: AgentState = {
        "position_side": "flat",
        "position_size_fraction": 0.0,
    }

    params = {
        "min_edge_pct": 0.05,
        "min_confidence": "high",  # Requires high confidence
        "max_capital_pct": 0.15,
        "max_kelly_fraction": 0.25,
        "risk_off": False,
    }

    result = decide_action(
        signal,
        position_side=state["position_side"],
        position_size=state["position_size_fraction"],
        params=params,
    )

    assert result.recommended_action == "hold"
    assert result.recommended_size_fraction == 0.0


def test_decide_action_hold_small_edge():
    """Test decide_action with HOLD due to edge too small."""
    signal = Signal(
        market_prob=0.5,
        model_prob=0.52,
        edge_pct=0.02,  # Below min_edge_pct
        expected_value_per_dollar=0.02,
        kelly_fraction_yes=0.05,
        kelly_fraction_no=0.0,
        confidence_level="high",
        confidence_score=0.8,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon="24h",
        rationale_short="Test",
    )

    state: AgentState = {
        "position_side": "flat",
        "position_size_fraction": 0.0,
    }

    params = {
        "min_edge_pct": 0.05,  # Edge is 0.02, too small
        "min_confidence": "medium",
        "max_capital_pct": 0.15,
        "max_kelly_fraction": 0.25,
        "risk_off": False,
    }

    result = decide_action(
        signal,
        position_side=state["position_side"],
        position_size=state["position_size_fraction"],
        params=params,
    )

    assert result.recommended_action == "hold"
    assert result.recommended_size_fraction == 0.0


def test_decide_action_risk_off():
    """Test decide_action with risk_off flag."""
    signal = Signal(
        market_prob=0.5,
        model_prob=0.6,
        edge_pct=0.1,
        expected_value_per_dollar=0.1,
        kelly_fraction_yes=0.2,
        kelly_fraction_no=0.0,
        confidence_level="high",
        confidence_score=0.8,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon="24h",
        rationale_short="Test",
    )

    state: AgentState = {
        "position_side": "flat",
        "position_size_fraction": 0.0,
    }

    params = {
        "min_edge_pct": 0.05,
        "min_confidence": "medium",
        "max_capital_pct": 0.15,
        "max_kelly_fraction": 0.25,
        "risk_off": True,  # Risk off
    }

    result = decide_action(
        signal,
        position_side=state["position_side"],
        position_size=state["position_size_fraction"],
        params=params,
    )

    assert result.recommended_action == "hold"
    assert result.recommended_size_fraction == 0.0


def test_decide_action_exact_threshold():
    """Test decide_action with exact threshold values."""
    signal = Signal(
        market_prob=0.5,
        model_prob=0.55,
        edge_pct=0.05,  # Exactly min_edge_pct
        expected_value_per_dollar=0.05,
        kelly_fraction_yes=0.1,
        kelly_fraction_no=0.0,
        confidence_level="medium",
        confidence_score=0.5,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon="24h",
        rationale_short="Test",
    )

    state: AgentState = {
        "position_side": "flat",
        "position_size_fraction": 0.0,
    }

    params = {
        "min_edge_pct": 0.05,
        "min_confidence": "medium",
        "max_capital_pct": 0.15,
        "max_kelly_fraction": 0.25,
        "risk_off": False,
    }

    result = decide_action(
        signal,
        position_side=state["position_side"],
        position_size=state["position_size_fraction"],
        params=params,
    )

    # Should proceed since edge equals threshold
    assert result.recommended_action in ["buy_yes", "hold"]


@pytest.mark.anyio(backend="asyncio")
async def test_run_strategy_agent_all_presets():
    """Test run_strategy_agent with all preset configurations."""
    for preset in ["Conservative", "Balanced", "Aggressive"]:
        signal = Signal(
            market_prob=0.5,
            model_prob=0.6,
            edge_pct=0.1,
            expected_value_per_dollar=0.1,
            kelly_fraction_yes=0.2,
            kelly_fraction_no=0.0,
            confidence_level="high",
            confidence_score=0.8,
            recommended_action="hold",
            recommended_size_fraction=0.0,
            target_take_profit_prob=None,
            target_stop_loss_prob=None,
            horizon="24h",
            rationale_short="Test",
        )

        state: AgentState = {
            "strategy_preset": preset,
            "horizon": "24h",
            "signal": signal,
            "position_side": "flat",
            "position_size_fraction": 0.0,
        }

        result = await run_strategy_agent(state)

        assert result["strategy_preset"] == preset
        assert "decision" in result
        assert result["decision"]["action"] in ["BUY", "HOLD", "SELL"]


@pytest.mark.anyio(backend="asyncio")
async def test_run_strategy_agent_custom_params():
    """Test run_strategy_agent with custom strategy_params."""
    signal = Signal(
        market_prob=0.5,
        model_prob=0.6,
        edge_pct=0.1,
        expected_value_per_dollar=0.1,
        kelly_fraction_yes=0.2,
        kelly_fraction_no=0.0,
        confidence_level="high",
        confidence_score=0.8,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon="24h",
        rationale_short="Test",
    )

    state: AgentState = {
        "strategy_preset": "Balanced",
        "strategy_params": {
            "min_edge_pct": 0.08,  # Override
            "max_capital_pct": 0.2,  # Override
        },
        "horizon": "24h",
        "signal": signal,
        "position_side": "flat",
        "position_size_fraction": 0.0,
    }

    result = await run_strategy_agent(state)

    assert result["strategy_params"]["min_edge_pct"] == 0.08
    assert result["strategy_params"]["max_capital_pct"] == 0.2


@pytest.mark.anyio(backend="asyncio")
async def test_run_strategy_agent_missing_signal():
    """Test run_strategy_agent with missing signal."""
    state: AgentState = {
        "strategy_preset": "Balanced",
        "horizon": "24h",
        "market_snapshot": {
            "yes_price": 0.5,
        },
    }

    result = await run_strategy_agent(state)

    assert "signal" in result
    assert result["signal"].recommended_action == "hold"
    assert "decision" in result


@pytest.mark.anyio(backend="asyncio")
async def test_run_strategy_agent_dict_signal():
    """Test run_strategy_agent with dict signal (backward compatibility)."""
    state: AgentState = {
        "strategy_preset": "Balanced",
        "horizon": "24h",
        "signal": {
            "market_prob": 0.5,
            "model_prob_abs": 0.6,
            "edge_pct": 0.1,
            "confidence": "high",
            "rationale": "Test",
        },
        "position_side": "flat",
        "position_size_fraction": 0.0,
    }

    result = await run_strategy_agent(state)

    assert "signal" in result
    assert isinstance(result["signal"], Signal)
    assert "decision" in result


@pytest.mark.anyio(backend="asyncio")
async def test_run_strategy_agent_position_management():
    """Test run_strategy_agent position management logic."""
    signal = Signal(
        market_prob=0.5,
        model_prob=0.6,
        edge_pct=0.1,
        expected_value_per_dollar=0.1,
        kelly_fraction_yes=0.2,
        kelly_fraction_no=0.0,
        confidence_level="high",
        confidence_score=0.8,
        recommended_action="hold",
        recommended_size_fraction=0.0,
        target_take_profit_prob=None,
        target_stop_loss_prob=None,
        horizon="24h",
        rationale_short="Test",
    )

    # Test with existing position
    state: AgentState = {
        "strategy_preset": "Balanced",
        "horizon": "24h",
        "signal": signal,
        "position_side": "long_yes",
        "position_size_fraction": 0.1,
    }

    result = await run_strategy_agent(state)

    assert "decision" in result
    assert result["decision"]["action"] in ["BUY", "HOLD", "SELL"]
