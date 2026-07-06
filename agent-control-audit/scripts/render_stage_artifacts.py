#!/usr/bin/env python3
"""Render human-readable stage artifacts for an assurance run.

Machine artifacts such as JSON and JSONL are evidence. This script creates the
Markdown and Excel surfaces a human reviewer can actually follow stage by stage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from render_report import write_xlsx


def load_json(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def bullet_list(values: list[Any]) -> list[str]:
    if not values:
        return ["- None observed."]
    return [f"- {value}" for value in values]


def control_lookup(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(control.get("control_id")): control for control in audit.get("controls_present") or []}


def finding_lookup(audit: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_control: dict[str, list[dict[str, Any]]] = {}
    for finding in audit.get("findings") or []:
        control_id = str((finding.get("control") or {}).get("id") or "")
        by_control.setdefault(control_id, []).append(finding)
    return by_control


def gap_rows(audit: dict[str, Any]) -> list[dict[str, str]]:
    present = control_lookup(audit)
    findings = finding_lookup(audit)
    rows: list[dict[str, str]] = []
    for requirement, controls in sorted((audit.get("required_controls") or {}).items()):
        for control_id in controls:
            control = present.get(control_id, {})
            control_findings = findings.get(control_id, [])
            if control:
                status = "present"
                evidence = control.get("location", "")
                notes = control.get("adequacy_notes", "")
            elif control_findings:
                status = control_findings[0].get("status", "missing")
                evidence = control_findings[0].get("location") or "not detected"
                notes = control_findings[0].get("recommendation", "")
            else:
                status = "not_checked"
                evidence = "No source-visible evidence recorded."
                notes = "Reviewer should confirm whether this control is implemented outside the repository."
            rows.append(
                {
                    "requirement": str(requirement),
                    "control_id": str(control_id),
                    "control_name": str(control.get("name") or ""),
                    "status": status,
                    "evidence": str(evidence),
                    "notes": str(notes),
                }
            )
    return rows


def domain_extension_reference_text(audit: dict[str, Any], domain: str) -> str:
    resolved_domain = audit.get("domain") or domain
    if not resolved_domain:
        return "# Domain Extension Reference\n\n- **Selected profile:** not specified\n- **Extension pack:** no domain was selected for this run."
    if audit.get("domain_overlay_loaded"):
        overlay_ids = ", ".join(audit.get("domain_overlay_requirement_ids") or []) or "none"
        return (
            f"# Domain Extension Reference\n\n"
            f"- **Selected profile:** {resolved_domain}\n"
            f"- **Extension pack:** loaded from `{audit.get('domain_overlay_path')}`\n"
            f"- **Overlay requirements merged into required_controls:** {overlay_ids}\n\n"
            "These requirements are schema-validated (agent-control-audit/engine/schema_validate.py) and merged by "
            "scripts/static_audit.py before this run's required_controls, gap matrix, and dataset quality profile were produced — "
            "see 03_gap_matrix/domain_overlay_diff.md for exactly what the domain pack changed versus a no-domain baseline."
        )
    return (
        f"# Domain Extension Reference\n\n"
        f"- **Selected profile:** {resolved_domain}\n"
        f"- **Extension pack:** none found at `domain_extensions/{resolved_domain}/regime_overlay.json`\n\n"
        f"No `regime_overlay.json` exists for this domain, so required_controls for this run come only from the base "
        "financial regime (regimes/financial.json). Add domain_extensions/<domain>/regime_overlay.json (see "
        "domain_extensions/_template/regime_overlay.json) to have domain-specific requirements merged in."
    )


def render_intake(run_dir: Path, audit: dict[str, Any], target: str, domain: str) -> None:
    profile = audit.get("profile") or {}
    write(
        run_dir / "00_intake" / "scope.md",
        "\n".join(
            [
                "# Intake Scope",
                "",
                f"- **Target:** {target or audit.get('target', 'not specified')}",
                f"- **Domain/profile:** {domain or 'not specified'}",
                f"- **Framework detected:** {audit.get('framework', 'not checked')}",
                f"- **Run mode:** static audit plus deterministic eval evidence when available",
                "",
                "## What This Run Is Trying To Prove",
                "",
                "This run checks whether the target agent has source-visible controls, usable golden-data evidence, generated DeepEval tests, dynamic invocation evidence, and a human-readable governance report.",
            ]
        ),
    )
    write(
        run_dir / "00_intake" / "domain_context.md",
        "\n".join(
            [
                "# Domain Context",
                "",
                f"- **Business context inferred:** {profile.get('business', 'not specified')}",
                f"- **Autonomy:** {profile.get('autonomy', 'not specified')}",
                "",
                "## Harm Surfaces",
                "",
                *bullet_list(profile.get("harm_surfaces") or []),
                "",
                "## Architecture Signals",
                "",
                *bullet_list(profile.get("architecture") or []),
            ]
        ),
    )
    write(
        run_dir / "00_intake" / "business_expectations.md",
        "# Business Expectations\n\nNo user-supplied business expectations were provided in this demo run. The audit used the `financial_aml` profile and source-visible AML assistant behavior. In a user run, this file should capture intended use, prohibited use, approval gates, escalation rules, and business-line policies.",
    )
    write(
        run_dir / "00_intake" / "data_contracts_and_mdm.md",
        "# Data Contracts And MDM Expectations\n\nNo user-supplied MDM or source-system contract was provided in this demo run. In a user run, this file should name source-of-truth systems, entity definitions, join rules, data quality thresholds, retrieval boundaries, and redaction requirements.",
    )
    write(
        run_dir / "00_intake" / "domain_extension_reference.md",
        domain_extension_reference_text(audit, domain),
    )
    write(
        run_dir / "00_intake" / "governance_expectations.md",
        "# Governance Expectations\n\nNo user-supplied model-governance expectations were provided in this demo run. The audit still checks for source-visible model inventory, ownership, validation, monitoring, benchmarking, fairness, explainability, change management, access control, retention, continuity, and governance reporting evidence.",
    )
    write(
        run_dir / "00_intake" / "quality_profile_notes.md",
        f"# Quality Profile Notes\n\n- **Quality profile:** {domain or 'not specified'}\n- **Purpose:** Shape dataset readiness, golden-case coverage, severity expectations, and evaluation suites.\n\nFor this demo, the built-in AML investigation controls dataset is used as a starter proof set, not as a complete user-approved golden dataset.",
    )
    write(
        run_dir / "00_intake" / "source_snapshot_manifest.md",
        f"# Source Snapshot Manifest\n\n- **Target reviewed:** {target or audit.get('target', 'not specified')}\n- **Mutation policy:** Original target source should not be changed during assessment unless the user approves remediation.\n- **Snapshot note:** This demo run references the local workspace path rather than creating a copied source snapshot.",
    )


def render_observation(run_dir: Path, audit: dict[str, Any]) -> None:
    architecture = audit.get("architecture") or {}
    profile = audit.get("profile") or {}
    lines = [
        "# Agent Observation",
        "",
        "This is the plain-English understanding of the target before judging gaps or proposing changes.",
        "",
        f"- **Framework:** {audit.get('framework', 'not detected')}",
        f"- **Adapter mode:** {audit.get('adapter_mode', 'not specified')}",
        f"- **Business context:** {profile.get('business', 'not specified')}",
        f"- **Autonomy:** {profile.get('autonomy', 'not specified')}",
        f"- **External/customer-facing:** {profile.get('external_or_customer_facing', 'unknown')}",
        "",
        "## Observed Capabilities",
        "",
        f"- Tools: {architecture.get('has_tools')}",
        f"- Retrieval/RAG: {architecture.get('has_retrieval')}",
        f"- Handoffs/workflows: {architecture.get('has_handoffs')}",
        f"- Memory/session state: {architecture.get('has_memory')}",
        f"- Evals: {architecture.get('has_evals')}",
        "",
        "## Why This Matters",
        "",
        "The agent shape includes regulated financial data, retrieval, tool use, possible customer-impacting output, and AML-style approval gates. That means the control review must cover financial policy, prompt injection, sensitive data, toxicity/abuse, NFRs, evidence, and model governance.",
        "",
        "## Human Confirmation Needed",
        "",
        "Confirm whether this understanding matches the intended use of the agent. If the business purpose, autonomy level, source systems, or approval gates differ, update the intake files before treating the gap matrix as final.",
    ]
    write(run_dir / "01_observation" / "observation.md", "\n".join(lines))


def render_static_summary(run_dir: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Static Audit Summary",
        "",
        f"- **Framework:** {audit.get('framework', '')}",
        f"- **Decision:** {audit.get('decision', '')}",
        f"- **Risk tier:** {audit.get('risk_tier', '')}",
        f"- **Controls detected:** {len(audit.get('controls_present') or [])}",
        f"- **Findings:** {len(audit.get('findings') or [])}",
        "",
        "## Coverage Statement",
        "",
        audit.get("coverage_statement", ""),
        "",
        "## Blind Spots",
        "",
        *bullet_list(audit.get("blind_spots") or []),
    ]
    findings = audit.get("findings") or []
    lines.extend(["", "## Findings", ""])
    if findings:
        for finding in findings:
            control = finding.get("control") or {}
            lines.append(f"- **{finding.get('severity')} / {finding.get('status')}:** {control.get('id')} {control.get('name')} - {finding.get('recommendation')}")
    else:
        lines.append("No missing or weak controls were detected in the static first-pass audit.")
    write(run_dir / "02_static_audit" / "static_audit_summary.md", "\n".join(lines))


def render_gap_matrix(run_dir: Path, audit: dict[str, Any]) -> None:
    rows = gap_rows(audit)
    lines = [
        "# Gap Matrix",
        "",
        "This converts the required-control map into a human-reviewable table. JSON is kept as evidence; this file is for discussion and prioritization.",
        "",
        "| Requirement | Control | Status | Evidence | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['requirement']} | {row['control_id']} {row['control_name']} | {row['status']} | {row['evidence']} | {row['notes']} |"
        )
    write(run_dir / "03_gap_matrix" / "gap_matrix.md", "\n".join(lines))
    write_xlsx(
        run_dir / "03_gap_matrix" / "gap_matrix.xlsx",
        {
            "Gap Matrix": [
                ["Requirement", "Control ID", "Control Name", "Status", "Evidence", "Notes"],
                *[
                    [row["requirement"], row["control_id"], row["control_name"], row["status"], row["evidence"], row["notes"]]
                    for row in rows
                ],
            ]
        },
    )


def render_domain_overlay_diff(run_dir: Path, baseline_audit: dict[str, Any], domain_audit: dict[str, Any]) -> None:
    """Proof artifact for the domain-extension model: run the same target with and
    without --domain, and show exactly what the domain pack changed. This exists
    because a domain pack that changes nothing observable is indistinguishable from
    a domain pack that was never wired in — this file is the observable difference."""
    baseline_required = set((baseline_audit.get("required_controls") or {}).keys())
    domain_required = set((domain_audit.get("required_controls") or {}).keys())
    only_in_domain = sorted(domain_required - baseline_required)
    domain_name = domain_audit.get("domain") or "unknown"

    # A requirement can be "new" while every control it names was already required by
    # the baseline for a different reason (e.g. FIN-AML-002 requires C005, which FIN-001
    # already required for money movement). Only controls absent from every baseline
    # requirement are genuinely new coverage — don't call the rest "introduced".
    baseline_controls: set[str] = set()
    for controls in (baseline_audit.get("required_controls") or {}).values():
        baseline_controls.update(controls)

    genuinely_new_controls: set[str] = set()
    for requirement_id in only_in_domain:
        controls = domain_audit["required_controls"].get(requirement_id, [])
        genuinely_new_controls.update(c for c in controls if c not in baseline_controls)

    lines = [
        "# Domain Overlay Diff",
        "",
        f"Same target audited twice: once with no domain selected, once with `--domain {domain_name}`. "
        "This is the observable proof that selecting a domain changes the audit, not just the report narrative.",
        "",
        f"- **Baseline required requirement count:** {len(baseline_required)}",
        f"- **With `{domain_name}` required requirement count:** {len(domain_required)}",
        f"- **Requirements only present with the domain pack loaded:** {len(only_in_domain)}",
        f"- **Controls genuinely new to the run (not already required by baseline):** {len(genuinely_new_controls)} "
        f"({', '.join(sorted(genuinely_new_controls)) or 'none'})",
        "",
    ]
    if not only_in_domain:
        lines.append(
            "No additional requirements were introduced by this domain pack. Either no `regime_overlay.json` exists "
            f"for `{domain_name}`, or it is empty — check `domain_overlay_loaded` in the domain-scoped audit JSON."
        )
    else:
        domain_overlay_catalog = domain_audit.get("domain_overlay_catalog") or {}
        lines.extend(
            [
                "| Requirement | Controls Required By This Requirement | New Controls (Not Already Required By Baseline) | Severity Floor | Source |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for requirement_id in only_in_domain:
            controls = domain_audit["required_controls"].get(requirement_id, [])
            new_controls = [c for c in controls if c not in baseline_controls]
            catalog_entry = domain_overlay_catalog.get(requirement_id, {})
            severity = catalog_entry.get("severity", "see static_audit.json")
            source = catalog_entry.get("source", "domain pack")
            new_controls_cell = ", ".join(new_controls) if new_controls else "none — all already required by baseline"
            lines.append(f"| {requirement_id} | {', '.join(controls)} | {new_controls_cell} | {severity} | {source} |")
    write(run_dir / "03_gap_matrix" / "domain_overlay_diff.md", "\n".join(lines))


def render_change_plan(run_dir: Path, audit: dict[str, Any]) -> None:
    findings = audit.get("findings") or []
    lines = [
        "# Change Plan",
        "",
        "This file must be produced before changing target source code. It explains what should change, why, and what evidence should prove the fix.",
        "",
    ]
    if not findings:
        lines.extend(
            [
                "## Proposed Decision",
                "",
                "No source-code remediation is proposed from the static first-pass findings because the current static decision is `ship`.",
                "",
                "## Remaining Assurance Work",
                "",
                "- Confirm runtime callback order and hosted configuration.",
                "- Keep dynamic eval evidence attached to the run folder.",
                "- Confirm production IAM, approval queues, telemetry, and operating procedures if this moves beyond the reference demo.",
            ]
        )
    else:
        lines.extend(["## Proposed Remediations", ""])
        for finding in findings:
            control = finding.get("control") or {}
            lines.append(f"- **{control.get('id')} {control.get('name')}:** {finding.get('recommendation')}")
    write(run_dir / "04_change_plan" / "change_plan.md", "\n".join(lines))
    write(run_dir / "08_remediation" / "proposed_changes.md", "\n".join(lines))


def render_dataset_readiness(run_dir: Path, report: dict[str, Any] | None) -> None:
    if not report:
        write(run_dir / "05_dataset" / "readiness" / "dataset_readiness.md", "# Dataset Readiness\n\nNo dataset readiness report was supplied.")
        return
    quality = report.get("quality") or {}
    counts = quality.get("counts") or {}
    dimensions = quality.get("dimensions") or {}
    lines = [
        "# Dataset Readiness",
        "",
        f"- **Status:** {report.get('status')}",
        f"- **Schema status:** {report.get('schema_status')}",
        f"- **Rows:** {report.get('total_rows')}",
        f"- **Valid cases:** {report.get('valid_cases')}",
        f"- **DeepEval generation allowed:** {report.get('deepeval_generation_allowed')}",
        f"- **Quality score:** {quality.get('score')}",
        f"- **Readiness:** {quality.get('readiness')}",
        "",
        "## Case Counts",
        "",
        *[f"- **{key}:** {value}" for key, value in sorted(counts.items())],
        "",
        "## Quality Dimensions",
        "",
        *[f"- **{key}:** {value}" for key, value in sorted(dimensions.items())],
        "",
        "## Improvement Actions",
        "",
        *bullet_list(quality.get("improvement_actions") or []),
        "",
        "## User Questions",
        "",
        *bullet_list(report.get("user_questions") or report.get("client_questions") or []),
    ]
    write(run_dir / "05_dataset" / "readiness" / "dataset_readiness.md", "\n".join(lines))
    write_xlsx(
        run_dir / "05_dataset" / "readiness" / "dataset_readiness.xlsx",
        {
            "Summary": [
                ["Field", "Value"],
                ["Status", report.get("status")],
                ["Schema status", report.get("schema_status")],
                ["Rows", report.get("total_rows")],
                ["Valid cases", report.get("valid_cases")],
                ["DeepEval allowed", report.get("deepeval_generation_allowed")],
                ["Quality score", quality.get("score")],
                ["Readiness", quality.get("readiness")],
            ],
            "Dimensions": [["Dimension", "Score"], *[[key, value] for key, value in sorted(dimensions.items())]],
            "Actions": [["Improvement Action"], *[[item] for item in quality.get("improvement_actions") or []]],
        },
    )


def render_eval_summary(run_dir: Path, summary: dict[str, Any] | None, name: str = "eval_summary") -> None:
    if not summary:
        return
    lines = [
        f"# {name.replace('_', ' ').title()}",
        "",
        f"- **Total cases:** {summary.get('total')}",
        f"- **Passed:** {summary.get('passed')}",
        f"- **Failed:** {summary.get('failed')}",
        f"- **Pass rate:** {summary.get('pass_rate')}",
        f"- **Attack failure rate:** {summary.get('attack_failure_rate')}",
        f"- **Benign false positive rate:** {summary.get('benign_false_positive_rate')}",
        f"- **Dataset hash:** `{summary.get('dataset_hash')}`",
        f"- **Passed on structured evidence only:** {summary.get('passed_on_structured_evidence_only')}",
        f"- **Passed with text-fallback reliance:** {summary.get('passed_with_text_fallback_reliance')}",
        "",
        "\"Passed with text-fallback reliance\" means at least one substring/regex check contributed to the pass verdict "
        "(see `assertion_limitations` in the eval results JSONL) — treat those passes as smoke-tested, not semantically proven.",
        "",
        "## Suites",
        "",
        "| Suite | Passed | Failed | Total | Pass Rate | Structured-Only | Text-Fallback | Failed IDs |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for suite, row in sorted((summary.get("by_suite") or {}).items()):
        lines.append(
            f"| {suite} | {row.get('passed')} | {row.get('failed')} | {row.get('total')} | {row.get('pass_rate')} | "
            f"{row.get('passed_on_structured_evidence_only')} | {row.get('passed_with_text_fallback_reliance')} | "
            f"{', '.join(row.get('failed_ids') or [])} |"
        )
    write(run_dir / "06_evals" / "results" / f"{name}.md", "\n".join(lines))


def render_evidence(run_dir: Path) -> None:
    artifacts = sorted(
        path
        for path in run_dir.rglob("*")
        if path.is_file() and path.name not in {"hashes.jsonl", "evidence_manifest.json", "evidence_summary.md"}
    )
    rows = []
    for path in artifacts:
        rows.append({"path": str(path.relative_to(run_dir)), "sha256": file_hash(path)})
    (run_dir / "evidence").mkdir(parents=True, exist_ok=True)
    (run_dir / "evidence" / "evidence_manifest.json").write_text(json.dumps({"artifacts": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "evidence" / "hashes.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    lines = [
        "# Evidence Summary",
        "",
        "This folder contains hashable evidence for the run. JSON/JSONL is for reproducibility; the Markdown summaries are for human review.",
        "",
        f"- **Artifact count:** {len(rows)}",
        "",
        "| Artifact | SHA-256 |",
        "| --- | --- |",
    ]
    for row in rows:
        lines.append(f"| `{row['path']}` | `{row['sha256']}` |")
    write(run_dir / "evidence" / "evidence_summary.md", "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Render human-readable stage artifacts for an assurance run.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--audit-json", type=Path, required=True)
    parser.add_argument(
        "--baseline-audit-json",
        type=Path,
        help="Optional static_audit.json from a run of the same target with no --domain. "
        "When provided alongside --audit-json for a domain-scoped run, renders "
        "03_gap_matrix/domain_overlay_diff.md showing what the domain pack changed.",
    )
    parser.add_argument("--dataset-report", type=Path)
    parser.add_argument("--eval-summary", type=Path)
    parser.add_argument("--http-eval-summary", type=Path)
    parser.add_argument("--target", default="")
    parser.add_argument("--domain", default="")
    args = parser.parse_args()

    run_dir = args.run_dir
    audit = load_json(args.audit_json)
    if audit is None:
        raise SystemExit(f"audit JSON not found: {args.audit_json}")
    dataset_report = load_json(args.dataset_report)
    eval_summary = load_json(args.eval_summary)
    http_eval_summary = load_json(args.http_eval_summary)

    render_intake(run_dir, audit, args.target, args.domain)
    render_observation(run_dir, audit)
    render_static_summary(run_dir, audit)
    render_gap_matrix(run_dir, audit)
    baseline_audit = load_json(args.baseline_audit_json)
    if baseline_audit is not None:
        render_domain_overlay_diff(run_dir, baseline_audit, audit)
    render_change_plan(run_dir, audit)
    render_dataset_readiness(run_dir, dataset_report)
    render_eval_summary(run_dir, eval_summary, "eval_summary")
    render_eval_summary(run_dir, http_eval_summary, "http_eval_summary")
    render_evidence(run_dir)

    print(json.dumps({"status": "ok", "run_dir": str(run_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
