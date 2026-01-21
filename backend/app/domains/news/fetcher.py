# app/domains/news/fetcher.py
"""Article fetching and deduplication for news domain."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.config import get_logger
from app.domains.news.query_generator import TavilyQuerySpec
from app.infrastructure.http import search_news

logger = get_logger(__name__)


def normalize_tavily_queries(raw: Any) -> List[TavilyQuerySpec]:
    """Normalize tavily_queries to a list of TavilyQuerySpec.

    Handles both legacy format (list of strings) and new format (list of TavilyQuerySpec dicts).

    Args:
        raw: Raw query data (list of strings or dicts)

    Returns:
        List of normalized TavilyQuerySpec dicts
    """
    specs: List[TavilyQuerySpec] = []

    if not raw:
        return specs

    if not isinstance(raw, list):
        logger.warning("tavily_queries is not a list, ignoring", raw_type=type(raw).__name__)
        return specs

    for item in raw:
        if isinstance(item, str):
            # Legacy format: list of strings
            specs.append(
                {
                    "name": "legacy",
                    "query": item,
                    "max_results": 8,
                    "search_depth": "basic",
                }
            )
        elif isinstance(item, dict):
            # New format: TavilyQuerySpec dict
            query = item.get("query")
            if not query or not isinstance(query, str):
                logger.warning("Skipping invalid query spec (missing or invalid query)", item=item)
                continue

            spec: TavilyQuerySpec = {
                "name": item.get("name") or "news",
                "query": query,
                "max_results": int(item.get("max_results") or 8),
                "search_depth": item.get("search_depth") or "basic",
            }

            # Optional fields
            if item.get("timeframe"):
                spec["timeframe"] = item["timeframe"]
            if item.get("notes"):
                spec["notes"] = item["notes"]

            specs.append(spec)
        else:
            logger.warning("Skipping invalid query item", item_type=type(item).__name__)

    return specs


def deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate articles by URL.

    Args:
        articles: List of article dicts

    Returns:
        Deduplicated list of articles
    """
    deduped: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for art in articles:
        url = art.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(art)

    return deduped


async def fetch_articles(
    query_specs: List[TavilyQuerySpec],
    default_max_per_query: int = 8,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Fetch articles for given query specifications.

    Args:
        query_specs: List of TavilyQuerySpec dicts
        default_max_per_query: Default max results per query

    Returns:
        Tuple of (all_articles, query_results, answers)
    """
    all_articles: List[Dict[str, Any]] = []
    answers: List[str] = []
    query_results: List[Dict[str, Any]] = []

    for spec in query_specs:
        query = spec["query"]
        max_results = spec.get("max_results") or default_max_per_query
        max_results = max(5, min(12, max_results))
        search_depth = spec.get("search_depth", "basic")

        if search_depth == "advanced":
            logger.debug(
                "search_depth=advanced requested, but Tavily API may not support it yet",
                query=query,
            )

        try:
            result = await search_news(query, max_results=max_results, search_depth=search_depth)
            answer = result.get("answer")
            if isinstance(answer, str) and answer.strip():
                answers.append(answer)

            articles = result.get("articles") or []
            if not articles:
                logger.warning(
                    "Tavily search returned no articles",
                    query=query,
                    max_results=max_results,
                    has_answer=bool(answer),
                )
            else:
                logger.debug(
                    "Tavily search successful",
                    query=query,
                    articles_count=len(articles),
                )
            all_articles.extend(articles)
        except Exception as e:
            logger.error(
                "Failed to search Tavily for query",
                query=query,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            continue

        query_results.append(
            {
                "name": spec.get("name", "unnamed"),
                "query": query,
                "results": articles,
                "answer": answer if isinstance(answer, str) else "",
            }
        )

    return all_articles, query_results, answers


async def fetch_and_deduplicate_articles(
    query_specs: List[TavilyQuerySpec],
    default_max_per_query: int = 8,
    max_articles: int = 15,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Fetch and deduplicate articles.

    Args:
        query_specs: List of TavilyQuerySpec dicts
        default_max_per_query: Default max results per query
        max_articles: Maximum total articles to return

    Returns:
        Tuple of (deduplicated_articles, query_results, answers)
    """
    all_articles, query_results, answers = await fetch_articles(
        query_specs, default_max_per_query
    )

    # Deduplicate and limit
    deduped = deduplicate_articles(all_articles)
    limited = deduped[:max_articles]

    return limited, query_results, answers


def summarize_news_brief(queries_block: List[Dict[str, Any]]) -> str:
    """Generate a brief summary of collected news queries.

    Args:
        queries_block: List of query result dicts

    Returns:
        Brief summary string
    """
    total_docs = sum(len(q.get("results", [])) for q in queries_block)
    names = ", ".join(q.get("name", "unnamed") for q in queries_block)
    return f"Collected {total_docs} news articles across queries: {names}."
