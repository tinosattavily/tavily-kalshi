from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import Any

from app.config import get_logger
from app.domains.markets.adapters.base import MarketVenueAdapter, NormalizedMarketResult
from app.domains.markets.canonicalization import canonicalize_url, detect_venue
from app.domains.markets.fetcher import fetch_order_book_async
from app.domains.markets.service import get_market_service

logger = get_logger(__name__)


class PolymarketAdapter(MarketVenueAdapter):
    venue = "polymarket"

    def matches(self, url: str) -> bool:
        try:
            return detect_venue(url) == self.venue
        except ValueError:
            return False

    async def fetch(
        self,
        url: str,
        selected_market_id: str | None = None,
    ) -> NormalizedMarketResult:
        service = get_market_service()
        event, markets, slug = await service.fetch_market_data(url, selected_market_id)
        is_event = service.is_event(markets)
        selected_slug = selected_market_id

        event_state: dict[str, Any] = {}

        if is_event:
            options = _normalize_options(service.build_options(markets))
            chosen_market, chosen_slug, requires_selection = service.select_market(
                markets, selected_slug, slug
            )
            if requires_selection:
                event_state = service.update_event_metadata(event_state, event, None)
                return {
                    "venue": self.venue,
                    "raw_url": url,
                    "canonical_url": canonicalize_url(url),
                    "event_id": _event_id(event, slug),
                    "requires_market_selection": True,
                    "market_options": options,
                    "event": event_state,
                    "event_context": {**event_state, "url": url},
                    "raw": {"event": event, "markets": markets},
                }

            selected_market_rec = chosen_market
            if chosen_slug and not selected_slug:
                selected_slug = chosen_slug
        else:
            selected_market_rec = None
            if selected_slug and markets:
                selected_market_rec = _find_market(service, markets, selected_slug)
            elif markets and len(markets) == 1:
                selected_market_rec = markets[0]
                selected_slug = selected_market_rec.get("slug") or str(
                    selected_market_rec.get("id", "")
                )

        selected_slug = selected_slug or slug
        selected_market_rec = selected_market_rec if "selected_market_rec" in locals() else None

        event_image = service.extract_event_image(event, markets, selected_market_rec, is_event)
        event_state = service.update_event_metadata(event_state, event, event_image)
        event_state = service.extract_comment_count_from_market(selected_market_rec, event_state)

        gamma_market_id = (
            selected_market_rec.get("id")
            if selected_market_rec
            else None
        ) or f"gamma-{selected_slug}"
        timestamp = datetime.now(timezone.utc).isoformat()
        question = service.extract_question(
            selected_market_rec,
            markets,
            None,
            selected_slug,
        )
        outcomes = ["Yes", "No"]
        yes_index = 0

        market = service.build_market_dict(
            slug=selected_slug,
            question=question,
            selected_market=selected_market_rec,
            gamma_market_id=gamma_market_id,
            polymarket_url=url,
            outcomes=outcomes,
            yes_index=yes_index,
            existing_market={},
        )
        market["created_at"] = market.get("created_at", timestamp)
        market["updated_at"] = timestamp

        order_book = {}
        if selected_market_rec:
            token_id = selected_market_rec.get("token_id") or selected_market_rec.get("tokenId")
            if token_id:
                try:
                    maybe_order_book = fetch_order_book_async(token_id)
                    order_book = (
                        await maybe_order_book
                        if inspect.isawaitable(maybe_order_book)
                        else maybe_order_book
                    )
                except Exception as exc:
                    logger.warning("Failed to fetch order book", token_id=token_id, error=str(exc))
                    order_book = {}

        state = {"event": event_state, "market": market, "market_snapshot": {}}
        market_snapshot = service.build_snapshot(
            market=market,
            market_url=url,
            order_book=order_book,
            state=state,
            slug=selected_slug,
            api_market_record=selected_market_rec,
        )
        market_snapshot["venue"] = self.venue
        market_snapshot["market_id"] = selected_slug

        return {
            "venue": self.venue,
            "raw_url": url,
            "canonical_url": canonicalize_url(url),
            "market_id": selected_slug,
            "event_id": _event_id(event, selected_slug),
            "selected_market_id": selected_slug,
            "requires_market_selection": False,
            "market_options": [],
            "market": market,
            "event": event_state,
            "market_snapshot": market_snapshot,
            "event_context": {**event_state, "url": url},
            "raw": {"event": event, "markets": markets},
        }


def _normalize_options(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for option in options:
        market_id = option.get("slug") or str(option.get("id") or "")
        normalized.append(
            {
                "venue": "polymarket",
                "market_id": market_id,
                "label": option.get("question") or option.get("title") or market_id,
                "best_bid": option.get("best_bid") or option.get("bestBid"),
                "best_ask": option.get("best_ask") or option.get("bestAsk"),
                "liquidity": option.get("liquidity"),
                "raw": option,
            }
        )
    return normalized


def _find_market(service: Any, markets: list[dict[str, Any]], selected_slug: str):
    if hasattr(service, "find_market"):
        return service.find_market(markets, selected_slug)
    return next(
        (
            market
            for market in markets
            if (market.get("slug") or "") == selected_slug or str(market.get("id")) == selected_slug
        ),
        None,
    )


def _event_id(event: dict[str, Any] | None, fallback: str) -> str:
    if event:
        return str(event.get("slug") or event.get("id") or fallback)
    return fallback
