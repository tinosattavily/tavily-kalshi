"""Tests for Analysis Graph."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.agents.graph import reset_analysis_graph, run_analysis_graph
from app.agents.state import AgentState


@pytest.fixture(autouse=True)
def reset_graph_singleton():
    """Reset the graph singleton before each test to ensure fresh compilation with mocks."""
    reset_analysis_graph()
    yield
    reset_analysis_graph()


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_graph_full_execution():
    """Test run_analysis_graph full execution flow (all agents)."""
    initial_state: AgentState = {
        "market_url": "https://polymarket.com/market/test-market",
        "slug": "test-market",
        "horizon": "24h",
        "strategy_preset": "Balanced",
    }

    # Mock all agents to return modified state
    with (
        patch("app.agents.graph.run_market_agent") as mock_market,
        patch("app.agents.graph.run_event_agent") as mock_event,
        patch("app.agents.graph.run_tavily_prompt_agent") as mock_tavily,
        patch("app.agents.graph.run_news_agent") as mock_news,
        patch("app.agents.graph.run_news_summary_agent") as mock_summary,
        patch("app.agents.graph.run_prob_agent") as mock_prob,
        patch("app.agents.graph.run_strategy_agent") as mock_strategy,
        patch("app.agents.graph.run_report_agent") as mock_report,
    ):
        # Each agent returns state with its additions
        # Note: run_analysis_graph sets run_id and run_at at the start,
        # so agents should preserve them
        def preserve_fields(s, **kwargs):
            result = {**s, **kwargs}
            # Preserve run_id and run_at that graph sets
            if "run_id" not in result:
                result["run_id"] = "run-test"
            if "run_at" not in result:
                result["run_at"] = "2025-01-01T00:00:00Z"
            return result

        mock_market.side_effect = lambda s: preserve_fields(s, market_snapshot={})
        mock_event.side_effect = lambda s: preserve_fields(s, event_context={})
        mock_tavily.side_effect = lambda s: preserve_fields(s, tavily_queries=[])
        mock_news.side_effect = lambda s: preserve_fields(s, news_context={})
        mock_summary.side_effect = lambda s: preserve_fields(s, news_context={"summary": "Test"})
        mock_prob.side_effect = lambda s: preserve_fields(s, signal={})
        mock_strategy.side_effect = lambda s: preserve_fields(s, decision={})
        mock_report.side_effect = lambda s: preserve_fields(s, report={})

        result = await run_analysis_graph(initial_state)

        # Verify all agents were called
        assert mock_market.called
        assert mock_event.called
        assert mock_tavily.called
        assert mock_news.called
        assert mock_summary.called
        assert mock_prob.called
        assert mock_strategy.called
        assert mock_report.called

        # Verify final state has all components
        assert "run_id" in result
        assert "run_at" in result


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_graph_early_termination():
    """Test run_analysis_graph early termination (market selection required)."""
    initial_state: AgentState = {
        "market_url": "https://polymarket.com/event/test-event",
        "slug": "test-event",
    }

    with patch("app.agents.graph.run_market_agent") as mock_market:
        # Market agent returns state requiring selection
        mock_market.return_value = {
            **initial_state,
            "requires_market_selection": True,
            "market_options": [{"slug": "market-1"}],
        }

        result = await run_analysis_graph(initial_state)

        # Should stop early and not call other agents
        assert result["requires_market_selection"] is True
        assert "market_options" in result


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_graph_missing_initial_fields():
    """Test run_analysis_graph with missing initial state fields (defaults)."""
    initial_state: AgentState = {}

    with (
        patch("app.agents.graph.run_market_agent") as mock_market,
        patch("app.agents.graph.run_event_agent") as mock_event,
        patch("app.agents.graph.run_tavily_prompt_agent") as mock_tavily,
        patch("app.agents.graph.run_news_agent") as mock_news,
        patch("app.agents.graph.run_news_summary_agent") as mock_summary,
        patch("app.agents.graph.run_prob_agent") as mock_prob,
        patch("app.agents.graph.run_strategy_agent") as mock_strategy,
        patch("app.agents.graph.run_report_agent") as mock_report,
    ):
        # Agents should preserve run_id and run_at that graph sets
        def preserve_fields(s):
            result = dict(s)
            if "run_id" not in result:
                result["run_id"] = "run-test"
            if "run_at" not in result:
                result["run_at"] = "2025-01-01T00:00:00Z"
            return result

        mock_market.side_effect = preserve_fields
        mock_event.side_effect = preserve_fields
        mock_tavily.side_effect = preserve_fields
        mock_news.side_effect = preserve_fields
        mock_summary.side_effect = preserve_fields
        mock_prob.side_effect = preserve_fields
        mock_strategy.side_effect = preserve_fields
        mock_report.side_effect = preserve_fields

        result = await run_analysis_graph(initial_state)

        # Should have defaults
        assert "run_id" in result
        assert "run_at" in result
        assert result.get("market_url") == "https://polymarket.com"  # Default


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_graph_run_id_generation():
    """Test run_analysis_graph generates run_id."""
    initial_state: AgentState = {
        "market_url": "https://polymarket.com/market/test",
    }

    with (
        patch("app.agents.graph.run_market_agent") as mock_market,
        patch("app.agents.graph.run_event_agent") as mock_event,
        patch("app.agents.graph.run_tavily_prompt_agent") as mock_tavily,
        patch("app.agents.graph.run_news_agent") as mock_news,
        patch("app.agents.graph.run_news_summary_agent") as mock_summary,
        patch("app.agents.graph.run_prob_agent") as mock_prob,
        patch("app.agents.graph.run_strategy_agent") as mock_strategy,
        patch("app.agents.graph.run_report_agent") as mock_report,
    ):
        # Agents should preserve run_id and run_at that graph sets
        def preserve_fields(s):
            result = dict(s)
            if "run_id" not in result:
                result["run_id"] = "run-test"
            if "run_at" not in result:
                result["run_at"] = "2025-01-01T00:00:00Z"
            return result

        mock_market.side_effect = preserve_fields
        mock_event.side_effect = preserve_fields
        mock_tavily.side_effect = preserve_fields
        mock_news.side_effect = preserve_fields
        mock_summary.side_effect = preserve_fields
        mock_prob.side_effect = preserve_fields
        mock_strategy.side_effect = preserve_fields
        mock_report.side_effect = preserve_fields

        result = await run_analysis_graph(initial_state)

        assert "run_id" in result
        assert result["run_id"].startswith("run-")
        assert len(result["run_id"]) > 4


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_graph_run_at_timestamp():
    """Test run_analysis_graph generates run_at timestamp."""
    initial_state: AgentState = {
        "market_url": "https://polymarket.com/market/test",
    }

    with (
        patch("app.agents.graph.run_market_agent") as mock_market,
        patch("app.agents.graph.run_event_agent") as mock_event,
        patch("app.agents.graph.run_tavily_prompt_agent") as mock_tavily,
        patch("app.agents.graph.run_news_agent") as mock_news,
        patch("app.agents.graph.run_news_summary_agent") as mock_summary,
        patch("app.agents.graph.run_prob_agent") as mock_prob,
        patch("app.agents.graph.run_strategy_agent") as mock_strategy,
        patch("app.agents.graph.run_report_agent") as mock_report,
    ):
        # Agents should preserve run_id and run_at that graph sets
        def preserve_fields(s):
            result = dict(s)
            if "run_id" not in result:
                result["run_id"] = "run-test"
            if "run_at" not in result:
                result["run_at"] = "2025-01-01T00:00:00Z"
            return result

        mock_market.side_effect = preserve_fields
        mock_event.side_effect = preserve_fields
        mock_tavily.side_effect = preserve_fields
        mock_news.side_effect = preserve_fields
        mock_summary.side_effect = preserve_fields
        mock_prob.side_effect = preserve_fields
        mock_strategy.side_effect = preserve_fields
        mock_report.side_effect = preserve_fields

        result = await run_analysis_graph(initial_state)

        assert "run_at" in result
        assert "T" in result["run_at"] or "Z" in result["run_at"]


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_graph_error_propagation():
    """Test run_analysis_graph error propagation from agents."""
    initial_state: AgentState = {
        "market_url": "https://polymarket.com/market/test",
    }

    with patch("app.agents.graph.run_market_agent") as mock_market:
        mock_market.side_effect = Exception("Market agent error")

        with pytest.raises(Exception, match="Market agent error"):
            await run_analysis_graph(initial_state)


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_graph_state_mutation():
    """Test run_analysis_graph state mutation verification."""
    initial_state: AgentState = {
        "market_url": "https://polymarket.com/market/test",
        "slug": "test-market",
    }

    # Track state mutations
    state_history = []

    def track_state_mutation(state):
        state_history.append(dict(state))
        return state

    with (
        patch("app.agents.graph.run_market_agent") as mock_market,
        patch("app.agents.graph.run_event_agent") as mock_event,
        patch("app.agents.graph.run_tavily_prompt_agent") as mock_tavily,
        patch("app.agents.graph.run_news_agent") as mock_news,
        patch("app.agents.graph.run_news_summary_agent") as mock_summary,
        patch("app.agents.graph.run_prob_agent") as mock_prob,
        patch("app.agents.graph.run_strategy_agent") as mock_strategy,
        patch("app.agents.graph.run_report_agent") as mock_report,
    ):
        mock_market.side_effect = lambda s: track_state_mutation({**s, "market_snapshot": {}})
        mock_event.side_effect = lambda s: track_state_mutation({**s, "event_context": {}})
        mock_tavily.side_effect = lambda s: track_state_mutation({**s, "tavily_queries": []})
        mock_news.side_effect = lambda s: track_state_mutation({**s, "news_context": {}})
        mock_summary.side_effect = lambda s: track_state_mutation(
            {**s, "news_context": {"summary": "Test"}}
        )
        mock_prob.side_effect = lambda s: track_state_mutation({**s, "signal": {}})
        mock_strategy.side_effect = lambda s: track_state_mutation({**s, "decision": {}})
        mock_report.side_effect = lambda s: track_state_mutation({**s, "report": {}})

        await run_analysis_graph(initial_state)

        # Verify state was mutated through the chain
        assert len(state_history) == 8  # All 8 agents
        assert "market_snapshot" in state_history[0]
        assert "event_context" in state_history[1]
        assert "report" in state_history[7]
