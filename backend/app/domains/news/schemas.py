# app/domains/news/schemas.py
"""Pydantic models for Tavily API responses."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TavilyRawArticle(BaseModel):
    """Raw article structure from Tavily API response.

    Based on Tavily API documentation, the response includes:
    - title: Article title
    - url: Article URL
    - content: Full article content
    - score: Relevance score (0-1)
    - published_date: Publication date (ISO format or string)
    - source: Source domain/website name
    - image: Optional image URL
    """

    title: str
    url: str
    content: Optional[str] = None
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score")
    published_date: Optional[str] = None
    published_at: Optional[str] = None  # Alternative field name
    source: Optional[str] = None
    image: Optional[str] = None

    @field_validator("published_date", "published_at", mode="before")
    @classmethod
    def parse_published_date(cls, v: str | None) -> str | None:
        """Parse published date - Tavily may return various formats."""
        if not v:
            return None
        # Return as-is, let the consumer handle parsing
        return str(v) if v else None


class TavilySearchResponse(BaseModel):
    """Complete Tavily API search response."""

    query: Optional[str] = None
    answer: Optional[str] = Field(None, description="AI-generated answer summary")
    results: List[TavilyRawArticle] = Field(default_factory=list)
    response_time: Optional[float] = None
    images: Optional[List[str]] = Field(None, description="Related images")

    class Config:
        extra = "allow"  # Allow extra fields from API that we don't model


class TavilyArticle(BaseModel):
    """Processed/normalized article for internal use.

    This is the cleaned version that we use throughout the application.
    """

    title: str
    url: str
    source: str = Field(..., description="Source domain or publication name")
    published_at: Optional[str] = Field(None, description="ISO format date string")
    snippet: Optional[str] = Field(None, description="Truncated content preview")
    content: Optional[str] = Field(None, description="Full content if available")
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score from Tavily")
    image: Optional[str] = None
    sentiment: Optional[str] = Field(None, description="bullish, bearish, or neutral")

    @classmethod
    def from_tavily_raw(cls, raw: TavilyRawArticle, snippet_length: int = 240) -> "TavilyArticle":
        """Create TavilyArticle from raw Tavily response.

        Args:
            raw: Raw article from Tavily API
            snippet_length: Maximum length for snippet

        Returns:
            Normalized TavilyArticle
        """
        # Extract source from URL if not provided
        source = raw.source
        if not source and raw.url:
            try:
                from urllib.parse import urlparse

                parsed = urlparse(raw.url)
                source = parsed.netloc.replace("www.", "")
            except Exception:
                source = "Unknown source"

        # Use published_date or published_at
        published_at = raw.published_date or raw.published_at

        # Create snippet from content
        snippet = None
        if raw.content:
            snippet = raw.content[:snippet_length]
            if len(raw.content) > snippet_length:
                snippet += "..."

        return cls(
            title=raw.title,
            url=raw.url,
            source=source or "Unknown source",
            published_at=published_at,
            snippet=snippet,
            content=raw.content,
            score=raw.score,
            image=raw.image,
            sentiment=None,  # Will be set by sentiment analysis
        )


class TavilySearchResult(BaseModel):
    """Processed Tavily search result for internal use."""

    answer: str = Field(default="", description="AI-generated answer summary")
    articles: List[TavilyArticle] = Field(default_factory=list)
    query: Optional[str] = None
    response_time: Optional[float] = None

    @classmethod
    def from_api_response(cls, api_response: dict) -> "TavilySearchResult":
        """Create TavilySearchResult from raw API response.

        Args:
            api_response: Raw JSON response from Tavily API

        Returns:
            Processed TavilySearchResult
        """
        try:
            # Try to parse with Pydantic model first
            parsed = TavilySearchResponse.model_validate(api_response)

            # Convert raw articles to processed articles
            articles = [
                TavilyArticle.from_tavily_raw(raw_article) for raw_article in parsed.results
            ]

            return cls(
                answer=parsed.answer or "",
                articles=articles,
                query=parsed.query,
                response_time=parsed.response_time,
            )
        except Exception as e:
            # Fallback: manual parsing if Pydantic validation fails
            from app.config import get_logger

            logger = get_logger(__name__)
            logger.warning(
                "Failed to parse Tavily response with Pydantic, using fallback",
                error=str(e),
            )

            raw_results = api_response.get("results", [])
            articles = []

            for item in raw_results:
                try:
                    # Try to create from dict
                    raw_article = TavilyRawArticle.model_validate(item)
                    articles.append(TavilyArticle.from_tavily_raw(raw_article))
                except Exception:
                    # Fallback: manual extraction
                    source = item.get("source")
                    if not source and item.get("url"):
                        try:
                            from urllib.parse import urlparse

                            parsed = urlparse(item.get("url", ""))
                            source = parsed.netloc.replace("www.", "")
                        except Exception:
                            source = "Unknown source"

                    content = item.get("content") or ""
                    snippet = content[:240] if content else None
                    if snippet and len(content) > 240:
                        snippet += "..."

                    articles.append(
                        TavilyArticle(
                            title=item.get("title", "Untitled"),
                            url=item.get("url", ""),
                            source=source or "Unknown source",
                            published_at=item.get("published_date") or item.get("published_at"),
                            snippet=snippet,
                            content=content if content else None,
                            score=item.get("score"),
                            image=item.get("image"),
                        )
                    )

            return cls(
                answer=api_response.get("answer", ""),
                articles=articles,
                query=api_response.get("query"),
                response_time=api_response.get("response_time"),
            )
