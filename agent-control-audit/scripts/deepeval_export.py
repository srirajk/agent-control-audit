#!/usr/bin/env python3
"""Deterministically export datasets into the default DeepEval pytest suite.

This exporter has no DeepEval dependency. The generated pytest file imports
DeepEval only when the user runs it. This script does not invoke an LLM, run a
judge, or call the target agent; it only renders Python test code from already
normalized cases.

The generated suite's assertion logic is sourced verbatim from
agent-control-audit/engine/assertions.py at generation time, not hand-copied,
so the generated suite and the local eval_runner.py grader can never drift
from each other again.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ENGINE_DIR = SCRIPT_DIR.parent / "engine"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ENGINE_DIR))

import eval_runner  # noqa: E402
import judge_rubric  # noqa: E402


def public_case(case: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in case.items() if not key.startswith("_")}


def embed_assertions_source() -> str:
    """Read engine/assertions.py verbatim, minus its own `from __future__` line
    (the generated file declares that once, at its own top, as Python requires)."""
    src = (ENGINE_DIR / "assertions.py").read_text(encoding="utf-8")
    lines = [line for line in src.splitlines() if not line.startswith("from __future__ import")]
    return "\n".join(lines)


def render_pytest(cases: list[dict[str, Any]], domain: str | None = None) -> str:
    cases_json = json.dumps([public_case(case) for case in cases], indent=2, sort_keys=True)
    assertions_src = embed_assertions_source()
    criteria_repr = repr(judge_rubric.combined_criteria(domain))
    return f'''"""Generated DeepEval tests for agent-control-audit.

Install DeepEval dependencies in the target project, then run:
  pip install deepeval pytest
  AGENT_ASSURANCE_COMMAND="python path/to/agent_adapter.py" deepeval test run this_file.py

The deterministic gates below always run before the LLM-as-judge metric.
structured_runtime_evidence failures come from structured result fields
(blocked, approval_requested, tool_calls, citations, policy_violations) and are
real gates. text_fallback_heuristic failures come from substring/regex scans of
free-text output and are smoke checks, not semantic proof.
Set AGENT_ASSURANCE_DEEPEVAL_JUDGE=0 to run only deterministic gates.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess

import pytest


def import_deepeval():
    """DeepEval is only required in judge mode (AGENT_ASSURANCE_DEEPEVAL_JUDGE != "0").
    Importing it lazily, inside the test, means AGENT_ASSURANCE_DEEPEVAL_JUDGE=0 actually
    runs the deterministic gates standalone without DeepEval installed, matching this
    file's own module docstring instead of contradicting it with a module-level
    pytest.skip(allow_module_level=True) that would skip every test regardless of mode."""
    try:
        from deepeval import assert_test
        from deepeval.metrics import GEval
        from deepeval.test_case import LLMTestCase
        try:
            from deepeval.test_case import LLMTestCaseParams as params_cls
        except Exception:
            from deepeval.test_case import SingleTurnParams as params_cls
        return assert_test, GEval, LLMTestCase, params_cls
    except Exception as exc:  # pragma: no cover - generated optional dependency path
        pytest.fail(
            f"DeepEval is not installed or importable: {{exc}}. "
            "Set AGENT_ASSURANCE_DEEPEVAL_JUDGE=0 to run only deterministic gates without DeepEval installed."
        )


CASES = {cases_json}


# --- Begin shared assertion engine, sourced verbatim from agent-control-audit/engine/assertions.py ---
{assertions_src}
# --- End shared assertion engine ---


def hard_gate_failures(case: dict, result: dict) -> list:
    return evaluate_case(case, result)["failures"]


def run_target(case: dict) -> dict:
    command = os.environ.get("AGENT_ASSURANCE_COMMAND")
    if not command:
        pytest.fail("Set AGENT_ASSURANCE_COMMAND to a command that reads case JSON on stdin.")
    completed = subprocess.run(
        shlex.split(command),
        input=json.dumps(case, sort_keys=True),
        text=True,
        capture_output=True,
        timeout=int(os.environ.get("AGENT_ASSURANCE_TIMEOUT", "60")),
        check=False,
    )
    if completed.returncode != 0:
        pytest.fail(f"target command failed with {{completed.returncode}}: {{completed.stderr}}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(f"target command did not emit JSON: {{exc}}; stdout={{completed.stdout!r}}")
    result.setdefault("id", case["id"])
    result.setdefault("suite", case["suite"])
    result.setdefault("tool_calls", [])
    result.setdefault("blocked", False)
    result.setdefault("approval_requested", False)
    result.setdefault("citations", [])
    return result


def make_metric(case: dict, GEval, params_cls):
    # Sourced verbatim from agent-control-audit/engine/judge_rubric.py at generation time, the
    # same rubric a client scores against by hand in a Judge Handoff Pack (judge_handoff_export.py)
    # when no local judge-model API key is available — the two paths must never drift.
    threshold = float(os.environ.get("AGENT_ASSURANCE_DEEPEVAL_THRESHOLD", "{judge_rubric.DEFAULT_THRESHOLD}"))
    criteria = {criteria_repr}
    return GEval(
        name=f"agent_assurance_{{case['suite']}}",
        criteria=criteria,
        evaluation_params=[params_cls.INPUT, params_cls.ACTUAL_OUTPUT, params_cls.EXPECTED_OUTPUT],
        threshold=threshold,
    )


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_agent_assurance(case: dict):
    result = run_target(case)
    failures = hard_gate_failures(case, result)
    assert not failures, failures

    if os.environ.get("AGENT_ASSURANCE_DEEPEVAL_JUDGE", "1") == "0":
        return

    assert_test, GEval, LLMTestCase, params_cls = import_deepeval()
    test_case = LLMTestCase(
        input=case["input"],
        actual_output=str(result.get("observed_output") or ""),
        expected_output=str(case.get("expected") or ""),
    )
    assert_test(test_case, [make_metric(case, GEval, params_cls)])
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically export normalized datasets to a DeepEval pytest file")
    parser.add_argument("--dataset", type=Path, action="append", required=True, help="Dataset JSONL path. Repeatable.")
    parser.add_argument("--out", type=Path, required=True, help="Generated pytest file path.")
    parser.add_argument(
        "--domain",
        help="Domain pack name. When domain_extensions/<domain>/judge_rubric_overlay.md exists, its text is "
        "appended to the GEval criteria — the same combined criteria judge_handoff_export.py renders for a "
        "client-run judge, so the two paths never score against different rubrics.",
    )
    args = parser.parse_args()

    cases = eval_runner.load_cases(args.dataset)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_pytest(cases, args.domain), encoding="utf-8")
    print(json.dumps({"status": "ok", "cases": len(cases), "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
