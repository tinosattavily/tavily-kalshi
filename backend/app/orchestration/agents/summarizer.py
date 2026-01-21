"""Summarizer agent - generates news summary using LLM with fallback."""

from __future__ import annotations

from typing import List

from app.config import get_logger
from app.domains.news.summarizer import (
    generate_no_articles_summary,
    summarize_news,
)
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_summarizer(state: AgentState) -> AgentState:
    """Generate comprehensive news summary from collected articles."""
    event_ctx = state.get("event_context", {}) or {}
    market_snapshot = state.get("market_snapshot", {}) or {}
    event_data = state.get("event", {}) or {}
    news_context = state.get("news_context") or {}

    if news_context.get("summary"):
        logger.debug("Using existing summary from news context")
        return state

    event_title = (
        event_ctx.get("title")
        or event_data.get("title")
        or market_snapshot.get("question")
        or "Key event"
    )
    market_question = market_snapshot.get("question") or ""
    articles = news_context.get("articles", [])

    query_results = news_context.get("queries", [])
    answers: List[str] = []
    for query_result in query_results:
        answer = query_result.get("answer")
        if isinstance(answer, str) and answer.strip():
            answers.append(answer)

    if articles:
        summary = await summarize_news(
            articles=articles,
            event_title=event_title,
            market_question=market_question,
            answers=answers,
        )
    else:
        summary = generate_no_articles_summary(event_title)

    state.setdefault("news_context", {})
    state["news_context"]["summary"] = summary

    logger.info(
        "News summary agent completed",
        summary_length=len(summary),
        article_count=len(articles) if articles else 0,
    )

    return state
