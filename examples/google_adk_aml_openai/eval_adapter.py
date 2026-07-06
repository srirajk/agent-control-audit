#!/usr/bin/env python3
"""Backward-compatible eval adapter import path and CLI entrypoint."""

from __future__ import annotations

import json
import sys

try:
    from .adk_aml_openai.assurance.eval_adapter import deterministic_case_result, run_case, run_live_adk_case
except ImportError:  # pragma: no cover - direct script/folder import path
    from adk_aml_openai.assurance.eval_adapter import deterministic_case_result, run_case, run_live_adk_case

__all__ = ["deterministic_case_result", "run_case", "run_live_adk_case"]


def main() -> int:
    case = json.load(sys.stdin)
    print(json.dumps(run_case(case), sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
