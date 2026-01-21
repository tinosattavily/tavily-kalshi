"""Orchestration agent wrappers."""

from app.orchestration.agents.article_fetcher import run_article_fetcher
from app.orchestration.agents.event import run_event_agent
from app.orchestration.agents.market import run_market_agent
from app.orchestration.agents.probability import run_probability_agent
from app.orchestration.agents.report import run_report_agent
from app.orchestration.agents.search_planner import run_search_planner
from app.orchestration.agents.strategy import run_strategy_agent
from app.orchestration.agents.summarizer import run_summarizer

__all__ = [
    "run_article_fetcher",
    "run_event_agent",
    "run_market_agent",
    "run_probability_agent",
    "run_report_agent",
    "run_search_planner",
    "run_strategy_agent",
    "run_summarizer",
]
