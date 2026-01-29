"""Event agent - normalizes event metadata."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.agents.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_DESCRIPTION = "Placeholder description for the macro event associated with this market."


def _derive_event_slug(market_slug: str | None) -> str:
    """Derive an event slug from a market slug by removing the last segment."""
    if not market_slug:
        return "unknown-event"
    parts = market_slug.split("-")
    if len(parts) <= 1:
        return market_slug
    return "-".join(parts[:-1]) or market_slug


def _get_default_end_date() -> str:
    """Generate a default end date 30 days from now in ISO format."""
    end = datetime.now(timezone.utc) + timedelta(days=30)
    return end.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_event_document(
    event: dict[str, Any],
    event_slug: str,
    title: str,
    description: str,
    category: str,
    image: str | None,
    end_date: str,
    timestamp: str,
) -> dict[str, Any]:
    """Build the normalized event document, preserving API-sourced metrics."""
    doc: dict[str, Any] = {
        "gamma_event_id": event.get("gamma_event_id") or f"evt-{event_slug}",
        "slug": event_slug,
        "title": title,
        "description": description,
        "category": category,
        "image": image,
        "end_date": end_date,
        "created_at": event.get("created_at", timestamp),
        "updated_at": timestamp,
    }

    # Preserve API-sourced metrics (set by market_agent) if present
    for key in ("commentCount", "seriesCommentCount", "volume24hr"):
        if event.get(key) is not None:
            doc[key] = event[key]

    return doc


async def run_event_agent(state: AgentState) -> AgentState:
    """Normalize event metadata and provide denormalized context.

    This agent can run in parallel with news_agent since it only processes
    data already available in state.
    """
    market_slug = state.get("slug")
    logger.debug("Running event agent", market_slug=market_slug)

    event = state.get("event") or {}
    event_slug = event.get("slug") or _derive_event_slug(market_slug)
    title = event.get("title") or f"{event_slug.replace('-', ' ').title()}?"
    description = event.get("description", DEFAULT_DESCRIPTION)
    category = event.get("category") or "Macro"
    image = event.get("image")
    end_date = event.get("end_date") or _get_default_end_date()
    timestamp = state.get("run_at") or datetime.now(timezone.utc).isoformat()

    # Build and store normalized event document
    state["event"] = _build_event_document(
        event=event,
        event_slug=event_slug,
        title=title,
        description=description,
        category=category,
        image=image,
        end_date=end_date,
        timestamp=timestamp,
    )
    state["event_description"] = description

    # Build event context for downstream agents
    url = state.get("polymarket_url") or state.get("market_url")
    state["event_context"] = {
        "title": title,
        "description": description,
        "category": category,
        "image": image,
        "volume24hr": state["event"].get("volume24hr"),
        "commentCount": state["event"].get("commentCount"),
        "seriesCommentCount": state["event"].get("seriesCommentCount"),
        "url": url,
    }

    logger.debug(
        "Event agent completed",
        event_slug=event_slug,
        has_comment_count=state["event"].get("commentCount") is not None,
        has_volume24hr=state["event"].get("volume24hr") is not None,
    )

    return state
