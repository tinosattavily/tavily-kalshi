# app/domains/reports/generator.py
"""LLM-based report generation."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

from app.config import get_logger
from app.domains.reports.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    extract_prompt_data,
)
from app.domains.reports.templates import generate_fallback_report, signal_to_dict
from app.infrastructure.llm import get_openai_client

logger = get_logger(__name__)

REQUIRED_FIELDS = [
    "headline",
    "thesis",
    "bull_case",
    "bear_case",
    "key_risks",
    "execution_notes",
]


def clean_json_response(raw_content: str) -> str:
    """Clean markdown code blocks from JSON response.

    Args:
        raw_content: Raw response string

    Returns:
        Cleaned JSON string
    """
    content = raw_content.strip()

    if content.startswith("```json"):
        lines = content.split("\n")
        if lines[-1].startswith("```"):
            content = "\n".join(lines[1:-1])
        else:
            content = "\n".join(lines[1:])
    elif content.startswith("```"):
        lines = content.split("\n")
        if lines[-1].startswith("```"):
            content = "\n".join(lines[1:-1])
        else:
            content = "\n".join(lines[1:])

    return content


def validate_report_data(report_data: Dict[str, Any]) -> bool:
    """Validate that report data has required fields.

    Args:
        report_data: Parsed report data

    Returns:
        True if valid
    """
    for field in REQUIRED_FIELDS:
        if field not in report_data:
            logger.warning(f"Missing field {field} in report data")
            return False
    return True


def normalize_list_fields(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure list fields are actually lists.

    Args:
        report_data: Report data dict

    Returns:
        Normalized report data
    """
    for field in ["bull_case", "bear_case", "key_risks"]:
        if field in report_data and not isinstance(report_data[field], list):
            report_data[field] = [str(report_data[field])]
    return report_data


async def generate_report_with_llm(
    market_snapshot: Dict[str, Any],
    signal: Dict[str, Any],
    decision: Dict[str, Any],
    event_context: Optional[Dict[str, Any]] = None,
    news_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate structured report using LLM.

    Args:
        market_snapshot: Market snapshot dict
        signal: Signal dict
        decision: Decision dict
        event_context: Event context dict (optional)
        news_context: News context dict (optional)

    Returns:
        Report data dict

    Raises:
        RuntimeError: If LLM is not available
    """
    try:
        client = get_openai_client()
    except Exception as exc:
        logger.warning("Failed to get OpenAI client", error=str(exc))
        raise RuntimeError("OpenAI client not available") from exc

    if not client or not client.api_key:
        raise RuntimeError("OpenAI API key not configured")

    # Extract prompt data
    s = signal_to_dict(signal)
    prompt_data = extract_prompt_data(market_snapshot, s, decision, news_context)

    # Build user prompt
    user_msg = build_user_prompt(**prompt_data)

    # Call LLM
    def _call_openai():
        if not client.client:
            raise RuntimeError("OpenAI client not initialized")

        if client._use_new_api:
            try:
                completion = client.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )
            except (TypeError, AttributeError):
                completion = client.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.3,
                )
            return completion.choices[0].message.content
        else:
            import openai

            if not openai.api_key:
                raise RuntimeError("OpenAI API key not configured")
            completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
            )
            return completion.choices[0].message["content"]

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    raw_content = await loop.run_in_executor(None, _call_openai)

    # Parse response
    content = clean_json_response(raw_content)
    report_data = json.loads(content)

    # Validate
    if not validate_report_data(report_data):
        logger.warning("Invalid report data from LLM, using fallback")
        return generate_fallback_report(
            market_snapshot, signal, decision, event_context, news_context
        )

    # Normalize list fields
    report_data = normalize_list_fields(report_data)

    return report_data


async def generate_report(
    market_snapshot: Dict[str, Any],
    signal: Dict[str, Any],
    decision: Dict[str, Any],
    event_context: Optional[Dict[str, Any]] = None,
    news_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate report with LLM, falling back to template on failure.

    Args:
        market_snapshot: Market snapshot dict
        signal: Signal dict
        decision: Decision dict
        event_context: Event context dict (optional)
        news_context: News context dict (optional)

    Returns:
        Report data dict
    """
    try:
        report = await generate_report_with_llm(
            market_snapshot, signal, decision, event_context, news_context
        )
        logger.debug("Report generated successfully with LLM")
        return report
    except Exception as exc:
        logger.warning(
            "Report generation failed, using fallback template",
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        return generate_fallback_report(
            market_snapshot, signal, decision, event_context, news_context
        )
