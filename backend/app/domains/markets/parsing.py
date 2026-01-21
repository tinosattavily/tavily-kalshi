# app/domains/markets/parsing.py
"""URL and price parsing utilities for Polymarket."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


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
