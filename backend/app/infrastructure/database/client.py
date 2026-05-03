"""Async MongoDB client using motor."""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import get_logger, settings

logger = get_logger(__name__)

_client: Optional[AsyncIOMotorClient] = None


async def get_async_client() -> AsyncIOMotorClient:
    """Return a shared AsyncIOMotorClient instance with connection pooling."""
    global _client
    if _client is None:
        if not settings.mongodb_uri:
            raise RuntimeError("MONGODB_URI is not configured")

        try:
            _client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                retryWrites=True,
                retryReads=True,
            )
            # Test connection
            await _client.admin.command("ping")
            logger.info("MongoDB connection established", max_pool_size=50, min_pool_size=10)
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Failed to connect to MongoDB", error=str(e))
            raise RuntimeError("Failed to connect to MongoDB") from e

    return _client


async def get_async_db():
    """Return the main application database."""
    client = await get_async_client()
    return client["tavily_proj"]


async def check_mongodb_health() -> tuple[bool, str]:
    """Check MongoDB connection health."""
    try:
        client = await get_async_client()
        await client.admin.command("ping")
        return True, "MongoDB connection healthy"
    except Exception as e:
        logger.warning("MongoDB health check failed", error=str(e))
        return False, f"MongoDB connection failed: {str(e)}"


async def close_async_client() -> None:
    """Close the async MongoDB client."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB async client closed")
