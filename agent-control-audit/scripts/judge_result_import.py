#!/usr/bin/env python3
"""Import a client-completed Judge Handoff Pack result file and produce
llm_judge_score evidence.

This does not call an LLM. It validates the client's returned
`judge_result.json` (an array of {case_id, score, passed, judge_model_used,
run_date, rationale}) against the original dataset, recomputes pass/fail from
score vs. threshold (rather than trusting a possibly-inconsistent client-
supplied `passed` value), and flags data-quality issues — a returned score
with no judge_model_used/run_date is materially weaker evidence than a fully
attributed one, and this must be visible in the summary, not silently dropped.
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


def load_judge_results(path: Path) -> dict[str, dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"{path}: judge result file must be a JSON array")
    by_case_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or "case_id" not in row:
            raise ValueError(f"{path}: every entry must be an object with a case_id")
        case_id = row["case_id"]
        if case_id in by_case_id:
            raise ValueError(f"{path}: duplicate case_id {case_id!r}")
        by_case_id[case_id] = row
    return by_case_id


def evaluate_judge_results(
    cases: list[dict[str, Any]], judge_results: dict[str, dict[str, Any]], threshold: float, domain: str | None = None
) -> dict[str, Any]:
    dataset_case_ids = {case["id"] for case in cases}
    unexpected_case_ids = sorted(set(judge_results) - dataset_case_ids)
    matched_case_ids = set(judge_results) & dataset_case_ids
    if judge_results and not matched_case_ids:
        raise ValueError(
            f"None of the {len(judge_results)} case_id(s) in the returned judge results match this dataset's "
            f"case ids. This looks like the wrong judge_result.json was uploaded. Returned ids: {sorted(judge_results)}"
        )

    graded: list[dict[str, Any]] = []
    for case in cases:
        row = judge_results.get(case["id"])
        data_quality_issues: list[str] = []
        if row is None:
            graded.append(
                {
                    "case_id": case["id"],
                    "suite": case["suite"],
                    "severity": case["severity"],
                    "scored": False,
                    "score": None,
                    "passed": None,
                    "data_quality_issues": ["no judge result returned for this case"],
                }
            )
            continue

        score = row.get("score")
        if not isinstance(score, (int, float)) or not (0.0 <= float(score) <= 1.0):
            data_quality_issues.append(f"score {score!r} is not a number in [0.0, 1.0]")
            score = None
        if not row.get("judge_model_used"):
            data_quality_issues.append("judge_model_used is missing — score cannot be attributed to a specific judge model")
        if not row.get("run_date"):
            data_quality_issues.append("run_date is missing")
        client_passed = row.get("passed")
        recomputed_passed = (float(score) >= threshold) if score is not None else None
        if client_passed is not None and score is not None and bool(client_passed) != recomputed_passed:
            data_quality_issues.append(
                f"client-supplied passed={client_passed!r} disagrees with recomputed passed={recomputed_passed!r} "
                f"from score={score!r} vs threshold={threshold}; recomputed value is used"
            )

        graded.append(
            {
                "case_id": case["id"],
                "suite": case["suite"],
                "severity": case["severity"],
                "scored": score is not None,
                "score": score,
                "passed": recomputed_passed,
                "judge_model_used": row.get("judge_model_used"),
                "run_date": row.get("run_date"),
                "rationale": row.get("rationale"),
                "data_quality_issues": data_quality_issues,
            }
        )

    scored = [g for g in graded if g["scored"]]
    passed = [g for g in scored if g["passed"]]
    unscored = [g for g in graded if not g["scored"]]
    with_issues = [g for g in graded if g["data_quality_issues"]]

    by_suite: dict[str, dict[str, Any]] = {}
    for grade in graded:
        suite = grade["suite"]
        row = by_suite.setdefault(suite, {"total": 0, "scored": 0, "passed": 0, "with_issues": 0})
        row["total"] += 1
        row["scored"] += int(grade["scored"])
        row["passed"] += int(bool(grade["passed"]))
        row["with_issues"] += int(bool(grade["data_quality_issues"]))

    return {
        "evidence_type": "llm_judge_score",
        "threshold": threshold,
        "rubric_criteria": judge_rubric.combined_criteria(domain),
        "total_cases": len(graded),
        "scored_cases": len(scored),
        "unscored_cases": len(unscored),
        "unexpected_case_ids": unexpected_case_ids,
        "passed": len(passed),
        "pass_rate_of_scored": (len(passed) / len(scored)) if scored else None,
        "average_score": (sum(g["score"] for g in scored) / len(scored)) if scored else None,
        "cases_with_data_quality_issues": len(with_issues),
        "by_suite": by_suite,
        "cases": graded,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a completed Judge Handoff Pack result file")
    parser.add_argument("--dataset", type=Path, action="append", required=True, help="Normalized dataset JSONL path. Repeatable.")
    parser.add_argument("--results", type=Path, required=True, help="Client-returned judge_result.json.")
    parser.add_argument("--threshold", type=float, default=judge_rubric.DEFAULT_THRESHOLD, help="Passing score threshold.")
    parser.add_argument("--domain", help="Domain pack name, if the pack was generated with --domain, for rubric provenance.")
    parser.add_argument("--out", type=Path, help="Output summary JSON path.")
    args = parser.parse_args()

    cases = eval_runner.load_cases(args.dataset)
    judge_results = load_judge_results(args.results)
    summary = evaluate_judge_results(cases, judge_results, args.threshold, args.domain)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({k: v for k, v in summary.items() if k != "cases"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
