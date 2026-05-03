# app/domains/news/summarizer.py
"""News summarization utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.config import get_logger
from app.infrastructure.llm import get_openai_client

logger = get_logger(__name__)


def generate_fallback_summary(
    event_title: str,
    answers: Optional[List[str]] = None,
    articles: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Generate a fallback summary when LLM is unavailable.

    Args:
        event_title: Event title for context
        answers: List of Tavily answer strings
        articles: List of article dicts

    Returns:
        Fallback summary string
    """
    answers = answers or []
    articles = articles or []

    if answers:
        return "\n\n".join(f"- {a}" for a in answers if a.strip())
    elif articles:
        title_list = "; ".join(
            a.get("title", "") for a in articles[:3] if a.get("title")
        )
        return f"Recent coverage on {event_title} highlights: {title_list}."
    else:
        return (
            f"Recent coverage on {event_title} highlights cautious sentiment with "
            "participants awaiting new data releases."
        )


async def summarize_news(
    articles: List[Dict[str, Any]],
    event_title: str,
    market_question: str,
    answers: Optional[List[str]] = None,
    min_articles_for_llm: int = 2,
) -> str:
    """Generate a comprehensive news summary using LLM with sentiment weighting.

    Args:
        articles: List of article dicts with sentiment
        event_title: Event title for context
        market_question: Market question for context
        answers: Optional list of Tavily answer strings
        min_articles_for_llm: Minimum articles required to use LLM

    Returns:
        Generated summary string
    """
    answers = answers or []

    # Check if we have enough articles
    if not articles or len(articles) < min_articles_for_llm:
        logger.debug(
            "Too few articles for LLM summary, using fallback",
            article_count=len(articles) if articles else 0,
        )
        return generate_fallback_summary(event_title, answers, articles)

    # Try LLM summarization
    try:
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

    except RuntimeError as e:
        # OpenAI not available or circuit breaker open
        logger.warning(
            "OpenAI not available for summary, using fallback heuristic",
            error=str(e),
        )
        return generate_fallback_summary(event_title, answers, articles)

    except Exception as exc:
        # Any other error
        logger.warning(
            "OpenAI summary generation failed, using fallback heuristic",
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        return generate_fallback_summary(event_title, answers, articles)


def generate_no_articles_summary(event_title: str) -> str:
    """Generate a summary when no articles are found.

    Args:
        event_title: Event title for context

    Returns:
        Summary string
    """
    return (
        f"No recent news articles found for {event_title}. "
        "This may indicate limited coverage or the event is too recent."
    )
