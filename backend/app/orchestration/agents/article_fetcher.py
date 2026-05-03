"""Article fetcher agent - collects news via Tavily with fallback."""

from __future__ import annotations

from app.config import get_logger
from app.domains.news.fetcher import (
    deduplicate_articles,
    fetch_articles,
    normalize_tavily_queries,
    summarize_news_brief,
)
from app.domains.news.query_generator import build_fallback_query
from app.domains.news.sentiment import analyze_articles_sentiment
from app.infrastructure.http.tavily import TAVILY_API_KEY
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_article_fetcher(state: AgentState) -> AgentState:
    """Populate news_context using Tavily, with graceful fallback."""
    if not TAVILY_API_KEY:
        logger.error(
            "TAVILY_API_KEY is not configured - news agent cannot fetch articles",
            run_id=state.get("run_id"),
        )

    config = state.get("config", {}) or {}
    event_ctx = state.get("event_context", {}) or {}
    market_snapshot = state.get("market_snapshot", {}) or {}
    event_data = state.get("event", {}) or {}

    raw_queries = state.get("tavily_queries")
    query_specs = normalize_tavily_queries(raw_queries)
    using_llm_queries = (
        raw_queries
        and isinstance(raw_queries, list)
        and len(raw_queries) > 0
        and isinstance(raw_queries[0], dict)
        and "query" in raw_queries[0]
    )

    if not query_specs:
        event_title = (
            event_ctx.get("title")
            or event_data.get("title")
            or market_snapshot.get("question")
            or "key event"
        )
        fallback_query = build_fallback_query(event_title, market_snapshot.get("question"))
        fallback_max_results = config.get("max_articles_per_query", 8)
        query_specs = [
            {
                "name": "fallback",
                "query": fallback_query,
                "max_results": fallback_max_results,
                "search_depth": "basic",
            }
        ]
        using_llm_queries = False
        logger.debug(
            "Using fallback query (tavily_queries not available or empty)",
            query=fallback_query,
        )

    default_max_per_query = config.get("max_articles_per_query", 8)
    all_articles, query_results, answers = await fetch_articles(
        query_specs, default_max_per_query
    )

    deduped = deduplicate_articles(all_articles)
    max_articles = config.get("max_articles", 15)
    articles_for_context = deduped[:max_articles]

    market_question = market_snapshot.get("question") or ""
    yes_price_raw = market_snapshot.get("yes_price")
    yes_price = float(yes_price_raw) if yes_price_raw is not None else 0.5
    outcomes = market_snapshot.get("outcomes") or ["Yes", "No"]
    signal_direction = state.get("signal", {}).get("direction")

    enable_sentiment = config.get("enable_sentiment_analysis", True)
    if enable_sentiment:
        articles_for_context = analyze_articles_sentiment(
            articles=articles_for_context,
            market_question=market_question,
            yes_price=yes_price,
            signal_direction=signal_direction,
            outcomes=outcomes,
        )
    else:
        logger.debug("Sentiment analysis skipped (disabled in configuration)")

    combined_summary = summarize_news_brief(query_results)
    if not articles_for_context and not combined_summary.strip():
        event_title = (
            event_ctx.get("title")
            or event_data.get("title")
            or market_snapshot.get("question")
            or "this event"
        )
        combined_summary = (
            f"No recent news articles found for {event_title}. "
            "This may indicate limited coverage or the event is too recent."
        )

    query_strings = [spec["query"] for spec in query_specs]
    state["news_context"] = {
        "tavily_queries": query_strings,
        "queries": query_results,
        "combined_summary": combined_summary,
        "articles": articles_for_context,
    }

    logger.info(
        "News agent completed",
        run_id=state.get("run_id"),
        query_count=len(query_specs),
        articles_found=len(deduped),
        articles_in_context=len(articles_for_context),
        using_llm_queries=using_llm_queries,
        has_summary=bool(combined_summary),
        news_context_keys=list(state.get("news_context", {}).keys()),
    )

    if not articles_for_context:
        logger.warning(
            "News agent completed with NO articles",
            run_id=state.get("run_id"),
            query_count=len(query_specs),
            queries=[q.get("query", "N/A")[:50] for q in query_specs],
            all_articles_count=len(all_articles),
            deduped_count=len(deduped),
        )

    return state
