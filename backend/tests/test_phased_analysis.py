"""Tests for Phased Analysis."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.schemas import AnalyzeRequest
from app.services.phased_analysis import run_analysis_for_run_id


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_for_run_id_full_flow():
    """Test run_analysis_for_run_id full analysis flow."""
    req = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
        horizon="24h",
        strategy_preset="Balanced",
    )

    mock_state = {
        "run_id": "test-run",
        "market_snapshot": {"yes_price": 0.5},
        "event_context": {"title": "Test Event"},
        "news_context": {"articles": [], "summary": "Test summary"},
        "signal": {"direction": "up", "model_prob": 0.6},
        "decision": {"action": "BUY_YES"},
        "report": {"headline": "Test Report"},
    }

    with (
        patch("app.services.phased_analysis.run_analysis_graph", new_callable=AsyncMock) as mock_graph,
        patch("app.services.phased_analysis.update_run_phase_async", new_callable=AsyncMock) as mock_update,
        patch("app.services.phased_analysis.update_run_with_event_and_market_async", new_callable=AsyncMock) as mock_update_ids,
        patch("app.services.phased_analysis.persist_run_snapshot_async", new_callable=AsyncMock) as mock_persist,
    ):
        mock_graph.return_value = mock_state

        await run_analysis_for_run_id("test-run", req)

        # Verify graph was called
        assert mock_graph.called

        # Verify all phases were updated
        assert mock_update.call_count >= 3  # market, news, signal, report phases
        assert mock_update_ids.called
        assert mock_persist.called


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_for_run_id_market_selection():
    """Test run_analysis_for_run_id with market selection required."""
    req = AnalyzeRequest(
        market_url="https://polymarket.com/event/test",
    )

    mock_state = {
        "run_id": "test-run",
        "requires_market_selection": True,
        "market_options": [{"slug": "market-1"}],
        "event_context": {"title": "Test Event"},
    }

    with (
        patch("app.services.phased_analysis.run_analysis_graph", new_callable=AsyncMock) as mock_graph,
        patch("app.services.phased_analysis.update_run_phase_async", new_callable=AsyncMock) as mock_update,
    ):
        mock_graph.return_value = mock_state

        await run_analysis_for_run_id("test-run", req)

        # Should update market phase only (early return)
        assert mock_update.called
        # Should have called update once for market selection status
        assert mock_update.call_count == 1


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_for_run_id_error_handling():
    """Test run_analysis_for_run_id error handling."""
    req = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
    )

    with (
        patch("app.services.phased_analysis.run_analysis_graph", new_callable=AsyncMock) as mock_graph,
        patch("app.services.phased_analysis.update_run_phase_async", new_callable=AsyncMock) as mock_update,
    ):
        mock_graph.side_effect = Exception("Graph execution error")

        with pytest.raises(Exception, match="Graph execution error"):
            await run_analysis_for_run_id("test-run", req)

        # Should mark phases as error
        assert mock_update.called
        # Check that error status was set for phases
        error_calls = [call for call in mock_update.call_args_list if "error" in call.args]
        assert len(error_calls) >= 1


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_for_run_id_phase_updates():
    """Test run_analysis_for_run_id phase updates."""
    req = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
    )

    mock_state = {
        "run_id": "test-run",
        "market_snapshot": {"yes_price": 0.5},
        "event_context": {"title": "Test Event"},
        "news_context": {"articles": [{"title": "Article 1"}], "summary": "Summary"},
        "signal": {"direction": "up"},
        "decision": {"action": "HOLD"},
        "report": {"headline": "Report"},
    }

    with (
        patch("app.services.phased_analysis.run_analysis_graph", new_callable=AsyncMock) as mock_graph,
        patch("app.services.phased_analysis.update_run_phase_async", new_callable=AsyncMock) as mock_update,
        patch("app.services.phased_analysis.update_run_with_event_and_market_async", new_callable=AsyncMock) as mock_update_ids,
        patch("app.services.phased_analysis.persist_run_snapshot_async", new_callable=AsyncMock) as mock_persist,
    ):
        mock_graph.return_value = mock_state

        await run_analysis_for_run_id("test-run", req)

        # Should update phases: market, news, signal, report
        assert mock_update.call_count >= 3

        # Verify phase names in calls
        called_phases = [call.args[1] for call in mock_update.call_args_list]
        assert "market" in called_phases
        assert "news" in called_phases
        assert "signal" in called_phases
