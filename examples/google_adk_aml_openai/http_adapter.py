#!/usr/bin/env python3
"""Backward-compatible HTTP adapter entrypoint."""

try:
    from .adk_aml_openai.adapters.http_adapter import main
except ImportError:  # pragma: no cover - direct CLI execution path
    from adk_aml_openai.adapters.http_adapter import main


if __name__ == "__main__":
    raise SystemExit(main())
