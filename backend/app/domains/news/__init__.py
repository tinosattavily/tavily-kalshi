# app/domains/news/__init__.py
"""News domain exports."""

from app.domains.news.fetcher import (
    deduplicate_articles,
    fetch_and_deduplicate_articles,
    fetch_articles,
    normalize_tavily_queries,
    summarize_news_brief,
)
from app.domains.news.query_generator import (
    TavilyQuerySpec,
    build_fallback_queries,
    build_fallback_query,
    generate_search_queries,
    parse_tavily_specs,
)
from app.domains.news.schemas import (
    TavilyArticle,
    TavilyRawArticle,
    TavilySearchResponse,
    TavilySearchResult,
)
from app.domains.news.sentiment import (
    BEARISH_PATTERNS,
    BULLISH_PATTERNS,
    NEGATION_WORDS,
    Sentiment,
    analyze_article_sentiment,
    analyze_articles_sentiment,
)
from app.domains.news.service import NewsService, get_news_service
from app.domains.news.summarizer import (
    generate_fallback_summary,
    generate_no_articles_summary,
    summarize_news,
)

__all__ = [
    # Schemas
    "TavilyArticle",
    "TavilyRawArticle",
    "TavilySearchResponse",
    "TavilySearchResult",
    # Query Generator
    "TavilyQuerySpec",
    "build_fallback_queries",
    "build_fallback_query",
    "generate_search_queries",
    "parse_tavily_specs",
    # Fetcher
    "deduplicate_articles",
    "fetch_and_deduplicate_articles",
    "fetch_articles",
    "normalize_tavily_queries",
    "summarize_news_brief",
    # Sentiment
    "BEARISH_PATTERNS",
    "BULLISH_PATTERNS",
    "NEGATION_WORDS",
    "Sentiment",
    "analyze_article_sentiment",
    "analyze_articles_sentiment",
    # Summarizer
    "generate_fallback_summary",
    "generate_no_articles_summary",
    "summarize_news",
    # Service
    "NewsService",
    "get_news_service",
]
