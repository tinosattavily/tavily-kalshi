"""News agent - aggregates news using Tavily API."""

from __future__ import annotations

from typing import Any

from app.agents.state import AgentState
from app.agents.tavily_prompt_agent import TavilyQuerySpec
from app.core.logging_config import get_logger
from app.core.sentiment_analyzer import analyze_articles_sentiment
from app.services.tavily_client import search_news

logger = get_logger(__name__)


def _normalize_tavily_queries(raw: Any) -> list[TavilyQuerySpec]:
    """Normalize tavily_queries to a list of TavilyQuerySpec.

    Handles both legacy format (list of strings) and new format (list of TavilyQuerySpec dicts).
    """
    if not raw:
        return []

    if not isinstance(raw, list):
        logger.warning("tavily_queries is not a list, ignoring", raw_type=type(raw).__name__)
        return []

    specs: list[TavilyQuerySpec] = []
    for item in raw:
        if isinstance(item, str):
            specs.append({
                "name": "legacy",
                "query": item,
                "max_results": 8,
                "search_depth": "basic",
            })
        elif isinstance(item, dict):
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
            if item.get("timeframe"):
                spec["timeframe"] = item["timeframe"]
            if item.get("notes"):
                spec["notes"] = item["notes"]
            specs.append(spec)
        else:
            logger.warning("Skipping invalid query item", item_type=type(item).__name__)

    return specs


def _get_event_title(state: AgentState) -> str:
    """Extract the event title from state, with fallback to market question."""
    event_ctx = state.get("event_context", {}) or {}
    event_data = state.get("event", {}) or {}
    market_snapshot = state.get("market_snapshot", {}) or {}

    return (
        event_ctx.get("title")
        or event_data.get("title")
        or market_snapshot.get("question")
        or "key event"
    )


def _build_fallback_query(state: AgentState) -> str:
    """Build a fallback query from event/market context."""
    base = _get_event_title(state).replace("?", "")
    return f"Latest news and developments relevant to: {base}"


def _summarize_news_brief(queries_block: list[dict[str, Any]]) -> str:
    """Generate a brief summary of collected news queries."""
    total_docs = sum(len(q.get("results", [])) for q in queries_block)
    names = ", ".join(q.get("name", "unnamed") for q in queries_block)
    return f"Collected {total_docs} news articles across queries: {names}."


