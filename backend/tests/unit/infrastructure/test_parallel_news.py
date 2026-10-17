"""Exercise the optional provider through the real MCP SDK and news pipeline."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("mcp", reason="Install requirements-parallel.txt for optional provider tests")
import httpx  # noqa: E402

from app.config import settings  # noqa: E402
from app.domains.news.fetcher import fetch_articles  # noqa: E402
from app.infrastructure.http import parallel  # noqa: E402
from app.orchestration.agents.article_fetcher import run_article_fetcher  # noqa: E402
from app.orchestration.agents.summarizer import run_summarizer  # noqa: E402

pytestmark = pytest.mark.asyncio


@pytest.fixture
def server(monkeypatch):
    """Replace only the network; keep MCP initialization, dispatch and parsing real."""
    state = {
        "requests": [],
        "clients": [],
        "called": asyncio.Event(),
        "mode": "structured",
        "data": {
            "results": [{
                "url": "https://www.example.com/rates",
                "title": "Rate decision evidence",
                "publish_date": "2026-10-16",
                "excerpts": ["The central bank held rates steady.", "The vote was unanimous."],
            }],
        },
    }

    async def handle(request):
        state["requests"].append(request)
        assert str(request.url) == parallel.PARALLEL_MCP_URL
        assert request.headers["User-Agent"] == parallel.USER_AGENT
        assert "authorization" not in request.headers
        if request.method != "POST":
            return httpx.Response(405)
        message = json.loads(request.content)
        method = message["method"]
        if method == "notifications/initialized":
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": message["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fixture", "version": "1"},
            }
        elif method == "tools/list":
            result = {"tools": [{"name": "web_search", "inputSchema": {"type": "object"}}]}
        elif method == "tools/call":
            state["called"].set()
            assert message["params"]["name"] == "web_search"
            if state["mode"] == "wait":
                await asyncio.Event().wait()
            if state["mode"] == "http_error":
                return httpx.Response(503, text="Service unavailable")
            result = {"content": [{"type": "text", "text": json.dumps(state["data"])}]}
            if state["mode"] == "structured":
                result["structuredContent"] = state["data"]
            if state["mode"] == "tool_error":
                result["isError"] = True
        else:
            raise AssertionError(method)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": message["id"], "result": result})

    original_client = httpx.AsyncClient

    def client(**kwargs):
        instance = original_client(transport=httpx.MockTransport(handle), **kwargs)
        state["clients"].append(instance)
        return instance

    monkeypatch.setattr(httpx, "AsyncClient", client)
    monkeypatch.setattr(settings, "news_search_provider", "parallel")
    monkeypatch.setattr("app.orchestration.agents.article_fetcher.TAVILY_API_KEY", None)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    tavily = AsyncMock(side_effect=AssertionError("Unexpected Tavily fallback"))
    monkeypatch.setattr("app.domains.news.fetcher.search_news", tavily)
    state["tavily"] = tavily
    yield state
    assert all(c.is_closed for c in state["clients"])


async def test_agent_dispatches_and_consumes_articles(server):
    state = {
        "tavily_queries": ["central bank rate decision", "central bank vote results"],
        "event_context": {"title": "Rate decision"},
        "market_snapshot": {"question": "Will rates change?"},
        "config": {"enable_sentiment_analysis": False, "max_articles": 1},
    }
    result = await run_summarizer(await run_article_fetcher(state))
    news = result["news_context"]
    assert len(news["articles"]) == 1  # Deduplicated across both queries.
    article = news["articles"][0]
    assert article["source"] == "example.com"
    assert article["published_at"] == "2026-10-16"
    assert article["content"] == "\n\n".join(server["data"]["results"][0]["excerpts"])
    assert article["score"] is None
    assert news["queries"][0]["answer"] == ""
    assert "Rate decision evidence" in news["summary"]
    messages = [json.loads(r.content) for r in server["requests"] if r.method == "POST"]
    calls = [m["params"]["arguments"] for m in messages if m["method"] == "tools/call"]
    assert [c["search_queries"] for c in calls] == [[q] for q in state["tavily_queries"]]
    assert {c["session_id"] for c in calls} == {parallel.SESSION_ID}
    assert all(c["objective"].endswith(c["search_queries"][0]) for c in calls)
    assert all("max_results" not in c and "search_depth" not in c for c in calls)
    server["tavily"].assert_not_called()


async def test_text_response_and_local_limit(server):
    server["mode"] = "text"
    server["data"]["results"] *= 3
    server["data"]["results"].append({"url": "javascript:invalid", "excerpts": []})
    result = await parallel.search_news("rate decision", max_results=2, search_depth="advanced")
    assert len(result["articles"]) == 2
    assert result["answer"] == ""


@pytest.mark.parametrize("mode", ["tool_error", "http_error", "malformed", "wait"])
async def test_failed_queries_leave_no_articles_without_fallback(server, monkeypatch, mode):
    server["mode"] = mode
    if mode == "malformed":
        server["data"] = {"unexpected": []}
    if mode == "wait":
        monkeypatch.setattr(parallel, "SEARCH_TIMEOUT", 0.05)
    articles, queries, answers = await fetch_articles([{"query": "rate decision"}])
    assert (articles, queries, answers) == ([], [], [])
    server["tavily"].assert_not_called()


async def test_cancellation_propagates_and_closes_transport(server):
    server["mode"] = "wait"
    task = asyncio.create_task(fetch_articles([{"query": "rate decision"}]))
    await asyncio.wait_for(server["called"].wait(), timeout=5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    server["tavily"].assert_not_called()


async def test_default_tavily_path_is_preserved(monkeypatch):
    from app.config import Settings

    monkeypatch.delenv("NEWS_SEARCH_PROVIDER", raising=False)
    assert Settings().news_search_provider == "tavily"
    monkeypatch.setattr(settings, "news_search_provider", "tavily")
    tavily = AsyncMock(return_value={"answer": "Existing answer", "articles": []})
    monkeypatch.setattr("app.domains.news.fetcher.search_news", tavily)
    await fetch_articles([{"query": "rate decision", "max_results": 6, "search_depth": "advanced"}])
    tavily.assert_awaited_once_with("rate decision", max_results=6, search_depth="advanced")


async def test_unknown_provider_is_explicit(monkeypatch):
    monkeypatch.setattr(settings, "news_search_provider", "unknown")
    with pytest.raises(ValueError, match="NEWS_SEARCH_PROVIDER"):
        await fetch_articles([{"query": "rate decision"}])


async def test_optional_sdk_missing_has_install_guidance(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def without_mcp(name, *args, **kwargs):
        if name == "mcp":
            raise ImportError("Optional dependency absent")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_mcp)
    with pytest.raises(RuntimeError, match="requirements-parallel.txt"):
        await parallel.search_news("rate decision")
