# app/domains/markets/service.py
"""Market service - business logic for market operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.config import get_logger
from app.domains.markets.fetcher import get_event_and_markets_by_slug
from app.domains.markets.parsing import extract_slug_from_url
from app.domains.markets.selector import find_market_by_slug, select_market_from_options
from app.domains.markets.transformer import build_market_options, build_market_snapshot

logger = get_logger(__name__)


class MarketService:
    """Service class for market-related business logic.

    This class encapsulates the core market operations that can be used
    by agents, API endpoints, or other services.
    """

    async def fetch_market_data(
        self, market_url: Optional[str], slug: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], str]:
        """Fetch market data from Polymarket API.

        Args:
            market_url: URL of the market
            slug: Market slug (optional, derived from URL if not provided)

        Returns:
            Tuple of (event, markets, slug)
        """
        resolved_slug = slug or extract_slug_from_url(market_url) or "unknown-market"
        event, markets = await get_event_and_markets_by_slug(resolved_slug)
        return event, markets, resolved_slug

    def is_event(self, markets: List[Dict[str, Any]]) -> bool:
        """Check if this is an event with multiple markets."""
        return bool(markets and len(markets) > 1)

    def build_options(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build market options for UI selection."""
        return build_market_options(markets)

    def select_market(
        self,
        markets: List[Dict[str, Any]],
        selected_slug: Optional[str],
        url_slug: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], bool]:
        """Select a market from available options.

        Returns:
            Tuple of (chosen_market, chosen_slug, requires_selection)
        """
        return select_market_from_options(markets, selected_slug, url_slug)

    def find_market(
        self, markets: List[Dict[str, Any]], slug: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Find a market by slug."""
        return find_market_by_slug(markets, slug)

    def extract_event_image(
        self,
        event: Optional[Dict[str, Any]],
        markets: List[Dict[str, Any]],
        selected_market: Optional[Dict[str, Any]],
        is_event: bool,
    ) -> Optional[str]:
        """Extract image from event or market data.

        Args:
            event: Event dictionary from API
            markets: List of markets
            selected_market: Currently selected market
            is_event: Whether this is a multi-market event

        Returns:
            Image URL or None
        """
        event_image = None
        if event or markets:
            event_image = (
                (selected_market.get("image") or selected_market.get("icon"))
                if selected_market
                else (event.get("image") or event.get("icon") if event else None)
            )
            if not event_image and is_event and not selected_market and markets:
                first_market = markets[0]
                event_image = first_market.get("image") or first_market.get("icon")
        return event_image

    def extract_question(
        self,
        selected_market: Optional[Dict[str, Any]],
        markets: List[Dict[str, Any]],
        state_question: Optional[str],
        slug: str,
    ) -> str:
        """Extract question from market data.

        Args:
            selected_market: Currently selected market
            markets: List of markets
            state_question: Question from existing state
            slug: Market slug for fallback

        Returns:
            Market question string
        """
        api_question = None
        if selected_market:
            api_question = selected_market.get("question") or selected_market.get("title")
        elif markets and len(markets) > 0:
            api_question = markets[0].get("question") or markets[0].get("title")

        return (
            state_question
            or api_question
            or f"Will {slug.replace('-', ' ')} resolve to Yes?"
        )

    def build_market_dict(
        self,
        slug: str,
        question: str,
        selected_market: Optional[Dict[str, Any]],
        gamma_market_id: Optional[str] = None,
        polymarket_url: Optional[str] = None,
        outcomes: Optional[List[str]] = None,
        yes_index: int = 0,
        existing_market: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build market dictionary for state.

        Args:
            slug: Market slug
            question: Market question
            selected_market: Selected market from API
            gamma_market_id: Gamma market ID
            polymarket_url: Polymarket URL
            outcomes: List of outcomes
            yes_index: Index of YES outcome
            existing_market: Existing market dict from state

        Returns:
            Market dictionary
        """
        existing = existing_market or {}
        timestamp = datetime.now(timezone.utc).isoformat()
        group_item_title = (
            selected_market.get("groupItemTitle")
            if selected_market
            else existing.get("group_item_title", "Placeholder contract")
        )

        return {
            "gamma_market_id": gamma_market_id or f"gamma-{slug}",
            "slug": slug,
            "polymarket_url": polymarket_url or "https://polymarket.com",
            "question": question,
            "outcomes": outcomes or ["Yes", "No"],
            "yes_index": yes_index,
            "group_item_title": group_item_title,
            "created_at": existing.get("created_at", timestamp),
            "updated_at": timestamp,
        }

    def build_snapshot(
        self,
        market: Dict[str, Any],
        market_url: str,
        order_book: Dict[str, Any],
        state: Dict[str, Any],
        slug: str,
        api_market_record: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build market snapshot for frontend.

        Args:
            market: Market dictionary with question, outcomes, etc.
            market_url: The Polymarket URL for this market
            order_book: Order book data (bids/asks)
            state: Current state for fallback values
            slug: Market slug
            api_market_record: Raw market record from API

        Returns:
            Market snapshot dictionary
        """
        return build_market_snapshot(
            market, market_url, order_book, state, slug, api_market_record
        )

    def update_event_metadata(
        self,
        event_state: Dict[str, Any],
        event: Optional[Dict[str, Any]],
        event_image: Optional[str],
    ) -> Dict[str, Any]:
        """Update event state with metadata from API.

        Args:
            event_state: Existing event state
            event: Event data from API
            event_image: Event image URL

        Returns:
            Updated event state
        """
        if event_image:
            event_state["image"] = event_image
            logger.debug("Fetched image from Polymarket", image_url=event_image)

        if event:
            if "title" in event:
                event_state["title"] = event["title"]
            if "volume24hr" in event:
                event_state["volume24hr"] = event["volume24hr"]
            if "commentCount" in event:
                comment_count_value = event["commentCount"]
                event_state["commentCount"] = comment_count_value
                logger.debug(
                    "Set commentCount in state from event",
                    commentCount=comment_count_value,
                    commentCount_type=type(comment_count_value).__name__,
                )
            if "seriesCommentCount" in event:
                series_comment_value = event["seriesCommentCount"]
                event_state["seriesCommentCount"] = series_comment_value
                logger.debug(
                    "Set seriesCommentCount in state from event",
                    seriesCommentCount=series_comment_value,
                )

        return event_state

    def extract_comment_count_from_market(
        self,
        market: Optional[Dict[str, Any]],
        event_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract comment count from market if not in event state.

        Args:
            market: Market dictionary
            event_state: Event state dictionary

        Returns:
            Updated event state
        """
        if market and "commentCount" not in event_state:
            market_comment_count = None
            if "commentCount" in market and market["commentCount"] is not None:
                market_comment_count = market["commentCount"]
            elif "comment_count" in market and market["comment_count"] is not None:
                market_comment_count = market["comment_count"]

            if market_comment_count is not None:
                event_state["commentCount"] = market_comment_count

        return event_state


# Module-level singleton
_market_service: Optional[MarketService] = None


def get_market_service() -> MarketService:
    """Get the singleton MarketService instance."""
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service
