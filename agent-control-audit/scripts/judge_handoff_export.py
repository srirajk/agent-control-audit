#!/usr/bin/env python3
"""Generate a Judge Handoff Pack: everything a client needs to run the
LLM-as-judge semantic-quality scoring themselves, on their own approved model
(Google, Anthropic, OpenAI, internal, or human review) instead of an API key
we hold.

Why this exists: the deterministic hard-gate checks (tool calls, approval
flags, citations, policy violations) run locally with no API key and no data
leaving the client's environment. The LLM-as-judge layer is inherently
provider-dependent, and for regulated clients (AML, financial, healthcare)
sending case transcripts to an externally-called judge model may not be
something their governance rules allow. This script defers judge execution to
the client while keeping the rubric identical to what a live DeepEval run
would use (agent-control-audit/engine/judge_rubric.py), so the two paths
produce genuinely comparable evidence.

This script does not call an LLM, does not require DeepEval, and does not
require an API key. It only reads already-normalized cases and already-
recorded results and renders the handoff pack deterministically.
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

import assertions  # noqa: E402
import eval_runner  # noqa: E402
import judge_rubric  # noqa: E402
from render_report import write_xlsx  # noqa: E402

RESULT_TEMPLATE_FIELDS = ["score", "passed", "judge_model_used", "run_date", "rationale"]


def build_judge_cases(cases: list[dict[str, Any]], results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """A judge scoring AML behavior needs more than the free-text output: whether
    the hard gate already passed/failed, whether the agent blocked or requested
    approval, which tools it called, what it cited, and which checks were text
    heuristics vs. structured evidence. Without this, a reviewer cannot reliably
    judge approval-gate or forbidden-tool-use dimensions from `actual_output`
    alone — so this runs the same deterministic evaluation used everywhere else
    (engine/assertions.py) and hands the judge its output as context."""
    judge_cases = []
    for case in cases:
        result = results.get(case["id"])
        evaluation = assertions.evaluate_case(case, result) if result is not None else None
        judge_case = {
            "case_id": case["id"],
            "suite": case["suite"],
            "severity": case["severity"],
            "input": case["input"],
            "expected": case.get("expected"),
            "actual_output": (result or {}).get("observed_output", ""),
            "missing_result": result is None,
            "hard_gate_passed": (not evaluation["failures"]) if evaluation else None,
            "hard_gate_failures": evaluation["failures"] if evaluation else [],
            "structured_failures": evaluation["structured_failures"] if evaluation else [],
            "text_fallback_failures": evaluation["text_fallback_failures"] if evaluation else [],
            "assertion_limitations": evaluation["assertion_limitations"] if evaluation else [],
            "blocked": evaluation["blocked"] if evaluation else None,
            "approval_requested": evaluation["approval_requested"] if evaluation else None,
            "tool_calls": evaluation["tool_calls"] if evaluation else [],
            "citations": evaluation["citations"] if evaluation else [],
        }
        if case.get("retrieved_doc"):
            judge_case["retrieved_doc"] = case["retrieved_doc"]
        judge_cases.append(judge_case)
    return judge_cases


def render_instructions(pack_dir_name: str, case_count: int, missing_result_count: int) -> str:
    lines = [
        "# Instructions For Client — Judge Handoff Pack",
        "",
        f"This pack contains {case_count} cases that need semantic-quality scoring against "
        "the enclosed rubric. It does not require you to run our code, install DeepEval, or "
        "share any API key with us.",
        "",
        "## What's In This Folder",
        "",
        "- `judge_rubric.md` — the scoring criteria and threshold. This is the exact rubric "
        "our own generated DeepEval suite uses when a judge-model API key is available locally, "
        "so your results are comparable to a live DeepEval run.",
        "- `judge_cases.jsonl` — one row per case: `input` (what the agent was asked), "
        "`actual_output` (what the agent produced), `expected` (the expected behavior label), "
        "`retrieved_doc` when grounding evidence was supplied, and the deterministic evaluation already "
        "run against this case — `hard_gate_passed`, `hard_gate_failures`, `blocked`, `approval_requested`, "
        "`tool_calls`, `citations`, and `assertion_limitations` (which checks were text-substring heuristics "
        "rather than structured fields). Use these fields to judge approval-gate and forbidden-tool-use "
        "behavior precisely — see `judge_rubric.md`'s \"Inputs Per Case\" section for how.",
        "- `judge_result_template.json` / `judge_result_template.xlsx` — fill in `score`, "
        "`passed`, `judge_model_used`, `run_date`, and `rationale` for every `case_id`.",
        "",
        "## Data Sensitivity",
        "",
        "Before sending `judge_cases.jsonl` to any judge model or reviewer, confirm whether "
        "`input`/`actual_output`/`retrieved_doc` contain synthetic test data or real production "
        "content. This pack does not redact or classify that for you — check with the owner of "
        "the dataset this pack was generated from before it leaves your environment.",
        "",
        "## What To Do",
        "",
        "1. Read `judge_rubric.md`.",
        "2. For each row in `judge_cases.jsonl`, score `actual_output` against `expected` and "
        "`input` (and `retrieved_doc` when present) using your own approved judge model or a "
        "human reviewer, per the rubric.",
        "3. Fill in `judge_result_template.json` (or the `.xlsx` copy) with your scores.",
        "4. Return the completed file to us as `judge_result.json` in this same folder.",
        "",
        "## What Happens Next",
        "",
        "We re-import your completed `judge_result.json` with "
        "`scripts/judge_result_import.py` to produce `llm_judge_score` evidence in the assurance "
        "report. This does not replace or override the deterministic hard-gate results already in "
        "`06_evals/results/eval_summary.md` — both are reported side by side.",
    ]
    if missing_result_count:
        lines.extend(
            [
                "",
                "## Note",
                "",
                f"{missing_result_count} case(s) in `judge_cases.jsonl` have `missing_result: true` — "
                "no recorded agent output exists for them yet. Skip scoring those until a result is available.",
            ]
        )
    return "\n".join(lines)


def render_pack(
    cases: list[dict[str, Any]], results: dict[str, dict[str, Any]], out_dir: Path, domain: str | None = None
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    judge_cases = build_judge_cases(cases, results)
    missing_result_count = sum(1 for jc in judge_cases if jc["missing_result"])

    (out_dir / "judge_rubric.md").write_text(judge_rubric.rubric_markdown(domain=domain), encoding="utf-8")

    with (out_dir / "judge_cases.jsonl").open("w", encoding="utf-8") as handle:
        for judge_case in judge_cases:
            handle.write(json.dumps(judge_case, sort_keys=True) + "\n")

    template = [
        {"case_id": jc["case_id"], **{field: None for field in RESULT_TEMPLATE_FIELDS}} for jc in judge_cases
    ]
    (out_dir / "judge_result_template.json").write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    write_xlsx(
        out_dir / "judge_result_template.xlsx",
        {
            "Judge Results": [
                ["case_id", *RESULT_TEMPLATE_FIELDS],
                *[[jc["case_id"], "", "", "", "", ""] for jc in judge_cases],
            ]
        },
    )

    (out_dir / "instructions_for_client.md").write_text(
        render_instructions(out_dir.name, len(judge_cases), missing_result_count), encoding="utf-8"
    )

    return {
        "status": "ok",
        "out_dir": str(out_dir),
        "cases": len(judge_cases),
        "missing_result_cases": missing_result_count,
        "files": [
            "judge_rubric.md",
            "judge_cases.jsonl",
            "judge_result_template.json",
            "judge_result_template.xlsx",
            "instructions_for_client.md",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Judge Handoff Pack for client-run LLM-as-judge scoring")
    parser.add_argument("--dataset", type=Path, action="append", required=True, help="Normalized dataset JSONL path. Repeatable.")
    parser.add_argument("--results", type=Path, required=True, help="Recorded result JSONL (same shape eval_runner.py --results expects).")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory, e.g. 06_evals/judge_handoff/.")
    parser.add_argument(
        "--domain",
        help="Domain pack name. When domain_extensions/<domain>/judge_rubric_overlay.md exists, its text is "
        "appended to the rendered rubric — the same combined criteria a live DeepEval run with --domain would use.",
    )
    args = parser.parse_args()

    cases = eval_runner.load_cases(args.dataset)
    results = eval_runner.load_results(args.results)
    summary = render_pack(cases, results, args.out_dir, args.domain)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
