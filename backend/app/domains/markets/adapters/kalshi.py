from __future__ import annotations

from typing import Any

from app.domains.markets.adapters.base import MarketVenueAdapter, NormalizedMarketResult
from app.domains.markets.canonicalization import canonicalize_url, detect_venue
from app.domains.markets.parsing import parse_kalshi_url
from app.infrastructure.http.kalshi import get_event, get_market, get_markets, get_orderbook
from app.shared.exceptions import KalshiMarketNotFoundError


class KalshiAdapter(MarketVenueAdapter):
    venue = "kalshi"

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
        ticker, event_ticker, url_type = parse_kalshi_url(url)
        if selected_market_id:
            ticker = selected_market_id
            url_type = "market"

        if url_type == "market" and ticker:
            try:
                market = await get_market(ticker)
            except KalshiMarketNotFoundError:
                # Pretty Kalshi URLs sometimes embed the event ticker as the
                # last path segment (e.g. /markets/<series>/<event>/<EVENT-TICKER>).
                # Fall back to treating the parsed ticker as an event.
                fallback_event_ticker = ticker
                ticker = None
                url_type = "event"
                event_ticker = fallback_event_ticker
            else:
                event_id = str(
                    market.get("event_ticker") or event_ticker or ticker.rsplit("-", 1)[0]
                )
                event = await get_event(event_id)
                orderbook = await get_orderbook(ticker)
                return _build_market_result(
                    url=url,
                    market=market,
                    event=event,
                    event_id=event_id,
                    orderbook=orderbook,
                )

        if url_type == "event" and event_ticker:
            event = await get_event(event_ticker)
            markets = await get_markets(event_ticker=event_ticker)
            if selected_market_id:
                selected = _find_market(markets, selected_market_id)
                if selected:
                    orderbook = await get_orderbook(selected_market_id)
                    return _build_market_result(
                        url=url,
                        market=selected,
                        event=event,
                        event_id=event_ticker,
                        orderbook=orderbook,
                    )

            if len(markets) == 1:
                selected = markets[0]
                ticker = str(selected.get("ticker"))
                orderbook = await get_orderbook(ticker)
                return _build_market_result(
                    url=url,
                    market=selected,
                    event=event,
                    event_id=event_ticker,
                    orderbook=orderbook,
                )

            event_image = _event_image(event)
            return {
                "venue": self.venue,
                "raw_url": url,
                "canonical_url": canonicalize_url(url),
                "event_id": event_ticker,
                "requires_market_selection": True,
                "market_options": [
                    _normalize_option(market, event_image=event_image) for market in markets
                ],
                "event": _normalize_event(event),
                "event_context": _event_context(event, url),
                "raw": {"event": event, "markets": markets},
            }

        raise ValueError(f"Could not parse Kalshi market or event URL: {url}")


def kalshi_cents_to_probability(cents: int | float | None) -> float | None:
    if cents is None:
        return None
    return float(cents) / 100.0


def _kalshi_dollar_to_prob(value: Any) -> float | None:
    """Parse a Kalshi `*_dollars` field (decimal string in [0, 1]) into a float."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if 0.0 <= f <= 1.0 else None


def _kalshi_fp_number(value: Any) -> float | None:
    """Parse a Kalshi `*_fp` field (decimal string) into a float. Returns None if unparseable."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coalesce(*values: Any) -> Any:
    """Return the first non-None value, or None."""
    for v in values:
        if v is not None:
            return v
    return None


def _kalshi_level_price_to_prob(value: Any) -> float | None:
    """Normalize a Kalshi orderbook level price to a [0, 1] probability.

    Kalshi exposes orderbook prices in two shapes depending on the channel:
        - integer cents (1..99) under `yes` / `no`
        - dollar-decimal strings ("0.0900") under the same keys for some endpoints
    String values containing a decimal point are treated as dollars; everything
    else is treated as cents. Out-of-range or unparseable values return None.
    """
    if value is None:
        return None
    if isinstance(value, str):
        if "." in value:
            try:
                p = float(value)
            except ValueError:
                return None
            return p if 0.0 <= p <= 1.0 else None
        try:
            return int(value) / 100.0
        except ValueError:
            return None
    if isinstance(value, bool):  # bool is a subclass of int; reject explicitly
        return None
    if isinstance(value, int):
        return value / 100.0
    if isinstance(value, float):
        if 0.0 <= value <= 1.0:
            return value
        return value / 100.0
    return None


