"""Common API schema models."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    checks: Optional[dict[str, Any]] = Field(
        None, description="Dependency health checks"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(None, description="Request identifier for tracing")


__all__ = ["HealthResponse", "ErrorResponse"]
