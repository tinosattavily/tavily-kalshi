"""Market agent - thin wrapper calling MarketService."""

from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_logger
from app.domains.markets import get_market_service
from app.infrastructure.http import fetch_order_book_async
from app.orchestration.state import AgentState

logger = get_logger(__name__)


async def run_market_agent(state: AgentState) -> AgentState:
    """Execute market agent: fetch and build market snapshot."""
    market_url = state.get("market_url")
    logger.debug("Running market agent", market_url=market_url)

    service = get_market_service()

    event, markets, slug = await service.fetch_market_data(
        market_url, state.get("slug")
    )
    is_event = service.is_event(markets)
    selected_market_slug = state.get("selected_market_slug")

    if is_event:
        state["market_options"] = service.build_options(markets)
        chosen_market, chosen_slug, requires_selection = service.select_market(
            markets, selected_market_slug, slug
        )
        if requires_selection:
            state["requires_market_selection"] = True
            state["event"] = service.update_event_metadata(
                state.get("event", {}), event, None
            )
            return state

        state["requires_market_selection"] = False
        if chosen_slug and not selected_market_slug:
            selected_market_slug = chosen_slug
            state["selected_market_slug"] = chosen_slug
    else:
        state.pop("requires_market_selection", None)

    selected_market_rec = None
    if selected_market_slug and markets:
        selected_market_rec = service.find_market(markets, selected_market_slug)
    elif markets and len(markets) == 1:
        selected_market_rec = markets[0]
        selected_market_slug = selected_market_rec.get("slug") or str(
            selected_market_rec.get("id", "")
        )
        state["selected_market_slug"] = selected_market_slug

    event_image = service.extract_event_image(
        event, markets, selected_market_rec, is_event
    )

    state["event"] = service.update_event_metadata(
        state.get("event", {}), event, event_image
    )
    state["event"] = service.extract_comment_count_from_market(
        selected_market_rec, state["event"]
    )

    gamma_market_id = state.get("gamma_market_id") or f"gamma-{slug}"
    polymarket_url = (
        state.get("polymarket_url") or market_url or "https://polymarket.com"
    )
    timestamp = state.get("run_at") or datetime.now(timezone.utc).isoformat()

    question = service.extract_question(
        selected_market_rec,
        markets,
        state.get("market", {}).get("question"),
        slug,
    )
    outcomes = state.get("market", {}).get("outcomes") or ["Yes", "No"]
    yes_index = state.get("market", {}).get("yes_index", 0)

    state["market"] = service.build_market_dict(
        slug=slug,
        question=question,
        selected_market=selected_market_rec,
        gamma_market_id=gamma_market_id,
        polymarket_url=polymarket_url,
        outcomes=outcomes,
        yes_index=yes_index,
        existing_market=state.get("market", {}),
    )
    state["market"]["created_at"] = state.get("market", {}).get(
        "created_at", timestamp
    )
    state["market"]["updated_at"] = timestamp

    order_book = {}
    if selected_market_rec:
        token_id = selected_market_rec.get("token_id") or selected_market_rec.get(
            "tokenId"
        )
        if token_id:
            try:
                order_book = await fetch_order_book_async(token_id)
                logger.debug(
                    "Fetched order book",
                    token_id=token_id,
                    has_bids=bool(order_book.get("bids")),
                )
            except Exception as exc:
                logger.warning(
                    "Failed to fetch order book", token_id=token_id, error=str(exc)
                )
                order_book = {}

    state["market_snapshot"] = service.build_snapshot(
        market=state["market"],
        market_url=polymarket_url,
        order_book=order_book,
        state=state,
        slug=slug,
        api_market_record=selected_market_rec,
    )

    state["polymarket_url"] = polymarket_url
    state["slug"] = slug

    return state