def normalize_kalshi_orderbook(raw: dict[str, Any]) -> dict[str, Any]:
    book = raw.get("orderbook") or raw.get("orderbook_fp") or {}
    yes_levels = book.get("yes") or book.get("yes_dollars") or []
    no_levels = book.get("no") or book.get("no_dollars") or []

    bids: list[dict[str, Any]] = []
    for level in yes_levels:
        if len(level) < 2:
            continue
        prob = _kalshi_level_price_to_prob(level[0])
        if prob is None:
            continue
        bids.append({"price": prob, "size": level[1]})

    asks: list[dict[str, Any]] = []
    for level in no_levels:
        if len(level) < 2:
            continue
        no_prob = _kalshi_level_price_to_prob(level[0])
        if no_prob is None:
            continue
        # NO bids at price p convert to YES asks at price (1 - p).
        asks.append({"price": 1.0 - no_prob, "size": level[1]})

    asks.sort(key=lambda level: level["price"])
    best_bid = bids[0]["price"] if bids else None
    best_ask = asks[0]["price"] if asks else None
    return {"bids": bids, "asks": asks, "best_bid": best_bid, "best_ask": best_ask}


def _build_market_result(
    url: str,
    market: dict[str, Any],
    event: dict[str, Any],
    event_id: str,
    orderbook: dict[str, Any],
) -> NormalizedMarketResult:
    market_id = str(market.get("ticker"))
    order_book = normalize_kalshi_orderbook(orderbook)
    market_snapshot = _market_snapshot(market, event, url, order_book)
    market_dict = {
        "ticker": market_id,
        "event_ticker": event_id,
        "question": market_snapshot["question"],
        "outcomes": ["Yes", "No"],
        "yes_index": 0,
    }
    return {
        "venue": "kalshi",
        "raw_url": url,
        "canonical_url": canonicalize_url(url),
        "market_id": market_id,
        "event_id": event_id,
        "selected_market_id": market_id,
        "requires_market_selection": False,
        "market_options": [],
        "market": market_dict,
        "event": _normalize_event(event),
        "market_snapshot": market_snapshot,
        "event_context": _event_context(event, url),
        "raw": {"event": event, "market": market, "orderbook": orderbook},
    }


def _market_snapshot(
    market: dict[str, Any],
    event: dict[str, Any],
    url: str,
    order_book: dict[str, Any],
) -> dict[str, Any]:
    # Kalshi's modern API returns prices as decimal-string `*_dollars` fields
    # (already in [0, 1] probability form). Older/alternate responses use
    # cents-int `yes_bid` / `yes_ask` / `last_price`. Read both, prefer dollars.
    yes_bid_prob = _coalesce(
        _kalshi_dollar_to_prob(market.get("yes_bid_dollars")),
        kalshi_cents_to_probability(market.get("yes_bid")),
    )
    yes_ask_prob = _coalesce(
        _kalshi_dollar_to_prob(market.get("yes_ask_dollars")),
        kalshi_cents_to_probability(market.get("yes_ask")),
    )
    last_price_prob = _coalesce(
        _kalshi_dollar_to_prob(market.get("last_price_dollars")),
        kalshi_cents_to_probability(market.get("last_price")),
    )
    yes_mid_prob = (
        (yes_bid_prob + yes_ask_prob) / 2.0
        if yes_bid_prob is not None and yes_ask_prob is not None
        else None
    )
    yes_price_actual = _coalesce(yes_mid_prob, last_price_prob)

    book_best_bid = order_book.get("best_bid")
    book_best_ask = order_book.get("best_ask")
    # If the market endpoint didn't populate bid/ask/last, derive a price from
    # the orderbook (some Kalshi markets only carry pricing on the book channel).
    if yes_price_actual is None:
        if book_best_bid is not None and book_best_ask is not None:
            yes_price_actual = (book_best_bid + book_best_ask) / 2.0
        elif book_best_bid is not None:
            yes_price_actual = book_best_bid
        elif book_best_ask is not None:
            yes_price_actual = book_best_ask
    # Last-resort: untraded with no orderbook either. 0.5 lets downstream agents
    # run without TypeErrors.
    yes_price = yes_price_actual if yes_price_actual is not None else 0.5
    no_price = round(1.0 - yes_price, 4)
    best_bid = _coalesce(book_best_bid, yes_bid_prob)
    best_ask = _coalesce(book_best_ask, yes_ask_prob)
    # Volume / OI / liquidity — Kalshi exposes these under `*_fp` (decimal strings).
    volume_total = _coalesce(
        _kalshi_fp_number(market.get("volume_fp")),
        _kalshi_fp_number(market.get("volume")),
    )
    volume_24h = _coalesce(
        _kalshi_fp_number(market.get("volume_24h_fp")),
        _kalshi_fp_number(market.get("volume_24h")),
    )
    open_interest = _coalesce(
        _kalshi_fp_number(market.get("open_interest_fp")),
        _kalshi_fp_number(market.get("open_interest")),
    )
    liquidity_dollars = _kalshi_fp_number(market.get("liquidity_dollars"))
    # Kalshi event responses use `title` for the shared event question and
    # `subtitle` / `yes_sub_title` for the per-market differentiator. Combine
    # them so the displayed market question is unique per row but still carries
    # the full resolution context for analysis.
    title = market.get("title") or market.get("question") or market.get("ticker")
    differentiator = (
        market.get("subtitle")
        or market.get("yes_sub_title")
        or market.get("no_sub_title")
    )
    if differentiator and title and differentiator.lower() not in (title or "").lower():
        question = f"{title} — {differentiator}"
    else:
        question = differentiator or title
    close_time = market.get("close_time") or market.get("expiration_time")
    return {
        "venue": "kalshi",
        "market_id": market.get("ticker"),
        "ticker": market.get("ticker"),
        "event_ticker": market.get("event_ticker") or event.get("event_ticker"),
        "url": url,
        "question": question,
        "title": question,
        "subtitle": market.get("subtitle") or market.get("yes_sub_title"),
        "group_item_title": differentiator,
        "groupItemTitle": differentiator,
        "status": market.get("status"),
        "outcomes": ["Yes", "No"],
        "yes_index": 0,
        "yes_price": yes_price,
        "no_price": no_price,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "last_trade_price": yes_price,
        "volume": float(volume_total) if volume_total is not None else 0.0,
        "volume24hr": volume_24h,
        "open_interest": open_interest,
        "liquidity": (
            float(liquidity_dollars)
            if liquidity_dollars is not None
            else (float(open_interest) if open_interest is not None else 0.0)
        ),
        "close_time": close_time,
        "end_date": close_time,
        "endDate": close_time,
        "order_book": order_book,
        "orderBook": order_book,
    }


