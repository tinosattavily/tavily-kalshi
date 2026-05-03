"""FastAPI dependency injection for service clients."""

from __future__ import annotations

from app.infrastructure.llm import OpenAIClient, get_openai_client


async def get_openai_client_dep() -> OpenAIClient:
    """FastAPI dependency for OpenAIClient."""
    return get_openai_client()
