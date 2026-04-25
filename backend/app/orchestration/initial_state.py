from __future__ import annotations

from app.api.schemas.requests import AnalyzeRequest
from app.domains.markets.canonicalization import detect_venue
from app.orchestration.state import AgentState


def build_initial_state(payload: AnalyzeRequest, *, run_id: str | None = None) -> AgentState:
    config = payload.configuration
    strategy_params = payload.strategy_params or {}
    if config and config.min_confidence:
        strategy_params = {**strategy_params, "min_confidence": config.min_confidence}

    market_url = str(payload.market_url)
    venue = detect_venue(market_url)
    selected_market_id = (
        payload.selected_market_id or payload.selected_market_slug or payload.selected_ticker
    )
    state: AgentState = {
        "market_url": market_url,
        "raw_url": market_url,
        "venue": venue,
        "selected_market_id": selected_market_id,
        "selected_market_slug": payload.selected_market_slug,
        "selected_ticker": payload.selected_ticker,
        "horizon": payload.horizon or "24h",
        "strategy_preset": payload.strategy_preset or "Balanced",
        "strategy_params": strategy_params,
        "config": {
            "use_tavily_prompt_agent": config.use_tavily_prompt_agent if config else True,
            "use_news_summary_agent": config.use_news_summary_agent if config else True,
            "max_articles": config.max_articles if config else 15,
            "max_articles_per_query": config.max_articles_per_query if config else 8,
            "min_confidence": config.min_confidence if config else "medium",
            "enable_sentiment_analysis": config.enable_sentiment_analysis if config else True,
        }
        if config
        else {},
    }
    if run_id:
        state["run_id"] = run_id
    if venue == "polymarket":
        state["polymarket_url"] = market_url
    elif venue == "kalshi":
        state["kalshi_url"] = market_url
    return state
