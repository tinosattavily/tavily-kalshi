"""Tests for Async MongoDB Client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

from app.infrastructure.database.client import (
    check_mongodb_health,
    close_async_client,
    get_async_client,
    get_async_db,
)


@pytest.mark.anyio(backend="asyncio")
async def test_get_async_client_successful_connection():
    """Test get_async_client successful connection."""
    # Reset the singleton
    import app.infrastructure.database.client

    app.infrastructure.database.client._client = None

    with (
        patch("app.infrastructure.database.client.settings") as mock_settings,
        patch("app.infrastructure.database.client.AsyncIOMotorClient") as mock_client_class,
    ):
        mock_settings.mongodb_uri = "mongodb://localhost:27017/test"
        mock_client = AsyncMock(spec=AsyncIOMotorClient)
        mock_admin = MagicMock()
        mock_admin.command = AsyncMock()
        mock_client.admin = mock_admin
        mock_client_class.return_value = mock_client

        client = await get_async_client()

        assert client == mock_client
        assert mock_client.admin.command.called


@pytest.mark.anyio(backend="asyncio")
async def test_get_async_client_connection_errors():
    """Test get_async_client with connection errors."""
    # Reset the singleton
    import app.infrastructure.database.client

    app.infrastructure.database.client._client = None

    with (
        patch("app.infrastructure.database.client.settings") as mock_settings,
        patch("app.infrastructure.database.client.AsyncIOMotorClient") as mock_client_class,
    ):
        mock_settings.mongodb_uri = "mongodb://localhost:27017/test"
        mock_client = AsyncMock()
        mock_admin = MagicMock()
        mock_admin.command = AsyncMock(side_effect=ConnectionFailure("Connection failed"))
        mock_client.admin = mock_admin
        mock_client_class.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to connect"):
            await get_async_client()


@pytest.mark.anyio(backend="asyncio")
async def test_get_async_client_missing_uri():
    """Test get_async_client with missing MongoDB URI."""
    # Reset the singleton
    import app.infrastructure.database.client

    app.infrastructure.database.client._client = None

    with patch("app.infrastructure.database.client.settings") as mock_settings:
        mock_settings.mongodb_uri = None

        with pytest.raises(RuntimeError, match="MONGODB_URI is not configured"):
            await get_async_client()


@pytest.mark.anyio(backend="asyncio")
async def test_get_async_client_singleton():
    """Test get_async_client singleton pattern."""
    # Reset the singleton
    import app.infrastructure.database.client

    app.infrastructure.database.client._client = None

    with (
        patch("app.infrastructure.database.client.settings") as mock_settings,
        patch("app.infrastructure.database.client.AsyncIOMotorClient") as mock_client_class,
    ):
        mock_settings.mongodb_uri = "mongodb://localhost:27017/test"
        mock_client = AsyncMock()
        mock_admin = MagicMock()
        mock_admin.command = AsyncMock()
        mock_client.admin = mock_admin
        mock_client_class.return_value = mock_client

        client1 = await get_async_client()
        client2 = await get_async_client()

        assert client1 is client2
        # Should only create client once
        assert mock_client_class.call_count == 1


@pytest.mark.anyio(backend="asyncio")
async def test_get_async_db():
    """Test get_async_db database retrieval."""
    with patch("app.infrastructure.database.client.get_async_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_get_client.return_value = mock_client

        db = await get_async_db()

        assert db == mock_db
        mock_client.__getitem__.assert_called_with("tavily_proj")


@pytest.mark.anyio(backend="asyncio")
async def test_check_mongodb_health_healthy():
    """Test check_mongodb_health with healthy database."""
    with patch("app.infrastructure.database.client.get_async_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_admin = MagicMock()
        mock_admin.command = AsyncMock()
        mock_client.admin = mock_admin
        mock_get_client.return_value = mock_client

        healthy, message = await check_mongodb_health()

        assert healthy is True
        assert "healthy" in message.lower()


@pytest.mark.anyio(backend="asyncio")
async def test_check_mongodb_health_unhealthy():
    """Test check_mongodb_health with unhealthy database."""
    with patch("app.infrastructure.database.client.get_async_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_admin = MagicMock()
        mock_admin.command = AsyncMock(side_effect=Exception("Connection failed"))
        mock_client.admin = mock_admin
        mock_get_client.return_value = mock_client

        healthy, message = await check_mongodb_health()

        assert healthy is False
        assert "failed" in message.lower()


@pytest.mark.anyio(backend="asyncio")
async def test_close_async_client():
    """Test close_async_client."""
    with patch("app.infrastructure.database.client._client") as mock_client_global:
        mock_client = AsyncMock()
        mock_client.close = MagicMock()
        mock_client_global.__set__ = MagicMock()

        # Set the global client
        import app.infrastructure.database.client

        app.infrastructure.database.client._client = mock_client

        await close_async_client()

        assert mock_client.close.called
        assert app.infrastructure.database.client._client is None


@pytest.mark.anyio(backend="asyncio")
async def test_close_async_client_none():
    """Test close_async_client when client is None."""
    import app.infrastructure.database.client

    app.infrastructure.database.client._client = None

    # Should not crash
    await close_async_client()
