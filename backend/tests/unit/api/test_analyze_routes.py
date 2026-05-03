"""Tests for Analyze Routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.api.schemas.requests import AnalyzeRequest
from app.main import app

client = TestClient(app)


@pytest.mark.anyio(backend="asyncio")
async def test_analyze_endpoint_valid_request():
    """Test /analyze endpoint with valid request."""
    payload = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
        horizon="24h",
        strategy_preset="Balanced",
    )

    with (
        patch("app.api.routes.analyze.run_analysis_graph") as mock_graph,
        patch("app.api.routes.analyze.persist_run_snapshot_async") as mock_persist,
    ):
        mock_state = {
            "market_snapshot": {},
            "event_context": {},
            "news_context": {},
            "signal": {},
            "decision": {},
            "report": {},
        }
        mock_graph.return_value = mock_state
        mock_persist.return_value = {"run_id": "test-run"}

        # Create a mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"content-length": "100"}
        mock_request.state.request_id = "test-request-id"

        with patch("app.api.routes.analyze.Request", return_value=mock_request):
            response = client.post("/api/analyze", json=payload.model_dump(mode="json"))

            # Should succeed (200 or appropriate status)
            assert response.status_code in [200, 201]


@pytest.mark.anyio(backend="asyncio")
async def test_analyze_endpoint_request_too_large():
    """Test /analyze endpoint with request too large (413)."""
    payload = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
    )

    # Set content-length header directly - TestClient will pass it to the request
    response = client.post(
        "/api/analyze",
        json=payload.model_dump(mode="json"),
        headers={"content-length": str(2 * 1024 * 1024)},  # 2MB
    )

    # Should return 413
    assert response.status_code == 413


@pytest.mark.anyio(backend="asyncio")
async def test_analyze_endpoint_market_selection_required():
    """Test /analyze endpoint with market selection required."""
    payload = AnalyzeRequest(
        market_url="https://polymarket.com/event/test",
    )

    with patch("app.api.routes.analyze.run_analysis_graph") as mock_graph:
        mock_state = {
            "requires_market_selection": True,
            "market_options": [{"slug": "market-1"}],
            "event_context": {},
        }
        mock_graph.return_value = mock_state

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"content-length": "100"}
        mock_request.state.request_id = "test-request-id"

        with patch("app.api.routes.analyze.Request", return_value=mock_request):
            response = client.post("/api/analyze", json=payload.model_dump(mode="json"))

            # Should return market selection response
            assert response.status_code == 200
            data = response.json()
            assert data.get("requires_market_selection") is True


@pytest.mark.anyio(backend="asyncio")
async def test_analyze_endpoint_database_error():
    """Test /analyze endpoint with database persistence error."""
    payload = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
    )

    with (
        patch("app.api.routes.analyze.run_analysis_graph") as mock_graph,
        patch("app.api.routes.analyze.persist_run_snapshot_async") as mock_persist,
    ):
        mock_state = {
            "market_snapshot": {},
            "event_context": {},
            "news_context": {},
            "signal": {},
            "decision": {},
            "report": {},
        }
        mock_graph.return_value = mock_state
        mock_persist.side_effect = Exception("Database error")

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"content-length": "100"}
        mock_request.state.request_id = "test-request-id"

        with patch("app.api.routes.analyze.Request", return_value=mock_request):
            response = client.post("/api/analyze", json=payload.model_dump(mode="json"))

            # Should still succeed (database error is non-fatal)
            assert response.status_code in [200, 201]


@pytest.mark.anyio(backend="asyncio")
async def test_analyze_endpoint_error_handling():
    """Test /analyze endpoint error handling (500)."""
    payload = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
    )

    with patch("app.api.routes.analyze.run_analysis_graph") as mock_graph:
        mock_graph.side_effect = Exception("Analysis error")

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"content-length": "100"}
        mock_request.state.request_id = "test-request-id"

        with patch("app.api.routes.analyze.Request", return_value=mock_request):
            response = client.post("/api/analyze", json=payload.model_dump(mode="json"))

            # Should return 500
            assert response.status_code == 500


@pytest.mark.anyio(backend="asyncio")
async def test_analyze_start_endpoint():
    """Test /analyze/start endpoint."""
    payload = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
        horizon="24h",
    )

    with (
        patch("app.api.routes.analyze.init_run_document_async") as mock_init,
        patch("app.api.routes.analyze.run_analysis_for_run_id"),
    ):
        mock_init.return_value = AsyncMock()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"content-length": "100"}
        mock_request.state.request_id = "test-request-id"
        mock_background_tasks = MagicMock()

        with (
            patch("app.api.routes.analyze.Request", return_value=mock_request),
            patch("app.api.routes.analyze.BackgroundTasks", return_value=mock_background_tasks),
        ):
            response = client.post("/api/analyze/start", json=payload.model_dump(mode="json"))

            assert response.status_code == 200
            data = response.json()
            assert "run_id" in data
            assert data["run_id"].startswith("run-")


@pytest.mark.anyio(backend="asyncio")
async def test_analyze_start_accepts_kalshi_url():
    """Test /analyze/start accepts Kalshi URLs."""
    payload = AnalyzeRequest(
        market_url="https://kalshi.com/markets/INXD-25JAN17-B24999",
        horizon="24h",
    )

    with (
        patch("app.api.routes.analyze.init_run_document_async") as mock_init,
        patch("app.api.routes.analyze.run_analysis_for_run_id"),
    ):
        mock_init.return_value = AsyncMock()

        response = client.post("/api/analyze/start", json=payload.model_dump(mode="json"))

        assert response.status_code == 200
        assert "run_id" in response.json()


@pytest.mark.anyio(backend="asyncio")
async def test_analyze_start_request_too_large():
    """Test /analyze/start endpoint with request too large."""
    payload = AnalyzeRequest(
        market_url="https://polymarket.com/market/test",
    )

    # Set content-length header directly
    response = client.post(
        "/api/analyze/start",
        json=payload.model_dump(mode="json"),
        headers={"content-length": str(2 * 1024 * 1024)},  # 2MB
    )

    assert response.status_code == 413


@pytest.mark.anyio(backend="asyncio")
async def test_reset_circuit_breaker():
    """Test /reset-circuit-breaker endpoint."""
    with patch("app.api.routes.analyze.openai_circuit") as mock_circuit:
        mock_circuit.state.value = "open"
        mock_circuit.reset = MagicMock()

        response = client.post("/api/reset-circuit-breaker")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert mock_circuit.reset.called
