# app/domains/reports/__init__.py
"""Reports domain exports."""

from app.domains.reports.formatter import (
    add_legacy_fields,
    format_action_summary,
    format_bullet_list,
    format_report_markdown,
)
from app.domains.reports.generator import (
    clean_json_response,
    generate_report,
    generate_report_with_llm,
    normalize_list_fields,
    validate_report_data,
)
from app.domains.reports.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    extract_prompt_data,
)
from app.domains.reports.schemas import ReportData, ReportSection
from app.domains.reports.service import ReportService, get_report_service
from app.domains.reports.templates import generate_fallback_report, signal_to_dict

__all__ = [
    # Schemas
    "ReportData",
    "ReportSection",
    # Prompts
    "SYSTEM_PROMPT",
    "build_user_prompt",
    "extract_prompt_data",
    # Templates
    "generate_fallback_report",
    "signal_to_dict",
    # Generator
    "clean_json_response",
    "generate_report",
    "generate_report_with_llm",
    "normalize_list_fields",
    "validate_report_data",
    # Formatter
    "add_legacy_fields",
    "format_action_summary",
    "format_bullet_list",
    "format_report_markdown",
    # Service
    "ReportService",
    "get_report_service",
]
