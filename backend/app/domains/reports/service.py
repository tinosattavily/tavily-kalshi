# app/domains/reports/service.py
"""Report service - orchestrates report generation."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.config import get_logger
from app.domains.reports.formatter import add_legacy_fields
from app.domains.reports.generator import generate_report
from app.domains.reports.templates import generate_fallback_report

logger = get_logger(__name__)

DEFAULT_ENV = {
    "app_version": "0.1.0",
    "model": "gpt-4o-mini",
    "tavily_version": "v1",
    "langgraph_graph_version": "market-v1",
}


class ReportService:
    """Service class for report generation.

    Orchestrates LLM-based and template-based report generation.
    """

    def __init__(self, env: Optional[Dict[str, Any]] = None):
        """Initialize ReportService.

        Args:
            env: Environment metadata dict
        """
        self.env = env or DEFAULT_ENV.copy()

    async def generate_report(
        self,
        market_snapshot: Dict[str, Any],
        signal: Dict[str, Any],
        decision: Dict[str, Any],
        event_context: Optional[Dict[str, Any]] = None,
        news_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a structured report.

        Args:
            market_snapshot: Market snapshot dict
            signal: Signal dict
            decision: Decision dict
            event_context: Event context dict (optional)
            news_context: News context dict (optional)

        Returns:
            Report data dict with legacy fields
        """
        try:
            report = await generate_report(
                market_snapshot=market_snapshot,
                signal=signal,
                decision=decision,
                event_context=event_context,
                news_context=news_context,
            )
            logger.debug("Report generated successfully")
        except Exception as exc:
            logger.warning(
                "Report generation failed, using fallback",
                error=str(exc),
                error_type=type(exc).__name__,
                exc_info=True,
            )
            report = generate_fallback_report(
                market_snapshot=market_snapshot,
                signal=signal,
                decision=decision,
                event_context=event_context,
                news_context=news_context,
            )

        # Add legacy fields
        report = add_legacy_fields(report)

        return report

    def generate_fallback(
        self,
        market_snapshot: Dict[str, Any],
        signal: Dict[str, Any],
        decision: Dict[str, Any],
        event_context: Optional[Dict[str, Any]] = None,
        news_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a fallback template report.

        Args:
            market_snapshot: Market snapshot dict
            signal: Signal dict
            decision: Decision dict
            event_context: Event context dict (optional)
            news_context: News context dict (optional)

        Returns:
            Report data dict
        """
        report = generate_fallback_report(
            market_snapshot=market_snapshot,
            signal=signal,
            decision=decision,
            event_context=event_context,
            news_context=news_context,
        )
        return add_legacy_fields(report)

    def get_env(self) -> Dict[str, Any]:
        """Get environment metadata.

        Returns:
            Environment dict
        """
        return self.env.copy()


# Module-level singleton
_report_service: Optional[ReportService] = None


def get_report_service(env: Optional[Dict[str, Any]] = None) -> ReportService:
    """Get the ReportService instance.

    Args:
        env: Optional environment metadata

    Returns:
        ReportService instance
    """
    global _report_service
    if _report_service is None:
        _report_service = ReportService(env=env)
    return _report_service
