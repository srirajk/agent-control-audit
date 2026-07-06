#!/usr/bin/env python3
"""Dataset validator and deterministic eval runner/grader.

The runner supports three modes:

1. Validate datasets only.
2. Grade pre-recorded result JSONL.
3. Invoke a command template for each case and grade the JSON result.

Command templates receive the case JSON through stdin and should emit JSON with:
observed_output, tool_calls, blocked, approval_requested, citations, notes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE_DIR))

import assertions  # noqa: E402


REQUIRED_CASE_FIELDS = {"id", "suite", "input", "expected", "must_not", "severity", "source"}
ALLOWED_SEVERITIES = {"blocker", "high", "medium", "low"}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            row["_dataset_file"] = str(path)
            row["_line"] = line_no
            rows.append(row)
    return rows


def load_cases(dataset_paths: list[Path]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in dataset_paths:
        for case in load_jsonl(path):
            missing = REQUIRED_CASE_FIELDS - set(case)
            if missing:
                raise ValueError(f"{case['_dataset_file']}:{case['_line']}: missing fields {sorted(missing)}")
            if case["id"] in seen:
                raise ValueError(f"{case['_dataset_file']}:{case['_line']}: duplicate id {case['id']}")
            seen.add(case["id"])
            if case["severity"] not in ALLOWED_SEVERITIES:
                raise ValueError(f"{case['_dataset_file']}:{case['_line']}: invalid severity {case['severity']}")
            if not isinstance(case.get("must_not"), list):
                raise ValueError(f"{case['_dataset_file']}:{case['_line']}: must_not must be a list")
            cases.append(case)
    return cases


def load_results(path: Path) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(path):
        case_id = row.get("id")
        if not case_id:
            raise ValueError(f"{row['_dataset_file']}:{row['_line']}: result missing id")
        if case_id in results:
            raise ValueError(f"{row['_dataset_file']}:{row['_line']}: duplicate result id {case_id}")
        results[case_id] = row
    return results


def run_case(command: str, case: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    try:
        command_args = shlex.split(command)
    except ValueError as exc:
        return {
            "id": case["id"],
            "suite": case["suite"],
            "observed_output": "",
            "tool_calls": [],
            "blocked": False,
            "approval_requested": False,
            "citations": [],
            "notes": f"runner command could not be parsed: {exc}",
            "_runner_error": True,
        }
    if not command_args:
        return {
            "id": case["id"],
            "suite": case["suite"],
            "observed_output": "",
            "tool_calls": [],
            "blocked": False,
            "approval_requested": False,
            "citations": [],
            "notes": "runner command is empty",
            "_runner_error": True,
        }
    completed = subprocess.run(
        command_args,
        input=json.dumps(case, sort_keys=True),
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "id": case["id"],
            "suite": case["suite"],
            "observed_output": completed.stdout.strip(),
            "tool_calls": [],
            "blocked": False,
            "approval_requested": False,
            "citations": [],
            "notes": f"runner command failed with {completed.returncode}: {completed.stderr.strip()}",
            "_runner_error": True,
        }
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = {"observed_output": completed.stdout.strip(), "tool_calls": [], "blocked": False}
    result.setdefault("id", case["id"])
    result.setdefault("suite", case["suite"])
    return result


def grade_case(case: dict[str, Any], result: dict[str, Any] | None) -> dict[str, Any]:
    """Thin wrapper over the shared assertions engine (agent-control-audit/engine/assertions.py),
    reshaped into this module's historical return shape so existing callers/tests are unaffected."""
    evaluation = assertions.evaluate_case(case, result)
    graded_result = evaluation["result"]
    return {
        "id": case["id"],
        "suite": case["suite"],
        "severity": case["severity"],
        "expected": case.get("expected"),
        "passed": not evaluation["failures"],
        "failures": evaluation["failures"],
        "observed_output": graded_result.get("observed_output", ""),
        "tool_calls": evaluation["tool_calls"],
        "blocked": evaluation["blocked"],
        "approval_requested": evaluation["approval_requested"],
        "citations": evaluation["citations"],
        "notes": graded_result.get("notes", ""),
        "case_hash": canonical_hash({k: v for k, v in case.items() if not k.startswith("_")}),
        "result_hash": canonical_hash({k: v for k, v in graded_result.items() if not k.startswith("_")}),
        "assertion_limitations": evaluation["assertion_limitations"],
        "structured_failures": evaluation["structured_failures"],
        "text_fallback_failures": evaluation["text_fallback_failures"],
    }


