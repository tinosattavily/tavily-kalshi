# app/domains/markets/parsing.py
"""URL and price parsing utilities for Polymarket and Kalshi."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from app.domains.markets.canonicalization import _host_matches


def extract_slug_from_url(url: str | None) -> Optional[str]:
    """Extract market/event slug from Polymarket URL."""
    if not url:
        return None
    try:
        # Basic validation: URL should contain "://" or "/" to be considered a URL
        if "://" not in url and "/" not in url and not url.startswith("http"):
            return None
        url_no_scheme = re.sub(r"^https?://", "", url)
        url_no_qf = re.split(r"[?#]", url_no_scheme)[0]
        path = url_no_qf.split("/", 1)[-1]
        parts = [p for p in path.split("/") if p]
        if not parts:
            return None
        return parts[-1]
    except Exception:
        return None


def parse_prices_from_market(market: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """Parse YES/NO prices from market data."""
    yes_price = market.get("yes_price")
    no_price = market.get("no_price")
    if isinstance(yes_price, (int, float)) and isinstance(no_price, (int, float)):
        return float(yes_price), float(no_price)

    outcome_prices = market.get("outcomePrices")
    if outcome_prices:
        # Handle list format directly
        if isinstance(outcome_prices, list) and len(outcome_prices) >= 2:
            try:
                yes = float(outcome_prices[0])
                no = float(outcome_prices[1])
                return yes, no
            except (ValueError, TypeError):
                pass
        # Handle JSON string format
        elif isinstance(outcome_prices, str) and outcome_prices.startswith("["):
            try:
                arr = json.loads(outcome_prices)
                if isinstance(arr, list) and len(arr) >= 2:
                    yes = float(arr[0])
                    no = float(arr[1])
                    return yes, no
            except Exception:
                pass

    return None, None


def normalize_number(v: Any) -> Optional[float]:
    """Normalize a value to float."""
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        return float(str(v))
    except Exception:
        return None


def parse_end_date(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO date string to datetime."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except Exception:
        return None


# Kalshi URL patterns. Pretty URLs are lowercased, but the API requires uppercase tickers,
# so we match case-insensitively and uppercase the result.
KALSHI_DOMAINS = ["kalshi.com", "kalshi.co"]
KALSHI_TICKER_SEGMENT_PATTERN = re.compile(
    r"^(?=.*\d)[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$",
    re.IGNORECASE,
)


def is_kalshi_url(url: str) -> bool:
    """Check if URL is a Kalshi market or event URL."""
    try:
        parsed = urlparse(url)
        return _host_matches(parsed.netloc.lower(), tuple(KALSHI_DOMAINS))
    except Exception:
        return False


def extract_kalshi_ticker_from_url(url: str) -> Optional[str]:
    """Extract market ticker from Kalshi URL.

    Examples:
        https://kalshi.com/markets/INXD-25JAN17-B24999 -> INXD-25JAN17-B24999
        https://kalshi.com/markets/kxmlbmention/mlb-announcers/kxmlbmention-26apr24chclad
            -> KXMLBMENTION-26APR24CHCLAD
    """
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if "markets" not in parts:
        return None
    for part in reversed(parts):
        if KALSHI_TICKER_SEGMENT_PATTERN.match(part):
            return part.upper()
    return None


def extract_kalshi_event_ticker_from_url(url: str) -> Optional[str]:
    """Extract event ticker from Kalshi URL.

    Examples:
        https://kalshi.com/events/INXD-25JAN17 -> INXD-25JAN17
    """
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if "events" not in parts:
        return None
    for part in reversed(parts):
        if KALSHI_TICKER_SEGMENT_PATTERN.match(part):
            return part.upper()
    return None


def parse_kalshi_url(url: str) -> Tuple[Optional[str], Optional[str], str]:
    """Parse Kalshi URL to extract ticker and type.

    Returns:
        Tuple of (ticker, event_ticker, url_type)
        url_type is "market", "event", or "unknown"
    """
    ticker = extract_kalshi_ticker_from_url(url)
    if ticker:
        explicit_event_ticker = extract_kalshi_event_ticker_from_url(url)
        event_ticker = explicit_event_ticker or ticker.rsplit("-", 1)[0]
        return ticker, event_ticker, "market"

    event_ticker = extract_kalshi_event_ticker_from_url(url)
    if event_ticker:
        return None, event_ticker, "event"

    return None, None, "unknown"
