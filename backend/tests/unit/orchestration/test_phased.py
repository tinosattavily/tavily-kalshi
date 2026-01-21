"""Tests for Phased Analysis."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.api.schemas.requests import AnalyzeRequest
from app.orchestration.phased import run_analysis_for_run_id


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_for_run_id_full_flow():
    """Test run_analysis_for_run_id full analysis flow."""
    req = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
        horizon="24h",
        strategy_preset="Balanced",
    )

    with (
        patch("app.orchestration.phased.run_analysis_graph") as mock_graph,
        patch("app.orchestration.phased.update_run_phase_async") as mock_update,
        patch(
            "app.orchestration.phased.update_run_with_event_and_market_async"
        ) as mock_update_ids,
        patch("app.orchestration.phased.persist_run_snapshot_async") as mock_persist,
    ):
        # Setup mocks
        state = {
            "run_id": "test-run",
            "market_snapshot": {},
            "event_context": {},
            "news_context": {},
            "signal": {},
            "decision": {},
            "report": {},
        }
        mock_graph.return_value = state
        mock_update.return_value = AsyncMock()
        mock_update_ids.return_value = AsyncMock()
        mock_persist.return_value = AsyncMock()

        await run_analysis_for_run_id("test-run", req)

        assert mock_graph.called


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_for_run_id_market_selection():
    """Test run_analysis_for_run_id with market selection required."""
    req = AnalyzeRequest(
        market_url="https://polymarket.com/event/test",
    )

    with (
        patch("app.orchestration.phased.run_analysis_graph") as mock_graph,
        patch("app.orchestration.phased.update_run_phase_async") as mock_update,
    ):
        state = {
            "run_id": "test-run",
            "requires_market_selection": True,
            "market_options": [{"slug": "market-1"}],
            "event_context": {},
        }
        mock_graph.return_value = state
        mock_update.return_value = AsyncMock()

        await run_analysis_for_run_id("test-run", req)

        # Should stop early
        assert mock_update.called
        # Should not continue to other phases


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_for_run_id_error_handling():
    """Test run_analysis_for_run_id error handling."""
    req = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
    )

    with patch("app.orchestration.phased.run_analysis_graph") as mock_graph:
        mock_graph.side_effect = RuntimeError("Market agent error")

        with patch("app.orchestration.phased.update_run_phase_async") as mock_update:
            mock_update.return_value = AsyncMock()

            with pytest.raises(RuntimeError):
                await run_analysis_for_run_id("test-run", req)

            # Should mark phases as error
            assert mock_update.called


@pytest.mark.anyio(backend="asyncio")
async def test_run_analysis_for_run_id_phase_updates():
    """Test run_analysis_for_run_id phase updates."""
    req = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
    )

    with (
        patch("app.orchestration.phased.run_analysis_graph") as mock_graph,
        patch("app.orchestration.phased.update_run_phase_async") as mock_update,
        patch(
            "app.orchestration.phased.update_run_with_event_and_market_async"
        ) as mock_update_ids,
        patch("app.orchestration.phased.persist_run_snapshot_async") as mock_persist,
    ):
        state = {
            "run_id": "test-run",
            "market_snapshot": {},
            "event_context": {},
            "news_context": {},
            "signal": {},
            "decision": {},
            "report": {},
        }
        mock_graph.return_value = state
        mock_update.return_value = AsyncMock()
        mock_update_ids.return_value = AsyncMock()
        mock_persist.return_value = AsyncMock()

        await run_analysis_for_run_id("test-run", req)

        # Should update phases
        assert mock_update.call_count >= 3  # market, news, signal, report
