"""API route exports."""

from app.api.routes.analyze import router as analyze_router
from app.api.routes.health import router as health_router
from app.api.routes.runs import router as runs_router

__all__ = ["analyze_router", "health_router", "runs_router"]
