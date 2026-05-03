# app/domains/markets/event_service.py
"""Event service - business logic for event operations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.config import get_logger
from app.domains.markets.parsing import parse_kalshi_url
from app.domains.markets.kalshi_fetcher import get_kalshi_event_by_ticker
from app.domains.markets.kalshi_transformer import build_kalshi_event_context

logger = get_logger(__name__)


def _derive_event_slug(market_slug: str | None) -> str:
    """Derive event slug from market slug.

    Args:
        market_slug: Market slug string

    Returns:
        Derived event slug
    """
    if not market_slug:
        return "unknown-event"
    parts = market_slug.split("-")
    if len(parts) <= 1:
        return market_slug
    return "-".join(parts[:-1]) or market_slug


class EventService:
    """Service class for event-related business logic.

    This class encapsulates the core event operations that can be used
    by agents, API endpoints, or other services.
    """

    def derive_event_slug(self, market_slug: Optional[str]) -> str:
        """Derive event slug from market slug."""
        return _derive_event_slug(market_slug)

    def build_event_dict(
        self,
        event: Dict[str, Any],
        market_slug: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build normalized event dictionary.

        Args:
            event: Existing event data
            market_slug: Market slug for deriving event slug
            timestamp: Timestamp for created_at/updated_at

        Returns:
            Normalized event dictionary
        """
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        event_slug = event.get("slug") or self.derive_event_slug(market_slug)
        gamma_event_id = event.get("gamma_event_id") or f"evt-{event_slug}"
        title = event.get("title") or f"{event_slug.replace('-', ' ').title()}?"
        description = event.get(
            "description",
            "Placeholder description for the macro event associated with this market.",
        )
        category = event.get("category") or "Macro"
        image = event.get("image") or None
        end_date = event.get("end_date") or (
            datetime.now(timezone.utc) + timedelta(days=30)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        result = {
            "gamma_event_id": gamma_event_id,
            "slug": event_slug,
            "title": title,
            "description": description,
            "category": category,
            "image": image,
            "end_date": end_date,
            "created_at": event.get("created_at", ts),
            "updated_at": ts,
        }

        # Preserve API-provided fields if present
        if "commentCount" in event and event["commentCount"] is not None:
            result["commentCount"] = event["commentCount"]
        if "seriesCommentCount" in event and event["seriesCommentCount"] is not None:
            result["seriesCommentCount"] = event["seriesCommentCount"]
        if "volume24hr" in event and event["volume24hr"] is not None:
            result["volume24hr"] = event["volume24hr"]

        return result

    def build_event_context(
        self,
        event: Dict[str, Any],
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build event context for denormalized access.

        Args:
            event: Event dictionary
            url: Polymarket URL

        Returns:
            Event context dictionary
        """
        # Get commentCount, allowing 0 values (explicitly check for None)
        comment_count = event.get("commentCount") if "commentCount" in event else None
        series_comment_count = (
            event.get("seriesCommentCount") if "seriesCommentCount" in event else None
        )

        logger.debug(
            "Event service - building event context",
            commentCount=comment_count,
            seriesCommentCount=series_comment_count,
        )

        return {
            "title": event.get("title"),
            "description": event.get("description"),
            "category": event.get("category"),
            "image": event.get("image"),
            "volume24hr": event.get("volume24hr"),
            "commentCount": comment_count,
            "seriesCommentCount": series_comment_count,
            "url": url,
        }

    def normalize_event(
        self,
        event: Dict[str, Any],
        market_slug: Optional[str] = None,
        url: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> tuple[Dict[str, Any], Dict[str, Any], str]:
        """Normalize event and build context in one call.

        Args:
            event: Existing event data
            market_slug: Market slug
            url: Polymarket URL
            timestamp: Timestamp for created_at/updated_at

        Returns:
            Tuple of (normalized_event, event_context, event_description)
        """
        normalized = self.build_event_dict(event, market_slug, timestamp)
        context = self.build_event_context(normalized, url)
        description = normalized.get(
            "description",
            "Placeholder description for the macro event associated with this market.",
        )
        return normalized, context, description

    # -------------------------------------------------------------------------
    # Kalshi Methods
    # -------------------------------------------------------------------------

    async def get_kalshi_event_context(self, event_ticker: str) -> Dict[str, Any]:
        """Fetch Kalshi event and return context with all markets.

        Args:
            event_ticker: Kalshi event ticker

        Returns:
            Event context dictionary with market list
        """
        event = await get_kalshi_event_by_ticker(event_ticker)
        return build_kalshi_event_context(event)

    async def get_kalshi_event_context_from_url(self, url: str) -> Dict[str, Any]:
        """Get Kalshi event context from a URL.

        Args:
            url: Kalshi market or event URL

        Returns:
            Event context dictionary

        Raises:
            ValueError: If event ticker cannot be determined
        """
        ticker, event_ticker, url_type = parse_kalshi_url(url)

        # If market URL, extract event ticker from it
        if url_type == "market" and ticker:
            # Event ticker was extracted from market ticker
            pass
        elif url_type == "event":
            # Event ticker directly from URL
            pass
        else:
            raise ValueError(f"Could not determine event ticker from URL: {url}")

        if not event_ticker:
            raise ValueError(f"Could not determine event ticker from URL: {url}")

        return await self.get_kalshi_event_context(event_ticker)

    def requires_kalshi_market_selection(self, context: Dict[str, Any]) -> bool:
        """Check if Kalshi event has multiple markets requiring selection.

        Args:
            context: Event context dictionary

        Returns:
            True if selection is required
        """
        return context.get("requires_selection", False)

    def get_kalshi_market_options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of Kalshi markets for selection UI.

        Args:
            context: Event context dictionary

        Returns:
            List of market option dictionaries
        """
        return context.get("markets", [])


# Module-level singleton
_event_service: Optional[EventService] = None


def get_event_service() -> EventService:
    """Get the singleton EventService instance."""
    global _event_service
    if _event_service is None:
        _event_service = EventService()
    return _event_service
