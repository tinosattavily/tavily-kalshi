"""Tests for News Summary Agent."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.news.summarizer import generate_fallback_summary
from app.orchestration.agents.summarizer import run_summarizer
from app.orchestration.state import AgentState


def test_generate_fallback_summary_with_answers():
    """Test _generate_fallback_summary with answers."""
    event_title = "Test Event"
    answers = ["Answer 1", "Answer 2", "Answer 3"]
    articles = []

    summary = generate_fallback_summary(event_title, answers, articles)

    assert "Answer 1" in summary
    assert "Answer 2" in summary
    assert "Answer 3" in summary


def test_generate_fallback_summary_with_articles():
    """Test _generate_fallback_summary with articles."""
    event_title = "Test Event"
    answers = []
    articles = [
        {"title": "Article 1"},
        {"title": "Article 2"},
        {"title": "Article 3"},
    ]

    summary = generate_fallback_summary(event_title, answers, articles)

    assert "Article 1" in summary or "Article 2" in summary
    assert "Test Event" in summary


def test_generate_fallback_summary_without_articles():
    """Test _generate_fallback_summary without articles."""
    event_title = "Test Event"
    answers = []
    articles = []

    summary = generate_fallback_summary(event_title, answers, articles)

    assert "Test Event" in summary
    assert "cautious sentiment" in summary.lower() or "awaiting" in summary.lower()


def test_generate_fallback_summary_various_counts():
    """Test _generate_fallback_summary with various article counts."""
    event_title = "Test Event"

    # Single article
    summary1 = generate_fallback_summary(event_title, [], [{"title": "Single"}])
    assert len(summary1) > 0

    # Multiple articles
    summary2 = generate_fallback_summary(
        event_title, [], [{"title": f"Article {i}"} for i in range(5)]
    )
    assert len(summary2) > 0


@pytest.mark.anyio(backend="asyncio")
async def test_run_news_summary_agent_with_openai():
    """Test run_news_summary_agent with OpenAI available."""
    state: AgentState = {
        "event_context": {
            "title": "Test Event",
        },
        "market_snapshot": {
            "question": "Will this test pass?",
        },
        "news_context": {
            "articles": [
                {"title": "Article 1", "sentiment": "bullish"},
                {"title": "Article 2", "sentiment": "bearish"},
                {"title": "Article 3", "sentiment": "neutral"},
            ],
            "queries": [
                {"answer": "Answer 1"},
            ],
        },
    }

    mock_summary = "Generated summary from OpenAI"

    with patch("app.domains.news.summarizer.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.summarize_news_with_sentiment = AsyncMock(return_value=mock_summary)
        mock_get_client.return_value = mock_client

        result = await run_summarizer(state)

        assert result["news_context"]["summary"] == mock_summary
        assert mock_client.summarize_news_with_sentiment.called


@pytest.mark.anyio(backend="asyncio")
async def test_run_news_summary_agent_fallback():
    """Test run_news_summary_agent with fallback scenario."""
    state: AgentState = {
        "event_context": {
            "title": "Test Event",
        },
        "market_snapshot": {
            "question": "Will this test pass?",
        },
        "news_context": {
            "articles": [
                {"title": "Article 1"},
                {"title": "Article 2"},
            ],
            "queries": [
                {"answer": "Answer 1"},
            ],
        },
    }

    with patch("app.domains.news.summarizer.get_openai_client") as mock_get_client:
        mock_get_client.side_effect = RuntimeError("OpenAI not available")

        result = await run_summarizer(state)

        assert "summary" in result["news_context"]
        assert len(result["news_context"]["summary"]) > 0


@pytest.mark.anyio(backend="asyncio")
async def test_run_news_summary_agent_existing_summary():
    """Test run_news_summary_agent with existing summary."""
    existing_summary = "Existing summary"
    state: AgentState = {
        "event_context": {
            "title": "Test Event",
        },
        "market_snapshot": {},
        "news_context": {
            "summary": existing_summary,
            "articles": [{"title": "Article 1"}],
        },
    }

    result = await run_summarizer(state)

    assert result["news_context"]["summary"] == existing_summary


@pytest.mark.anyio(backend="asyncio")
async def test_run_news_summary_agent_too_few_articles():
    """Test run_news_summary_agent with too few articles for OpenAI."""
    state: AgentState = {
        "event_context": {
            "title": "Test Event",
        },
        "market_snapshot": {},
        "news_context": {
            "articles": [
                {"title": "Article 1"},  # Only 1 article, need 2+
            ],
        },
    }

    result = await run_summarizer(state)

    assert "summary" in result["news_context"]
    # Should use fallback since too few articles


@pytest.mark.anyio(backend="asyncio")
async def test_run_news_summary_agent_no_articles():
    """Test run_news_summary_agent with no articles."""
    state: AgentState = {
        "event_context": {
            "title": "Test Event",
        },
        "market_snapshot": {},
        "news_context": {
            "articles": [],
        },
    }

    result = await run_summarizer(state)

    assert "summary" in result["news_context"]
    assert "No recent news articles found for Test Event" in result["news_context"]["summary"]


@pytest.mark.anyio(backend="asyncio")
async def test_run_news_summary_agent_missing_news_context():
    """Test run_news_summary_agent with missing news_context."""
    state: AgentState = {
        "event_context": {
            "title": "Test Event",
        },
        "market_snapshot": {},
    }

    result = await run_summarizer(state)

    assert "news_context" in result
    assert "summary" in result["news_context"]


@pytest.mark.anyio(backend="asyncio")
async def test_run_news_summary_agent_openai_error():
    """Test run_news_summary_agent with OpenAI error."""
    state: AgentState = {
        "event_context": {
            "title": "Test Event",
        },
        "market_snapshot": {},
        "news_context": {
            "articles": [
                {"title": "Article 1"},
                {"title": "Article 2"},
            ],
        },
    }

    with patch("app.domains.news.summarizer.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.summarize_news_with_sentiment = AsyncMock(side_effect=Exception("API Error"))
        mock_get_client.return_value = mock_client

        result = await run_summarizer(state)

        assert "summary" in result["news_context"]
        # Should use fallback


@pytest.mark.anyio(backend="asyncio")
async def test_run_news_summary_agent_event_title_fallback():
    """Test run_news_summary_agent event title fallback chain."""
    # Test with event_data title
    state1: AgentState = {
        "event": {
            "title": "Event Title",
        },
        "market_snapshot": {},
        "news_context": {
            "articles": [],
        },
    }

    result1 = await run_summarizer(state1)
    assert "No recent news articles found for Event Title" in result1["news_context"]["summary"]

    # Test with market_snapshot question
    state2: AgentState = {
        "market_snapshot": {
            "question": "Market Question?",
        },
        "news_context": {
            "articles": [],
        },
    }

    result2 = await run_summarizer(state2)
    assert (
        "No recent news articles found for Market Question" in result2["news_context"]["summary"]
        or "No recent news articles found for Key event" in result2["news_context"]["summary"]
    )
