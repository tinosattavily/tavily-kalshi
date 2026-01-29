"""Market agent - extracts and normalizes market data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.state import AgentState
from app.core.logging_config import get_logger
from app.core.market_selector import find_market_by_slug, select_market_from_options
from app.core.market_transformer import build_market_options, build_market_snapshot
from app.core.polymarket_utils import extract_slug_from_url, get_event_and_markets_by_slug

logger = get_logger(__name__)


def _extract_image(record: dict[str, Any] | None) -> str | None:
    """Extract image URL from a market or event record."""
    if not record:
        return None
    return record.get("image") or record.get("icon")


def _get_comment_count(record: dict[str, Any]) -> int | None:
    """Extract comment count from a record, checking both naming conventions."""
    if "commentCount" in record and record["commentCount"] is not None:
        return record["commentCount"]
    if "comment_count" in record and record["comment_count"] is not None:
        return record["comment_count"]
    return None


def _populate_event_basics(state: AgentState, event: dict[str, Any] | None) -> None:
    """Populate basic event context fields from API event data."""
    if not event:
        return

    state["event"] = state.get("event", {})

    if "title" in event:
        state["event"]["title"] = event["title"]
    if "image" in event or "icon" in event:
        state["event"]["image"] = _extract_image(event)
    if "volume24hr" in event:
        state["event"]["volume24hr"] = event["volume24hr"]
    if "commentCount" in event:
        state["event"]["commentCount"] = event["commentCount"]


def _populate_event_metadata(state: AgentState, event: dict[str, Any] | None) -> None:
    """Store event metadata from API, including comment counts with logging."""
    if not event:
        return

    if "title" in event:
        state["event"]["title"] = event["title"]
    if "volume24hr" in event:
        state["event"]["volume24hr"] = event["volume24hr"]

    if "commentCount" in event:
        comment_count_value = event["commentCount"]
        state["event"]["commentCount"] = comment_count_value
        logger.debug(
            "Set commentCount in state from event",
            commentCount=comment_count_value,
            commentCount_type=type(comment_count_value).__name__,
        )

    if "seriesCommentCount" in event:
        series_comment_value = event["seriesCommentCount"]
        state["event"]["seriesCommentCount"] = series_comment_value
        logger.debug(
            "Set seriesCommentCount in state from event",
            seriesCommentCount=series_comment_value,
            seriesCommentCount_type=type(series_comment_value).__name__,
        )


def _clear_requires_market_selection(state: AgentState) -> None:
    """Clear the requires_market_selection flag from state."""
    state.pop("requires_market_selection", None)


def _resolve_event_image(
    selected_market_rec: dict[str, Any] | None,
    event: dict[str, Any] | None,
    markets: list[dict[str, Any]] | None,
    is_event: bool,
) -> str | None:
    """Determine the best image to use from available sources."""
    if selected_market_rec:
        return _extract_image(selected_market_rec)

    if event:
        image = _extract_image(event)
        if image:
            return image

    if is_event and markets:
        return _extract_image(markets[0])

    return None


def _get_question(
    selected_market_rec: dict[str, Any] | None,
    markets: list[dict[str, Any]] | None,
) -> str | None:
    """Extract question from API market data."""
    if selected_market_rec:
        return selected_market_rec.get("question") or selected_market_rec.get("title")
    if markets:
        return markets[0].get("question") or markets[0].get("title")
    return None


async def _fetch_order_book(selected_market_rec: dict[str, Any] | None) -> dict[str, Any]:
    """Fetch order book for a market if token ID is available."""
    if not selected_market_rec:
        return {}

    token_id = selected_market_rec.get("token_id") or selected_market_rec.get("tokenId")
    if not token_id:
        return {}

    try:
        from app.services.polymarket_client import get_polymarket_client

        client = get_polymarket_client()
        order_book = await client.fetch_order_book(token_id)
        logger.debug(
            "Fetched order book",
            token_id=token_id,
            has_bids=bool(order_book.get("bids")),
        )
        return order_book
    except Exception as e:
        logger.warning("Failed to fetch order book", token_id=token_id, error=str(e))
        return {}


async def run_market_agent(state: AgentState) -> AgentState:
    """Fill the canonical market definition and snapshot.

    This agent must run first as it sets up market_snapshot which other agents depend on.
    """
    market_url = state.get("market_url")
    logger.debug("Running market agent", market_url=market_url)
    slug = state.get("slug") or extract_slug_from_url(market_url) or "unknown-market"

    event, markets = await get_event_and_markets_by_slug(slug)

    is_event = bool(markets and len(markets) > 1)
    selected_market_slug = state.get("selected_market_slug")

    # Handle multi-market events
    if is_event:
        state["market_options"] = build_market_options(markets)

        chosen_market, chosen_slug, requires_selection = select_market_from_options(
            markets, selected_market_slug, slug
        )

        if requires_selection:
            state["requires_market_selection"] = True
            state["event"] = state.get("event", {})
            _populate_event_basics(state, event)
            return state

        _clear_requires_market_selection(state)
        state["requires_market_selection"] = False

        if chosen_slug and not selected_market_slug:
            selected_market_slug = chosen_slug
            state["selected_market_slug"] = chosen_slug
    else:
        _clear_requires_market_selection(state)

    # Resolve the selected market record
    selected_market_rec = None
    if selected_market_slug and markets:
        selected_market_rec = find_market_by_slug(markets, selected_market_slug)
    elif markets and len(markets) == 1:
        selected_market_rec = markets[0]
        selected_market_slug = selected_market_rec.get("slug") or str(
            selected_market_rec.get("id", "")
        )
        state["selected_market_slug"] = selected_market_slug

    # Store event data for event_agent
    state["event"] = state.get("event", {})

    event_image = _resolve_event_image(selected_market_rec, event, markets, is_event)
    if event_image:
        state["event"]["image"] = event_image
        logger.debug("Fetched image from Polymarket", image_url=event_image)

    _populate_event_metadata(state, event)

    # Fallback to market comment count if event doesn't have one
    if selected_market_rec and "commentCount" not in state.get("event", {}):
        market_comment_count = _get_comment_count(selected_market_rec)
        if market_comment_count is not None:
            state["event"]["commentCount"] = market_comment_count

    # Build market data
    # Use the selected market's slug for resolution tracking (not the event slug)
    market_slug = selected_market_slug or slug
    gamma_market_id = state.get("gamma_market_id") or f"gamma-{market_slug}"
    polymarket_url = state.get("polymarket_url") or market_url or "https://polymarket.com"
    timestamp = state.get("run_at") or datetime.now(timezone.utc).isoformat()

    existing_market = state.get("market", {})
    api_question = _get_question(selected_market_rec, markets)
    question = (
        existing_market.get("question")
        or api_question
        or f"Will {market_slug.replace('-', ' ')} resolve to Yes?"
    )
    outcomes = existing_market.get("outcomes") or ["Yes", "No"]
    yes_index = existing_market.get("yes_index", 0)

    if selected_market_rec:
        group_item_title = selected_market_rec.get("groupItemTitle")
    else:
        group_item_title = existing_market.get("group_item_title", "Placeholder contract")

    state["market"] = {
        "gamma_market_id": gamma_market_id,
        "slug": market_slug,
        "polymarket_url": polymarket_url,
        "question": question,
        "outcomes": outcomes,
        "yes_index": yes_index,
        "group_item_title": group_item_title,
        "created_at": existing_market.get("created_at", timestamp),
        "updated_at": timestamp,
    }

    order_book = await _fetch_order_book(selected_market_rec)

    market_snapshot = build_market_snapshot(
        {"question": question, "outcomes": outcomes, "yes_index": yes_index},
        polymarket_url,
        order_book,
        state,
        market_slug,
        api_market_record=selected_market_rec,
    )
    state["market_snapshot"] = market_snapshot
    state["polymarket_url"] = polymarket_url
    state["slug"] = market_slug

    return state
