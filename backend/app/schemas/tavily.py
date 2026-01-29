"""Pydantic models for Tavily API responses."""

from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _extract_source_from_url(url: str) -> str:
    """Extract source domain from URL."""
    if not url:
        return "Unknown source"
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "") or "Unknown source"
    except Exception:
        return "Unknown source"


def _create_snippet(content: str | None, max_length: int = 240) -> str | None:
    """Create a truncated snippet from content."""
    if not content:
        return None
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."


class TavilyRawArticle(BaseModel):
    """Raw article structure from Tavily API response."""

    title: str
    url: str
    content: Optional[str] = None
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    published_date: Optional[str] = None
    published_at: Optional[str] = None
    source: Optional[str] = None
    image: Optional[str] = None


class TavilySearchResponse(BaseModel):
    """Complete Tavily API search response."""

    query: Optional[str] = None
    answer: Optional[str] = None
    results: List[TavilyRawArticle] = Field(default_factory=list)
    response_time: Optional[float] = None
    images: Optional[List[str]] = None

    model_config = ConfigDict(extra="allow")


class TavilyArticle(BaseModel):
    """Processed/normalized article for internal use."""

    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    content: Optional[str] = None
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    image: Optional[str] = None
    sentiment: Optional[str] = None

    @classmethod
    def from_tavily_raw(cls, raw: TavilyRawArticle, snippet_length: int = 240) -> TavilyArticle:
        """Create TavilyArticle from raw Tavily response."""
        source = raw.source or _extract_source_from_url(raw.url)
        published_at = raw.published_date or raw.published_at

        return cls(
            title=raw.title,
            url=raw.url,
            source=source,
            published_at=published_at,
            snippet=_create_snippet(raw.content, snippet_length),
            content=raw.content,
            score=raw.score,
            image=raw.image,
            sentiment=None,
        )

    @classmethod
    def from_dict(cls, item: dict, snippet_length: int = 240) -> TavilyArticle:
        """Create TavilyArticle from a dictionary."""
        url = item.get("url", "")
        source = item.get("source") or _extract_source_from_url(url)
        content = item.get("content") or ""

        return cls(
            title=item.get("title", "Untitled"),
            url=url,
            source=source,
            published_at=item.get("published_date") or item.get("published_at"),
            snippet=_create_snippet(content, snippet_length),
            content=content if content else None,
            score=item.get("score"),
            image=item.get("image"),
            sentiment=None,
        )


class TavilySearchResult(BaseModel):
    """Processed Tavily search result for internal use."""

    answer: str = Field(default="")
    articles: List[TavilyArticle] = Field(default_factory=list)
    query: Optional[str] = None
    response_time: Optional[float] = None

    @classmethod
    def from_api_response(cls, api_response: dict) -> TavilySearchResult:
        """Create TavilySearchResult from raw API response."""
        try:
            parsed = TavilySearchResponse.model_validate(api_response)
            articles = [TavilyArticle.from_tavily_raw(raw) for raw in parsed.results]

            return cls(
                answer=parsed.answer or "",
                articles=articles,
                query=parsed.query,
                response_time=parsed.response_time,
            )
        except Exception as e:
            logger.warning(
                "Failed to parse Tavily response with Pydantic, using fallback",
                error=str(e),
            )
            return cls._from_api_response_fallback(api_response)

    @classmethod
    def _from_api_response_fallback(cls, api_response: dict) -> TavilySearchResult:
        """Fallback parsing when Pydantic validation fails."""
        articles = []
        for item in api_response.get("results", []):
            try:
                raw_article = TavilyRawArticle.model_validate(item)
                articles.append(TavilyArticle.from_tavily_raw(raw_article))
            except Exception:
                articles.append(TavilyArticle.from_dict(item))

        return cls(
            answer=api_response.get("answer", ""),
            articles=articles,
            query=api_response.get("query"),
            response_time=api_response.get("response_time"),
        )
