"""News summary agent - generates comprehensive summaries using OpenAI with sentiment weighting."""

from __future__ import annotations

from typing import Any

from app.agents.state import AgentState
from app.core.logging_config import get_logger
from app.services.openai_client import get_openai_client

logger = get_logger(__name__)


def _get_event_title(state: AgentState) -> str:
    """Extract the event title from state, with fallback to market question."""
    event_ctx = state.get("event_context", {}) or {}
    event_data = state.get("event", {}) or {}
    market_snapshot = state.get("market_snapshot", {}) or {}

    return (
        event_ctx.get("title")
        or event_data.get("title")
        or market_snapshot.get("question")
        or "Key event"
    )


def _generate_fallback_summary(
    event_title: str,
    answers: list[str],
    articles: list[dict[str, Any]],
) -> str:
    """Generate a fallback summary when OpenAI is unavailable."""
    if answers:
        return "\n\n".join(f"- {a}" for a in answers if a.strip())

    if articles:
        title_list = "; ".join(
            a.get("title", "") for a in articles[:3] if a.get("title")
        )
        return f"Recent coverage on {event_title} highlights: {title_list}."

    return (
        f"Recent coverage on {event_title} highlights cautious sentiment with "
        "participants awaiting new data releases."
    )


def _extract_tavily_answers(news_context: dict[str, Any]) -> list[str]:
    """Extract non-empty answer strings from Tavily query results."""
    query_results = news_context.get("queries", [])
    return [
        query_result.get("answer")
        for query_result in query_results
        if isinstance(query_result.get("answer"), str) and query_result.get("answer").strip()
    ]


async def _generate_openai_summary(
    articles: list[dict[str, Any]],
    event_title: str,
    market_question: str,
    answers: list[str],
) -> str:
    """Generate summary using OpenAI, falling back to heuristic on failure."""
    openai_client = get_openai_client()
    logger.debug(
        "Attempting OpenAI summary generation",
        article_count=len(articles),
        event_title=event_title,
    )

    summary = await openai_client.summarize_news_with_sentiment(
        articles=articles,
        event_title=event_title,
        market_question=market_question,
    )

    logger.info(
        "OpenAI news summary generated successfully",
        article_count=len(articles),
        summary_length=len(summary),
        summary_preview=summary[:100] if summary else "empty",
    )
    return summary


async def run_news_summary_agent(state: AgentState) -> AgentState:
    """Generate comprehensive news summary using OpenAI with sentiment weighting.

    This agent depends on news_agent having already:
    - Collected articles via Tavily
    - Performed sentiment analysis on articles

    The summary is weighted towards the sentiment category with the most articles,
    but includes perspectives from all sentiment categories (bullish, bearish, neutral).
    """
    news_context = state.get("news_context") or {}
    market_snapshot = state.get("market_snapshot", {}) or {}

    event_title = _get_event_title(state)
    market_question = market_snapshot.get("question") or ""
    articles = news_context.get("articles", [])
    answers = _extract_tavily_answers(news_context)

    # Use existing summary if available (e.g., from cache or previous run)
    if news_context.get("summary"):
        summary = news_context["summary"]
        logger.debug("Using existing summary from news context")
    elif len(articles) >= 2:
        # Require at least 2 articles for meaningful sentiment-weighted summary
        try:
            summary = await _generate_openai_summary(
                articles=articles,
                event_title=event_title,
                market_question=market_question,
                answers=answers,
            )
        except RuntimeError as e:
            logger.warning(
                "OpenAI not available for summary, using fallback heuristic",
                error=str(e),
            )
            summary = _generate_fallback_summary(event_title, answers, articles)
        except Exception as exc:
            logger.warning(
                "OpenAI summary generation failed, using fallback heuristic",
                error=str(exc),
                error_type=type(exc).__name__,
                exc_info=True,
            )
            summary = _generate_fallback_summary(event_title, answers, articles)
    else:
        if articles:
            logger.debug("Too few articles for OpenAI summary, using fallback", article_count=len(articles))
        else:
            logger.debug("No articles available for summary generation")
        summary = _generate_fallback_summary(event_title, answers, articles)

    # Update news_context with the generated summary
    if "news_context" not in state:
        state["news_context"] = {}
    state["news_context"]["summary"] = summary

    logger.info(
        "News summary agent completed",
        summary_length=len(summary),
        article_count=len(articles),
    )

    return state
