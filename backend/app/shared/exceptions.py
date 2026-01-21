# app/shared/exceptions.py
"""Custom exceptions for the application."""


class ProphilyError(Exception):
    """Base exception for all application errors."""

    pass


class ConfigurationError(ProphilyError):
    """Raised when configuration is invalid or missing."""

    pass


class ExternalAPIError(ProphilyError):
    """Raised when an external API call fails."""

    pass


class PolymarketAPIError(ExternalAPIError):
    """Raised when Polymarket API call fails."""

    pass


class TavilyAPIError(ExternalAPIError):
    """Raised when Tavily API call fails."""

    pass


class OpenAIAPIError(ExternalAPIError):
    """Raised when OpenAI API call fails."""

    pass


class DatabaseError(ProphilyError):
    """Raised when database operation fails."""

    pass


class ValidationError(ProphilyError):
    """Raised when data validation fails."""

    pass


class MarketSelectionRequiredError(ProphilyError):
    """Raised when user must select a market from multiple options."""

    def __init__(self, market_options: list, event_context: dict):
        self.market_options = market_options
        self.event_context = event_context
        super().__init__("Market selection required")
