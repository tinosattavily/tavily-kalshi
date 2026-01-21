"""Tests for Tavily Schemas."""

from __future__ import annotations

import pytest

from app.domains.news.schemas import (
    TavilyArticle,
    TavilyRawArticle,
    TavilySearchResponse,
    TavilySearchResult,
)


def test_tavily_raw_article_validation():
    """Test TavilyRawArticle validation."""
    article = TavilyRawArticle(
        title="Test Article",
        url="https://example.com/article",
        content="Test content",
        score=0.8,
        published_date="2025-11-15T00:00:00Z",
        source="Example",
    )

    assert article.title == "Test Article"
    assert article.url == "https://example.com/article"
    assert article.score == 0.8


def test_tavily_raw_article_missing_fields():
    """Test TavilyRawArticle with missing optional fields."""
    article = TavilyRawArticle(
        title="Test",
        url="https://example.com",
    )

    assert article.content is None
    assert article.score is None


def test_tavily_raw_article_invalid_score():
    """Test TavilyRawArticle with invalid score."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TavilyRawArticle(
            title="Test",
            url="https://example.com",
            score=1.5,  # Invalid: > 1.0
        )


def test_tavily_search_response():
    """Test TavilySearchResponse validation."""
    response = TavilySearchResponse(
        query="test query",
        answer="Test answer",
        results=[],
    )

    assert response.query == "test query"
    assert response.answer == "Test answer"
    assert len(response.results) == 0


def test_tavily_article_from_raw():
    """Test TavilyArticle.from_tavily_raw."""
    raw = TavilyRawArticle(
        title="Test Article",
        url="https://example.com/article",
        content="This is a long content that will be truncated for the snippet",
        source="Example",
    )

    article = TavilyArticle.from_tavily_raw(raw)

    assert article.title == "Test Article"
    assert article.url == "https://example.com/article"
    assert article.source == "Example"
    assert article.snippet is not None
    assert len(article.snippet) <= 243  # 240 + "..."


def test_tavily_article_from_raw_no_source():
    """Test TavilyArticle.from_tavily_raw with no source (extract from URL)."""
    raw = TavilyRawArticle(
        title="Test",
        url="https://www.example.com/article",
    )

    article = TavilyArticle.from_tavily_raw(raw)

    assert article.source == "example.com"  # Extracted from URL


def test_tavily_search_result_from_api_response():
    """Test TavilySearchResult.from_api_response."""
    api_response = {
        "query": "test query",
        "answer": "Test answer",
        "results": [
            {
                "title": "Article 1",
                "url": "https://example.com/1",
                "content": "Content 1",
                "source": "Example",
            }
        ],
    }

    result = TavilySearchResult.from_api_response(api_response)

    assert result.query == "test query"
    assert result.answer == "Test answer"
    assert len(result.articles) == 1
    assert result.articles[0].title == "Article 1"


def test_tavily_search_result_fallback_parsing():
    """Test TavilySearchResult.from_api_response with fallback parsing."""
    api_response = {
        "answer": "Test",
        "results": [
            {
                "title": "Article 1",
                "url": "https://example.com/1",
                # Missing some fields
            }
        ],
    }

    result = TavilySearchResult.from_api_response(api_response)

    assert len(result.articles) == 1
    assert result.articles[0].title == "Article 1"
