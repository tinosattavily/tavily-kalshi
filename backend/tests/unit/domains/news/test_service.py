"""Tests for News Agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.domains.news.fetcher import normalize_tavily_queries
from app.domains.news.query_generator import build_fallback_query
from app.orchestration.agents.article_fetcher import run_article_fetcher
from app.orchestration.state import AgentState


def test_normalize_tavily_queries_from_strings():
    """Test normalizing legacy format (list of strings) to TavilyQuerySpec."""
    raw = ["query 1", "query 2"]

    specs = normalize_tavily_queries(raw)

    assert len(specs) == 2
    assert specs[0]["name"] == "legacy"
    assert specs[0]["query"] == "query 1"
    assert specs[0]["max_results"] == 8
    assert specs[0]["search_depth"] == "basic"

    assert specs[1]["query"] == "query 2"


def test_normalize_tavily_queries_from_specs():
    """Test normalizing new format (list of TavilyQuerySpec dicts)."""
    raw = [
        {
            "name": "latest_news",
            "query": "Recent developments",
            "max_results": 10,
            "search_depth": "advanced",
        },
        {
            "name": "fundamentals",
            "query": "Background factors",
            "max_results": 8,
        },
    ]

    specs = normalize_tavily_queries(raw)

    assert len(specs) == 2
    assert specs[0]["name"] == "latest_news"
    assert specs[0]["query"] == "Recent developments"
    assert specs[0]["max_results"] == 10
    assert specs[0]["search_depth"] == "advanced"

    assert specs[1]["name"] == "fundamentals"
    assert specs[1]["search_depth"] == "basic"  # Default applied


def test_normalize_tavily_queries_mixed_format():
    """Test normalizing mixed format (strings and specs)."""
    raw = [
        "legacy string query",
        {
            "name": "structured",
            "query": "Structured query",
            "max_results": 6,
        },
    ]

    specs = normalize_tavily_queries(raw)

    assert len(specs) == 2
    assert specs[0]["name"] == "legacy"
    assert specs[0]["query"] == "legacy string query"
    assert specs[1]["name"] == "structured"
    assert specs[1]["query"] == "Structured query"


def test_normalize_tavily_queries_empty():
    """Test normalizing empty or None input."""
    assert len(normalize_tavily_queries(None)) == 0
    assert len(normalize_tavily_queries([])) == 0


def test_normalize_tavily_queries_invalid_items_skipped():
    """Test that invalid items are skipped."""
    raw = [
        "valid string",
        {"query": "valid dict"},
        {"name": "no query"},  # Missing query field
        123,  # Invalid type
    ]

    specs = normalize_tavily_queries(raw)

    assert len(specs) == 2  # Only valid string and valid dict
    assert specs[0]["query"] == "valid string"
    assert specs[1]["query"] == "valid dict"


def test_build_fallback_query():
    """Test building fallback query from state."""
    query = build_fallback_query("Fed Decision", "Will rates increase?")

    assert "Fed Decision" in query or "rates increase" in query
    assert isinstance(query, str)
    assert len(query) > 0


@patch("app.domains.news.fetcher.search_news")
@pytest.mark.anyio(backend="asyncio")
async def test_run_news_agent_with_structured_queries(mock_search_news):
    """Test news agent with structured TavilyQuerySpec queries."""
    # Mock Tavily search results
    mock_search_news.return_value = {
        "answer": "Test answer",
        "articles": [
            {
                "title": "Article 1",
                "url": "https://example.com/1",
                "source": "Example",
                "snippet": "Snippet 1",
            },
            {
                "title": "Article 2",
                "url": "https://example.com/2",
                "source": "Example",
                "snippet": "Snippet 2",
            },
        ],
    }

    state: AgentState = {
        "tavily_queries": [
            {
                "name": "query1",
                "query": "Test query 1",
                "max_results": 5,
                "search_depth": "basic",
            },
            {
                "name": "query2",
                "query": "Test query 2",
                "max_results": 3,
                "search_depth": "advanced",
            },
        ],
        "event_context": {"title": "Test Event"},
        "market_snapshot": {"question": "Test question"},
        "config": {
            "enable_sentiment_analysis": False,
            "max_articles_per_query": 5,
            "max_articles": 15,
        },
    }

    result = await run_article_fetcher(state)

    # Verify Tavily was called for each query
    assert mock_search_news.call_count == 2

    # Verify news_context structure
    assert "news_context" in result
    news_ctx = result["news_context"]

    assert "queries" in news_ctx
    assert len(news_ctx["queries"]) == 2
    assert news_ctx["queries"][0]["name"] == "query1"
    assert news_ctx["queries"][1]["name"] == "query2"

    assert "articles" in news_ctx
    assert len(news_ctx["articles"]) == 2  # Deduplicated articles

    assert "combined_summary" in news_ctx
    assert "query1" in news_ctx["combined_summary"] or "query2" in news_ctx["combined_summary"]

    assert "tavily_queries" in news_ctx  # Backward compatibility
    assert news_ctx["tavily_queries"] == ["Test query 1", "Test query 2"]


@patch("app.domains.news.fetcher.search_news")
@pytest.mark.anyio(backend="asyncio")
async def test_run_news_agent_with_legacy_strings(mock_search_news):
    """Test news agent with legacy format (list of strings)."""
    mock_search_news.return_value = {
        "answer": "",
        "articles": [],
    }

    state: AgentState = {
        "tavily_queries": ["query string 1", "query string 2"],  # Legacy format
        "event_context": {"title": "Test Event"},
        "market_snapshot": {"question": "Test question"},
        "config": {
            "enable_sentiment_analysis": False,
            "max_articles_per_query": 5,
            "max_articles": 15,
        },
    }

    result = await run_article_fetcher(state)

    # Should normalize and call Tavily for each string
    assert mock_search_news.call_count == 2

    news_ctx = result["news_context"]
    assert len(news_ctx["queries"]) == 2
    assert news_ctx["queries"][0]["name"] == "legacy"
    assert news_ctx["queries"][0]["query"] == "query string 1"


@patch("app.domains.news.fetcher.search_news")
@pytest.mark.anyio(backend="asyncio")
async def test_run_news_agent_fallback(mock_search_news):
    """Test news agent fallback when tavily_queries is missing."""
    mock_search_news.return_value = {
        "answer": "",
        "articles": [],
    }

    state: AgentState = {
        # No tavily_queries - should use fallback
        "event_context": {"title": "Fed Decision"},
        "market_snapshot": {"question": "Will rates increase?"},
        "config": {
            "enable_sentiment_analysis": False,
            "max_articles_per_query": 5,
            "max_articles": 15,
        },
    }

    result = await run_article_fetcher(state)

    # Should use fallback query
    assert mock_search_news.call_count == 1

    news_ctx = result["news_context"]
    assert len(news_ctx["queries"]) == 1
    assert news_ctx["queries"][0]["name"] == "fallback"
    query_text = news_ctx["queries"][0]["query"]
    assert "Fed Decision" in query_text or "rates increase" in query_text