async def run_news_agent(state: AgentState) -> AgentState:
    """Populate `news_context` using Tavily, with graceful fallback."""
    from app.services.tavily_client import TAVILY_API_KEY

    run_id = state.get("run_id")
    config = state.get("config", {}) or {}
    market_snapshot = state.get("market_snapshot", {}) or {}

    if not TAVILY_API_KEY:
        logger.error("TAVILY_API_KEY is not configured - news agent cannot fetch articles", run_id=run_id)
    else:
        logger.debug("Tavily API key is configured", run_id=run_id, key_length=len(TAVILY_API_KEY))

    raw_queries = state.get("tavily_queries")
    query_specs = _normalize_tavily_queries(raw_queries)

    using_llm_queries = (
        isinstance(raw_queries, list)
        and len(raw_queries) > 0
        and isinstance(raw_queries[0], dict)
        and "query" in raw_queries[0]
    )

    if not query_specs:
        fallback_query = _build_fallback_query(state)
        fallback_max_results = config.get("max_articles_per_query", 8)
        query_specs = [{
            "name": "fallback",
            "query": fallback_query,
            "max_results": fallback_max_results,
            "search_depth": "basic",
        }]
        using_llm_queries = False
        logger.debug("Using fallback query (tavily_queries not available or empty)", query=fallback_query)
    else:
        logger.debug(
            "Using normalized Tavily queries",
            query_count=len(query_specs),
            query_names=[q.get("name", "unnamed") for q in query_specs],
            using_llm_queries=using_llm_queries,
        )

    all_articles: list[dict[str, Any]] = []
    query_results: list[dict[str, Any]] = []
    default_max_per_query = config.get("max_articles_per_query", 8)

    for spec in query_specs:
        query = spec["query"]
        max_results = max(5, min(12, spec.get("max_results") or default_max_per_query))
        search_depth = spec.get("search_depth", "basic")

        if search_depth == "advanced":
            logger.debug("search_depth=advanced requested, but Tavily API may not support it yet", query=query)

        try:
            result = await search_news(query, max_results=max_results)
            answer = result.get("answer")
            articles = result.get("articles") or []

            if articles:
                logger.debug("Tavily search successful", query=query, articles_count=len(articles))
            else:
                logger.warning("Tavily search returned no articles", query=query, max_results=max_results, has_answer=bool(answer))

            all_articles.extend(articles)
            query_results.append({
                "name": spec.get("name", "unnamed"),
                "query": query,
                "results": articles,
                "answer": answer if isinstance(answer, str) else "",
            })
        except Exception as e:
            logger.error("Failed to search Tavily for query", query=query, error=str(e), error_type=type(e).__name__, exc_info=True)

    # Deduplicate articles by URL
    seen_urls: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for art in all_articles:
        url = art.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(art)

    # Analyze sentiment for articles if enabled
    enable_sentiment = config.get("enable_sentiment_analysis", True)
    if enable_sentiment:
        deduped_with_sentiment = analyze_articles_sentiment(
            articles=deduped,
            market_question=market_snapshot.get("question") or "",
            yes_price=float(market_snapshot.get("yes_price", 0.5)),
            signal_direction=state.get("signal", {}).get("direction"),
            outcomes=market_snapshot.get("outcomes") or ["Yes", "No"],
        )
        logger.debug(
            "Sentiment analysis completed",
            total_articles=len(deduped_with_sentiment),
            bullish_count=sum(1 for a in deduped_with_sentiment if a.get("sentiment") == "bullish"),
            bearish_count=sum(1 for a in deduped_with_sentiment if a.get("sentiment") == "bearish"),
            neutral_count=sum(1 for a in deduped_with_sentiment if a.get("sentiment") == "neutral"),
        )
    else:
        deduped_with_sentiment = deduped
        logger.debug("Sentiment analysis skipped (disabled in configuration)")

    query_strings = [spec["query"] for spec in query_specs]
    max_articles_config = config.get("max_articles", 15)
    articles_for_context = deduped_with_sentiment[:max_articles_config]
    combined_summary = _summarize_news_brief(query_results)

    if not articles_for_context:
        logger.warning(
            "News agent completed with no articles",
            query_count=len(query_specs),
            queries=query_strings,
            using_llm_queries=using_llm_queries,
        )
        if not combined_summary.strip():
            event_title = _get_event_title(state)
            combined_summary = f"No recent news articles found for {event_title}. This may indicate limited coverage or the event is too recent."

    state["news_context"] = {
        "tavily_queries": query_strings,
        "queries": query_results,
        "combined_summary": combined_summary,
        "articles": articles_for_context,
    }

    logger.info(
        "News agent completed",
        run_id=run_id,
        query_count=len(query_specs),
        articles_found=len(deduped_with_sentiment),
        articles_in_context=len(articles_for_context),
        using_llm_queries=using_llm_queries,
        has_summary=bool(combined_summary),
    )

    if articles_for_context:
        logger.debug(
            "News articles collected",
            run_id=run_id,
            article_titles=[a.get("title", "N/A")[:50] for a in articles_for_context[:3]],
            total_articles=len(articles_for_context),
        )
    else:
        logger.warning(
            "News agent completed with NO articles",
            run_id=run_id,
            query_count=len(query_specs),
            queries=[q.get("query", "N/A")[:50] for q in query_specs],
            all_articles_count=len(all_articles),
            deduped_count=len(deduped_with_sentiment),
        )

    return state
