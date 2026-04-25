from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.domains.markets.adapters.base import Venue

TRACKING_PREFIXES = ("utm_",)
TRACKING_KEYS = {"fbclid", "gclid", "msclkid"}
KALSHI_HOST_MARKERS = ("kalshi.com", "kalshi.co")
POLYMARKET_HOST_MARKERS = ("polymarket.com",)


def _host_matches(host: str, markers: tuple[str, ...]) -> bool:
    return any(host == marker or host.endswith("." + marker) for marker in markers)


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    kept_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in TRACKING_KEYS and not key.startswith(TRACKING_PREFIXES)
    ]
    query = urlencode(kept_query, doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))


def detect_venue(url: str) -> Venue:
    host = urlparse(url.strip()).netloc.lower()
    if _host_matches(host, KALSHI_HOST_MARKERS):
        return "kalshi"
    if _host_matches(host, POLYMARKET_HOST_MARKERS):
        return "polymarket"
    raise ValueError("Unsupported URL host. Paste a Kalshi or Polymarket URL.")
