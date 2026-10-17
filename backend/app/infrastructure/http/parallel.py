"""Optional anonymous Parallel Search MCP client for market research."""

from __future__ import annotations

import asyncio
import json
from urllib.parse import urlparse
from uuid import uuid4

from app.domains.news.schemas import TavilyArticle

PARALLEL_MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "prophecy-pred-markets/parallel-search"
SEARCH_TIMEOUT = 20
# Reuse one identity across related queries, including repeated calls and failures.
SESSION_ID = str(uuid4())


async def search_news(
    query: str, max_results: int = 5, search_depth: str | None = None
) -> dict:
    """Return search excerpts in the existing article format, without an API key.

    Anonymous search uses Fast mode. Tavily's search_depth does not apply, and
    max_results limits the returned articles locally. No answer or score is invented.
    Errors propagate to the news fetcher's existing per-query failure handling.
    """
    try:
        import httpx
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client
    except ImportError as exc:
        raise RuntimeError(
            "Parallel search requires: pip install -r backend/requirements-parallel.txt"
        ) from exc

    async with asyncio.timeout(SEARCH_TIMEOUT):
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=SEARCH_TIMEOUT
        ) as client:
            async with streamable_http_client(
                PARALLEL_MCP_URL, http_client=client
            ) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        "web_search",
                        {
                            "objective": (
                                f"Find current evidence for prediction-market research: {query}"
                            ),
                            "search_queries": [query],
                            "session_id": SESSION_ID,
                        },
                    )

    if result.isError:
        raise RuntimeError(f"Parallel search failed: {result.content}")
    data = result.structuredContent
    if data is None:
        # Older MCP servers can return the same JSON in a text content block.
        data = json.loads("\n".join(c.text for c in result.content if c.type == "text"))
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ValueError("Parallel search response is missing results")

    articles = []
    for item in data["results"]:
        url = item.get("url")
        if not isinstance(url, str) or urlparse(url).scheme not in ("http", "https"):
            continue
        content = "\n\n".join(item.get("excerpts") or [])
        article = TavilyArticle(
            title=item.get("title") or url,
            url=url,
            source=urlparse(url).netloc.removeprefix("www."),
            published_at=item.get("publish_date"),
            snippet=content[:240] + ("..." if len(content) > 240 else ""),
            content=content,
        )
        articles.append(article.model_dump())
    return {"answer": "", "articles": articles[:max(0, max_results)]}
