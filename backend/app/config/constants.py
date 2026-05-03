# app/config/constants.py
"""API endpoints and application constants."""


class KalshiAPI:
    """Kalshi API endpoint constants."""

    PUBLIC_BASE = "https://api.elections.kalshi.com/trade-api/v2"
    DEMO_AUTH_BASE = "https://demo-api.kalshi.co/trade-api/v2"
    PROD_AUTH_BASE = "https://trading-api.kalshi.com/trade-api/v2"

    # Backward-compatible names used by older health/config callers.
    DEMO_BASE = DEMO_AUTH_BASE
    PROD_BASE = PROD_AUTH_BASE
