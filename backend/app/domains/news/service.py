# app/domains/news/service.py
"""News service - orchestrates news fetching, sentiment analysis, and summarization."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.config import get_logger
from app.domains.news.fetcher import (
    deduplicate_articles,
    fetch_articles,
    normalize_tavily_queries,
    summarize_news_brief,
)
from app.domains.news.query_generator import (
    TavilyQuerySpec,
    build_fallback_query,
    generate_search_queries,
)
from app.domains.news.sentiment import analyze_articles_sentiment
from app.domains.news.summarizer import (
    generate_no_articles_summary,
    summarize_news,
)

logger = get_logger(__name__)


class NewsService:
    """Service class for news-related business logic.

    Orchestrates query generation, article fetching, sentiment analysis,
    and summarization.
    """

    def __init__(
        self,
        max_articles_per_query: int = 8,
        max_total_articles: int = 15,
        enable_sentiment_analysis: bool = True,
    ):
        """Initialize NewsService.

        Args:
            max_articles_per_query: Max articles per Tavily query
            max_total_articles: Max total articles to return
            enable_sentiment_analysis: Whether to perform sentiment analysis
        """
        self.max_articles_per_query = max_articles_per_query
        self.max_total_articles = max_total_articles
        self.enable_sentiment_analysis = enable_sentiment_analysis

    async def generate_queries(
        self,
        market_snapshot: Dict[str, Any],
        event_context: Dict[str, Any],
        event_data: Optional[Dict[str, Any]] = None,
        horizon: str = "24h",
        strategy_preset: str = "Balanced",
        slug: str = "unknown",
    ) -> List[TavilyQuerySpec]:
        """Generate search queries for news fetching.

        Args:
            market_snapshot: Market data dict
            event_context: Event context dict
            event_data: Event data dict
            horizon: Analysis horizon
            strategy_preset: Strategy preset
            slug: Market slug

        Returns:
            List of TavilyQuerySpec dicts
        """
        queries = await generate_search_queries(
            market_snapshot=market_snapshot,
            event_context=event_context,
            event_data=event_data,
            horizon=horizon,
            strategy_preset=strategy_preset,
            slug=slug,
        )

        # Fallback if no queries generated
        if not queries:
            event_title = (
                event_context.get("title")
                or (event_data or {}).get("title")
                or market_snapshot.get("question")
            )
            fallback_query = build_fallback_query(event_title, market_snapshot.get("question"))
            queries = [
                {
                    "name": "fallback",
                    "query": fallback_query,
                    "max_results": self.max_articles_per_query,
                    "search_depth": "basic",
                }
            ]
            logger.debug("Using fallback query", query=fallback_query)

        return queries

    async def fetch_news(
        self,
        query_specs: List[TavilyQuerySpec],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """Fetch news articles for given queries.

        Args:
            query_specs: List of TavilyQuerySpec dicts

        Returns:
            Tuple of (articles, query_results, answers)
        """
        all_articles, query_results, answers = await fetch_articles(
            query_specs, self.max_articles_per_query
        )

        # Deduplicate and limit
        deduped = deduplicate_articles(all_articles)
        limited = deduped[: self.max_total_articles]

        return limited, query_results, answers

    def analyze_sentiment(
        self,
        articles: List[Dict[str, Any]],
        market_question: str,
        yes_price: float,
        signal_direction: Optional[str] = None,
        outcomes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Analyze sentiment for articles.

        Args:
            articles: List of article dicts
            market_question: Market question
            yes_price: Current YES price
            signal_direction: Optional signal direction
            outcomes: Optional list of outcomes

        Returns:
            Articles with sentiment field added
        """
        if not self.enable_sentiment_analysis:
            logger.debug("Sentiment analysis disabled")
            return articles

        return analyze_articles_sentiment(
            articles=articles,
            market_question=market_question,
            yes_price=yes_price,
            signal_direction=signal_direction,
            outcomes=outcomes,
        )

    async def summarize(
        self,
        articles: List[Dict[str, Any]],
        event_title: str,
        market_question: str,
        answers: Optional[List[str]] = None,
    ) -> str:
        """Generate news summary.

        Args:
            articles: List of article dicts
            event_title: Event title
            market_question: Market question
            answers: Optional Tavily answers

        Returns:
            Summary string
        """
        return await summarize_news(
            articles=articles,
            event_title=event_title,
            market_question=market_question,
            answers=answers,
        )

    async def process_news(
        self,
        market_snapshot: Dict[str, Any],
        event_context: Dict[str, Any],
        event_data: Optional[Dict[str, Any]] = None,
        existing_queries: Optional[List[Any]] = None,
        horizon: str = "24h",
        strategy_preset: str = "Balanced",
        slug: str = "unknown",
        signal_direction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Full news processing pipeline.

        Orchestrates query generation, fetching, sentiment analysis, and summarization.

        Args:
            market_snapshot: Market data dict
            event_context: Event context dict
            event_data: Event data dict
            existing_queries: Pre-generated queries (optional)
            horizon: Analysis horizon
            strategy_preset: Strategy preset
            slug: Market slug
            signal_direction: Optional signal direction for sentiment

        Returns:
            News context dict with articles, summary, etc.
        """
        # Normalize existing queries or generate new ones
        if existing_queries:
            query_specs = normalize_tavily_queries(existing_queries)
        else:
            query_specs = []

        if not query_specs:
            query_specs = await self.generate_queries(
                market_snapshot=market_snapshot,
                event_context=event_context,
                event_data=event_data,
                horizon=horizon,
                strategy_preset=strategy_preset,
                slug=slug,
            )

        # Fetch articles
        articles, query_results, answers = await self.fetch_news(query_specs)

        # Analyze sentiment
        market_question = market_snapshot.get("question", "")
        yes_price = float(market_snapshot.get("yes_price", 0.5))
        outcomes = market_snapshot.get("outcomes") or ["Yes", "No"]

        articles_with_sentiment = self.analyze_sentiment(
            articles=articles,
            market_question=market_question,
            yes_price=yes_price,
            signal_direction=signal_direction,
            outcomes=outcomes,
        )

        # Log sentiment distribution
        if articles_with_sentiment:
            bullish = sum(1 for a in articles_with_sentiment if a.get("sentiment") == "bullish")
            bearish = sum(1 for a in articles_with_sentiment if a.get("sentiment") == "bearish")
            neutral = sum(1 for a in articles_with_sentiment if a.get("sentiment") == "neutral")
            logger.debug(
                "Sentiment analysis completed",
                total=len(articles_with_sentiment),
                bullish=bullish,
                bearish=bearish,
                neutral=neutral,
            )

        # Generate summary
        event_title = (
            event_context.get("title")
            or (event_data or {}).get("title")
            or market_question
            or "Key event"
        )

        if articles_with_sentiment:
            summary = await self.summarize(
                articles=articles_with_sentiment,
                event_title=event_title,
                market_question=market_question,
                answers=answers,
            )
        else:
            summary = generate_no_articles_summary(event_title)

        # Build combined summary
        combined_summary = summarize_news_brief(query_results)
        if not articles_with_sentiment:
            combined_summary = summary

        # Build news context
        query_strings = [spec["query"] for spec in query_specs]

        return {
            "tavily_queries": query_strings,
            "queries": query_results,
            "combined_summary": combined_summary,
            "articles": articles_with_sentiment,
            "summary": summary,
        }


# Module-level singleton
_news_service: Optional[NewsService] = None


def get_news_service(
    max_articles_per_query: int = 8,
    max_total_articles: int = 15,
    enable_sentiment_analysis: bool = True,
) -> NewsService:
    """Get the NewsService instance.

    Args:
        max_articles_per_query: Max articles per query
        max_total_articles: Max total articles
        enable_sentiment_analysis: Enable sentiment analysis

    Returns:
        NewsService instance
    """
    global _news_service
    if _news_service is None:
        _news_service = NewsService(
            max_articles_per_query=max_articles_per_query,
            max_total_articles=max_total_articles,
            enable_sentiment_analysis=enable_sentiment_analysis,
        )
    return _news_service
