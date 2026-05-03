"""Structured logging configuration using structlog."""

from __future__ import annotations

import logging
import sys

import structlog
from structlog.types import Processor


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    # Determine renderer based on log level
    use_json = log_level.upper() != "DEBUG"

    # Configure structlog processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if use_json:
        # JSON output for production
        renderer = structlog.processors.JSONRenderer()
        processors = shared_processors + [renderer]
    else:
        # Pretty console output for development
        renderer = structlog.dev.ConsoleRenderer(colors=True)
        processors = shared_processors + [renderer]

    # Configure standard library logging to use structlog's formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared_processors,
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)
