#!/usr/bin/env python3
"""Create the standard output folder structure for an assurance run."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


STAGES: list[tuple[str, str, list[str]]] = [
    (
        "00_intake",
        "Scope, domain context, source snapshot manifest, and run setup.",
        [
            "scope.md",
            "domain_context.md",
            "business_expectations.md",
            "data_contracts_and_mdm.md",
            "domain_extension_reference.md",
            "governance_expectations.md",
            "quality_profile_notes.md",
            "source_snapshot_manifest.md",
        ],
    ),
    (
        "01_observation",
        "Plain-English understanding of the agent before judging it.",
        ["observation.md"],
    ),
    (
        "02_static_audit",
        "Source-visible framework detection, controls, findings, and evidence.",
        ["static_audit_summary.md", "static_audit.json", "findings.jsonl"],
    ),
    (
        "03_gap_matrix",
        "Human-reviewable control gaps and prioritization.",
        ["gap_matrix.md", "gap_matrix.xlsx"],
    ),
    (
        "04_change_plan",
        "Proposed remediation plan created before source changes.",
        ["change_plan.md"],
    ),
    (
        "05_dataset",
        "Supplied, proposed, normalized, and readiness-checked golden data.",
        [
            "supplied/",
            "proposed/proposed_golden_dataset.md",
            "proposed/proposed_golden_dataset.jsonl",
            "readiness/dataset_readiness.md",
            "readiness/dataset_readiness.xlsx",
            "normalized/normalized_dataset.jsonl",
        ],
    ),
    (
        "06_evals",
        "Generated DeepEval suites and dynamic eval results.",
        ["deepeval/deepeval_suite.py", "results/eval_summary.md", "results/eval_results.jsonl", "results/eval_summary.json"],
    ),
    (
        "07_reports",
        "Final human-facing reports.",
        ["assurance_report.md", "assurance_report.xlsx", "assurance_report.docx"],
    ),
    (
        "08_remediation",
        "Approved code-change plans, patches, copied source, or branch notes.",
        ["proposed_changes.md", "patch.diff", "patched_copy/"],
    ),
    (
        "evidence",
        "Hashes, manifests, trace references, and durable evidence records.",
        ["evidence_summary.md", "evidence_manifest.json", "hashes.jsonl"],
    ),
]


def default_run_id() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H%M")


def slugify(value: str) -> str:
    source = value.strip()
    if not source:
        return "agent-assurance-run"
    name = Path(source).name or source
    if name in {".", "/"}:
        name = "agent-assurance-run"
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-._")
    return slug.lower() or "agent-assurance-run"


def artifact_index(target: str, domain: str, run_id: str) -> str:
    lines = [
        "# Agent Assurance Artifact Index",
        "",
        f"- **Target:** {target or 'not specified'}",
        f"- **Domain/profile:** {domain or 'not specified'}",
        f"- **Run ID:** {run_id}",
        "",
        "Use this index to understand where each artifact belongs. JSON and JSONL files are evidence; Markdown, Excel, and DOCX files are the human review surfaces.",
        "",
        "| Folder | Purpose | Typical Artifacts |",
        "| --- | --- | --- |",
    ]
    for folder, purpose, artifacts in STAGES:
        lines.append(f"| `{folder}/` | {purpose} | {', '.join(f'`{item}`' for item in artifacts)} |")
    lines.extend(
        [
            "",
            "## Golden Dataset Gate",
            "",
            "If no supplied golden dataset exists, use `05_dataset/proposed/` for draft synthetic seed cases. Do not treat those cases as approved golden data until the user/team explicitly approves them.",
            "",
            "## Source Safety",
            "",
            "Do not mutate the original target repository silently. Put proposed remediation plans in `04_change_plan/` and approved copied/patch work in `08_remediation/`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a structured output folder for an agent assurance run.")
    parser.add_argument("--out", help="Run output directory to create. If omitted, uses --base-out/<target-slug>/<run-id>.")
    parser.add_argument("--base-out", default="outputs", help="Base output directory used when --out is omitted.")
    parser.add_argument("--target-slug", default="", help="Folder-safe target name used when --out is omitted.")
    parser.add_argument("--target", default="", help="Target repository path or URL.")
    parser.add_argument("--domain", default="", help="Domain or quality profile, such as financial_aml.")
    parser.add_argument("--run-id", default="", help="Run identifier. Defaults to local timestamp YYYY-MM-DD-HHMM.")
    args = parser.parse_args()

    run_id = args.run_id or default_run_id()
    if args.out:
        out = Path(args.out).expanduser().resolve()
    else:
        target_slug = args.target_slug or slugify(args.target)
        out = (Path(args.base_out).expanduser() / target_slug / run_id).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for folder, _purpose, artifacts in STAGES:
        base = out / folder
        base.mkdir(parents=True, exist_ok=True)
        for artifact in artifacts:
            if artifact.endswith("/"):
                (base / artifact).mkdir(parents=True, exist_ok=True)
            elif "/" in artifact:
                (base / artifact).parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "1.0",
        "target": args.target,
        "domain": args.domain,
        "run_id": run_id,
        "created_at_local": datetime.now().isoformat(timespec="minutes"),
        "output_dir": str(out),
        "folders": [
            {"path": folder, "purpose": purpose, "typical_artifacts": artifacts}
            for folder, purpose, artifacts in STAGES
        ],
    }
    (out / "_run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "ARTIFACT_INDEX.md").write_text(artifact_index(args.target, args.domain, run_id), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "output_dir": str(out),
                "manifest": str(out / "_run_manifest.json"),
                "run_id": run_id,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