def summarize(grades: list[dict[str, Any]], dataset_hash: str) -> dict[str, Any]:
    by_suite: dict[str, dict[str, Any]] = {}
    suite_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for grade in grades:
        suite_groups[grade["suite"]].append(grade)

    def evidence_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
        passed_rows = [row for row in rows if row["passed"]]
        relies_on_text_fallback = [row for row in passed_rows if row.get("assertion_limitations")]
        return {
            "passed_on_structured_evidence_only": len(passed_rows) - len(relies_on_text_fallback),
            "passed_with_text_fallback_reliance": len(relies_on_text_fallback),
        }

    for suite, rows in suite_groups.items():
        total = len(rows)
        failed = [row for row in rows if not row["passed"]]
        by_suite[suite] = {
            "total": total,
            "passed": total - len(failed),
            "failed": len(failed),
            "pass_rate": (total - len(failed)) / total if total else 0.0,
            "failed_ids": [row["id"] for row in failed],
            **evidence_counts(rows),
        }

    total = len(grades)
    failed = [grade for grade in grades if not grade["passed"]]
    adversarial = [grade for grade in grades if grade["suite"] != "benign_false_positives"]
    adversarial_failed = [grade for grade in adversarial if not grade["passed"]]
    benign = [grade for grade in grades if grade["suite"] == "benign_false_positives"]
    benign_failed = [grade for grade in benign if not grade["passed"]]
    return {
        "schema_version": "1.0",
        "dataset_hash": dataset_hash,
        "total": total,
        "passed": total - len(failed),
        "failed": len(failed),
        "pass_rate": (total - len(failed)) / total if total else 0.0,
        "attack_failure_rate": len(adversarial_failed) / len(adversarial) if adversarial else 0.0,
        "benign_false_positive_rate": len(benign_failed) / len(benign) if benign else 0.0,
        "by_suite": by_suite,
        "failed_ids": [grade["id"] for grade in failed],
        **evidence_counts(grades),
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or grade agent-control-audit golden eval datasets")
    parser.add_argument("--dataset", type=Path, action="append", required=True, help="Dataset JSONL path. Repeatable.")
    parser.add_argument("--results", type=Path, help="Pre-recorded result JSONL to grade.")
    parser.add_argument("--command", help="Command template to run for each case. Receives case JSON on stdin.")
    parser.add_argument("--timeout", type=int, default=60, help="Per-case command timeout in seconds.")
    parser.add_argument("--out", type=Path, help="Output JSONL grades path.")
    parser.add_argument("--summary", type=Path, help="Output summary JSON path.")
    parser.add_argument("--validate-only", action="store_true", help="Only validate datasets and print hash/summary.")
    args = parser.parse_args()

    cases = load_cases(args.dataset)
    dataset_hash = canonical_hash([{k: v for k, v in case.items() if not k.startswith("_")} for case in cases])

    if args.validate_only:
        summary = {"status": "ok", "cases": len(cases), "dataset_hash": dataset_hash}
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if bool(args.results) == bool(args.command):
        parser.error("Provide exactly one of --results or --command, or use --validate-only.")

    if args.results:
        result_map = load_results(args.results)
    else:
        result_map = {}
        assert args.command is not None
        for case in cases:
            result_map[case["id"]] = run_case(args.command, case, args.timeout)

    grades = [grade_case(case, result_map.get(case["id"])) for case in cases]
    summary = summarize(grades, dataset_hash)

    if args.out:
        write_jsonl(args.out, grades)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
