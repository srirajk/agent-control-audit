"""Backward-compatible FastAPI app import path."""

try:
    from .adk_aml_openai.api.server import AssuranceCase, app, health, invoke
except ImportError:  # pragma: no cover - direct uvicorn import path
    from adk_aml_openai.api.server import AssuranceCase, app, health, invoke

__all__ = ["AssuranceCase", "app", "health", "invoke"]
