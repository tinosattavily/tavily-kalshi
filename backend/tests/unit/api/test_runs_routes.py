"""Tests for Runs Routes."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_runs_by_market_route_removed():
    """Ambiguous market_id query route should not be public."""
    response = client.get("/api/runs?market_id=507f1f77bcf86cd799439011")
    assert response.status_code == 404


@pytest.mark.anyio(backend="asyncio")
async def test_list_recent_runs_valid():
    """Test /runs/recent endpoint."""
    mock_runs = [{"run_id": "run-1", "market_snapshot": {}}]

    with patch("app.api.routes.runs.list_recent_runs_async") as mock_list:
        mock_list.return_value = mock_runs

        response = client.get("/api/runs/recent")

        assert response.status_code == 200
        assert response.json()["runs"] == mock_runs


@pytest.mark.anyio(backend="asyncio")
async def test_get_run_detail_valid():
    """Test /run/{run_id} endpoint with valid run_id."""
    mock_run = {
        "run_id": "test-run",
        "market_snapshot": {"yes_price": 0.5},
        "status": {
            "market": "done",
            "news": "done",
            "signal": "done",
            "report": "done",
        },
    }

    with patch("app.api.routes.runs.get_run_async") as mock_get:
        mock_get.return_value = mock_run

        response = client.get("/api/run/test-run")

        assert response.status_code == 200
        data = response.json()
        assert "run" in data
        assert data["run"]["run_id"] == "test-run"


@pytest.mark.anyio(backend="asyncio")
async def test_get_run_detail_not_found():
    """Test /run/{run_id} endpoint with run not found (404)."""
    with patch("app.api.routes.runs.get_run_async") as mock_get:
        mock_get.return_value = None

        response = client.get("/api/run/non-existent")

        assert response.status_code == 404


@pytest.mark.anyio(backend="asyncio")
async def test_get_run_detail_invalid_id():
    """Test /run/{run_id} endpoint with invalid run_id (400)."""
    with patch("app.api.routes.runs.get_run_async") as mock_get:
        mock_get.side_effect = ValueError("Invalid ObjectId")

        response = client.get("/api/run/invalid-id")

        assert response.status_code == 400


@pytest.mark.anyio(backend="asyncio")
async def test_get_run_detail_database_error():
    """Test /run/{run_id} endpoint with database errors (500)."""
    with patch("app.api.routes.runs.get_run_async") as mock_get:
        mock_get.side_effect = Exception("Database error")

        response = client.get("/api/run/test-run")

        assert response.status_code == 500