def _normalize_option(
    market: dict[str, Any],
    event_image: str | None = None,
) -> dict[str, Any]:
    market_id = str(market.get("ticker"))
    yes_bid_prob = _coalesce(
        _kalshi_dollar_to_prob(market.get("yes_bid_dollars")),
        kalshi_cents_to_probability(market.get("yes_bid")),
    )
    yes_ask_prob = _coalesce(
        _kalshi_dollar_to_prob(market.get("yes_ask_dollars")),
        kalshi_cents_to_probability(market.get("yes_ask")),
    )
    last_price_prob = _coalesce(
        _kalshi_dollar_to_prob(market.get("last_price_dollars")),
        kalshi_cents_to_probability(market.get("last_price")),
    )
    yes_mid_prob = (
        (yes_bid_prob + yes_ask_prob) / 2.0
        if yes_bid_prob is not None and yes_ask_prob is not None
        else None
    )
    yes_price = _coalesce(yes_mid_prob, last_price_prob)
    # Kalshi event responses use `title` as the shared event question and
    # `subtitle` / `yes_sub_title` as the per-market differentiator. Prefer
    # the differentiator so the picker renders distinct labels.
    label = (
        market.get("subtitle")
        or market.get("yes_sub_title")
        or market.get("no_sub_title")
        or market.get("title")
        or market_id
    )
    return {
        "venue": "kalshi",
        "market_id": market_id,
        "label": label,
        "subtitle": market.get("subtitle") or market.get("yes_sub_title"),
        "image": event_image,
        "yes_price": yes_price,
        "best_bid": yes_bid_prob,
        "best_ask": yes_ask_prob,
        "volume": _coalesce(
            _kalshi_fp_number(market.get("volume_fp")),
            _kalshi_fp_number(market.get("volume")),
        ),
        "volume_24h": _coalesce(
            _kalshi_fp_number(market.get("volume_24h_fp")),
            _kalshi_fp_number(market.get("volume_24h")),
        ),
        "liquidity": _coalesce(
            _kalshi_fp_number(market.get("liquidity_dollars")),
            _kalshi_fp_number(market.get("open_interest_fp")),
            _kalshi_fp_number(market.get("open_interest")),
        ),
        "close_time": market.get("close_time"),
        "raw": market,
    }


def _event_image(event: dict[str, Any]) -> str | None:
    """Pull the best available event-level image from a Kalshi event payload.

    Kalshi's REST event/series endpoints don't expose images, but the website
    constructs URLs from the series ticker against a CloudFront CDN. We mirror
    that pattern here so picker cards and the snapshot can show the same
    series-level icon kalshi.com uses.
    """
    # Direct fields if Kalshi ever starts populating them.
    for key in ("image_url", "image", "icon", "series_image_url", "category_icon"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    series_ticker = event.get("series_ticker")
    if isinstance(series_ticker, str) and series_ticker:
        return (
            "https://d1lvyva3zy5u58.cloudfront.net/series-images-webp/"
            f"{series_ticker}.webp?size=sm"
        )
    return None


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    event_id = event.get("event_ticker") or event.get("ticker") or event.get("id")
    return {
        "event_ticker": event_id,
        "slug": event_id,
        "title": event.get("title"),
        "category": event.get("category"),
    }


def _event_context(event: dict[str, Any], url: str) -> dict[str, Any]:
    return {
        "title": event.get("title"),
        "category": event.get("category"),
        "image": _event_image(event),
        "url": url,
    }


def _mid_cents(bid_cents: int | None, ask_cents: int | None) -> int | None:
    if bid_cents is None or ask_cents is None:
        return None
    return (int(bid_cents) + int(ask_cents)) // 2


def _find_market(markets: list[dict[str, Any]], ticker: str) -> dict[str, Any] | None:
    return next((market for market in markets if market.get("ticker") == ticker), None)
