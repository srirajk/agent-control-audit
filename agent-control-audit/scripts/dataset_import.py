#!/usr/bin/env python3
"""Normalize and validate user-supplied golden datasets.

Supported input: JSONL, JSON array, JSON object with "cases", CSV, and XLSX.
Output: canonical JSONL plus a structured report when requested.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import eval_runner


REQUIRED_FIELDS = {"id", "suite", "input", "expected", "must_not", "severity", "source"}
LIST_FIELDS = {
    "must_not",
    "allowed_tools",
    "forbidden_tools",
    "required_phrases",
    "forbidden_phrases",
    "expected_citations",
}
JSON_FIELDS = {"metadata", "user_context"}
ALLOWED_SEVERITIES = {"blocker", "high", "medium", "low"}
HIGH_RISK_SEVERITIES = {"blocker", "high"}
ALLOW_EXPECTED = {"allow", "answer", "answer_with_citations", "answer_with_citations_or_insufficient_evidence"}
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_QUALITY_PROFILE_PATH = SKILL_DIR / "evals" / "quality_profiles.json"
DEFAULT_QUALITY_PROFILE = {
    "profile_id": "default",
    "recommended_suites": [
        "jailbreak_direct",
        "prompt_injection_indirect",
        "unauthorized_tool_use",
        "sensitive_data_leakage",
        "grounding_failures",
        "toxicity_and_abuse",
        "nfr_resilience",
        "benign_false_positives",
    ],
    "owner_metadata_keys": ["owner", "approver", "reviewer", "approved_by"],
    "version_metadata_keys": ["version", "dataset_version", "approved_at", "reviewed_at"],
    "score_weights": {
        "schema_validity": 0.25,
        "machine_checkability": 0.20,
        "high_risk_machine_checkability": 0.20,
        "recommended_suite_coverage": 0.15,
        "benign_and_adversarial_balance": 0.10,
        "ownership_traceability": 0.05,
        "version_traceability": 0.05,
    },
    "readiness_thresholds": {
        "eval_ready_score": 70,
        "governance_grade_score": 85,
        "governance_metadata_ratio": 0.8,
    },
}
MACHINE_CHECK_FIELDS = (
    "must_not",
    "forbidden_tools",
    "forbidden_phrases",
    "required_phrases",
    "expected_citations",
    "max_tool_calls",
)

ALIASES = {
    "case_id": "id",
    "test_id": "id",
    "eval_id": "id",
    "name": "id",
    "category": "suite",
    "test_suite": "suite",
    "eval_suite": "suite",
    "risk_suite": "suite",
    "scenario": "suite",
    "prompt": "input",
    "question": "input",
    "user_input": "input",
    "task": "input",
    "expected_behavior": "expected",
    "expected_outcome": "expected",
    "expected_label": "expected",
    "label": "expected",
    "policy_expected": "expected",
    "forbidden_outcomes": "must_not",
    "negative_assertions": "must_not",
    "must_not_do": "must_not",
    "risk": "severity",
    "risk_level": "severity",
    "severity_level": "severity",
    "origin": "source",
    "source_type": "source",
    "retrieved_context": "retrieved_doc",
    "retrieved_document": "retrieved_doc",
    "source_text": "retrieved_doc",
    "tool_output": "tool_result",
    "context_json": "user_context",
    "account_context": "user_context",
    "disallowed_tools": "forbidden_tools",
}


def merge_profile(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key == "extends":
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def load_quality_profile(profile_name: str, profile_path: Path | None = None) -> dict[str, Any]:
    profiles: dict[str, Any] = {}
    if DEFAULT_QUALITY_PROFILE_PATH.exists():
        loaded = json.loads(DEFAULT_QUALITY_PROFILE_PATH.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"quality profile file must contain an object: {DEFAULT_QUALITY_PROFILE_PATH}")
        profiles = loaded
    if profile_path:
        loaded = json.loads(profile_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"quality profile file must contain an object: {profile_path}")
        profiles.update(loaded)

    resolved: dict[str, dict[str, Any]] = {}

    def resolve(name: str, seen: set[str] | None = None) -> dict[str, Any]:
        seen = seen or set()
        if name in resolved:
            return resolved[name]
        if name in seen:
            raise ValueError(f"quality profile inheritance cycle: {' -> '.join(sorted(seen | {name}))}")
        raw = profiles.get(name)
        if raw is None:
            if name == "default":
                resolved[name] = DEFAULT_QUALITY_PROFILE
                return resolved[name]
            available = ", ".join(sorted(set(profiles) | {"default"}))
            raise ValueError(f"quality profile {name!r} not found. Available profiles: {available}")
        if not isinstance(raw, dict):
            raise ValueError(f"quality profile {name!r} must be an object")
        base_name = raw.get("extends")
        base = resolve(str(base_name), seen | {name}) if base_name else DEFAULT_QUALITY_PROFILE
        resolved[name] = merge_profile(base, raw)
        resolved[name].setdefault("profile_id", name)
        return resolved[name]

    return resolve(profile_name)


def canonical_header(value: str) -> str:
    header = value.strip().lower()
    header = re.sub(r"[^a-z0-9]+", "_", header).strip("_")
    return ALIASES.get(header, header)


def clean_cell(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def parse_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            if not isinstance(parsed, list):
                raise ValueError(f"expected list, got {type(parsed).__name__}")
            return parsed
        return [part.strip() for part in stripped.split(",") if part.strip()]
    return [value]


def parse_json_object(value: Any) -> dict[str, Any]:
    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValueError(f"expected object, got {type(parsed).__name__}")
        return parsed
    raise ValueError(f"expected object-like value, got {type(value).__name__}")


def load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        records: list[dict[str, Any]] = []
        for row in reader:
            record: dict[str, Any] = {}
            for key, value in row.items():
                if key is None:
                    extras = [clean_cell(item) for item in value or []]
                    extras = [item for item in extras if item is not None]
                    if extras:
                        record["extra_columns"] = extras
                    continue
                record[canonical_header(key)] = clean_cell(value)
            records.append(record)
        return records


def xml_texts(element: ElementTree.Element, tag: str) -> list[str]:
    return [node.text or "" for node in element.iter() if node.tag.endswith(tag)]


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root:
        if item.tag.endswith("si"):
            values.append("".join(xml_texts(item, "t")))
    return values


def workbook_sheets(archive: zipfile.ZipFile) -> list[dict[str, str]]:
    workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {}
    for rel in rels:
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rel_id and target:
            if target.startswith("/"):
                path = target.lstrip("/")
            else:
                path = "xl/" + target
            rel_targets[rel_id] = path

    sheets: list[dict[str, str]] = []
    for node in workbook.iter():
        if not node.tag.endswith("sheet"):
            continue
        rel_id = node.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        if rel_id and rel_id in rel_targets:
            sheets.append({"name": node.attrib.get("name", ""), "path": rel_targets[rel_id]})
    return sheets


def column_index(cell_ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def xlsx_cell_value(cell: ElementTree.Element, shared_strings: list[str]) -> Any:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(xml_texts(cell, "t"))

    value_node = next((child for child in cell if child.tag.endswith("v")), None)
    if value_node is None or value_node.text is None:
        return None
    raw = value_node.text

    if cell_type == "s":
        try:
            return shared_strings[int(raw)]
        except (ValueError, IndexError):
            return raw
    if cell_type == "b":
        return raw == "1"
    return raw


def load_xlsx(path: Path, sheet: str | None) -> list[dict[str, Any]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings = read_shared_strings(archive)
        sheets = workbook_sheets(archive)
        if not sheets:
            return []
        selected = sheets[0]
        if sheet:
            matches = [candidate for candidate in sheets if candidate["name"] == sheet]
            if not matches:
                available = ", ".join(candidate["name"] for candidate in sheets)
                raise ValueError(f"sheet {sheet!r} not found. Available sheets: {available}")
            selected = matches[0]

        root = ElementTree.fromstring(archive.read(selected["path"]))
        parsed_rows: list[list[Any]] = []
        for row in root.iter():
            if not row.tag.endswith("row"):
                continue
            values: list[Any] = []
            next_index = 0
            for cell in row:
                if not cell.tag.endswith("c"):
                    continue
                ref = cell.attrib.get("r", "")
                index = column_index(ref) if ref else next_index
                while len(values) <= index:
                    values.append(None)
                values[index] = clean_cell(xlsx_cell_value(cell, shared_strings))
                next_index = index + 1
            if any(value is not None and value != "" for value in values):
                parsed_rows.append(values)

    if not parsed_rows:
        return []
    headers = [canonical_header(str(cell)) if cell is not None else "" for cell in parsed_rows[0]]
    records: list[dict[str, Any]] = []
    for row in parsed_rows[1:]:
        record = {}
        for idx, value in enumerate(row):
            if idx >= len(headers) or not headers[idx]:
                continue
            record[headers[idx]] = value
        if any(value is not None and value != "" for value in record.values()):
            records.append(record)
    return records


def load_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return []
    if path.suffix.lower() == ".jsonl":
        rows: list[dict[str, Any]] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
        return rows
    if stripped.startswith("[") or (stripped.startswith("{") and "\n" not in stripped):
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            rows = parsed.get("cases")
            if not isinstance(rows, list):
                raise ValueError("JSON object input must contain a list field named 'cases'")
            return rows
        if isinstance(parsed, list):
            return parsed
        raise ValueError("JSON input must be an array or object with 'cases'")

    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
    return rows


def load_input(path: Path, sheet: str | None = None) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv(path)
    if suffix in {".xlsx", ".xlsm", ".xltx"}:
        return load_xlsx(path, sheet)
    if suffix == ".xls":
        raise ValueError("Legacy .xls is not supported directly. Ask the user for .xlsx, CSV, JSON, or JSONL.")
    rows = load_json_or_jsonl(path)
    return [{canonical_header(str(key)): value for key, value in row.items()} for row in rows]


def normalize_case(row: dict[str, Any], row_number: int, default_source: str) -> tuple[dict[str, Any], list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    case: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    client_columns: dict[str, Any] = {}

    for raw_key, raw_value in row.items():
        key = canonical_header(str(raw_key))
        value = clean_cell(raw_value)
        if value is None:
            continue
        if key in REQUIRED_FIELDS or key in LIST_FIELDS or key in JSON_FIELDS or key in {
            "retrieved_doc",
            "tool_result",
            "allowed_tools",
            "forbidden_tools",
            "required_phrases",
            "forbidden_phrases",
            "expected_citations",
            "max_tool_calls",
        }:
            case[key] = value
        else:
            client_columns[key] = value

    if "source" not in case:
        case["source"] = default_source
        warnings.append("source missing; defaulted to client_golden")
    if "must_not" not in case:
        case["must_not"] = []

    for field in LIST_FIELDS:
        if field in case:
            try:
                case[field] = parse_list(case[field])
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                issues.append(f"{field} is not a valid list: {exc}")

    for field in JSON_FIELDS:
        if field in case:
            try:
                case[field] = parse_json_object(case[field])
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                issues.append(f"{field} is not a valid JSON object: {exc}")

    if "metadata" in case and isinstance(case["metadata"], dict):
        metadata.update(case["metadata"])
    if client_columns:
        metadata["client_columns"] = client_columns
    metadata["source_row"] = row_number
    metadata.setdefault("normalized_by", "agent-control-audit/scripts/dataset_import.py")
    case["metadata"] = metadata

    missing = sorted(REQUIRED_FIELDS - set(case))
    for field in missing:
        issues.append(f"missing required field: {field}")

    severity = str(case.get("severity", "")).lower()
    if "severity" in case:
        case["severity"] = severity
    if severity and severity not in ALLOWED_SEVERITIES:
        issues.append(f"severity must be one of {sorted(ALLOWED_SEVERITIES)}, got {case.get('severity')!r}")

    if not isinstance(case.get("must_not"), list):
        issues.append("must_not must be a list")

    expected = str(case.get("expected", "")).lower()
    has_machine_check = any(case.get(field) for field in MACHINE_CHECK_FIELDS)
    if severity in HIGH_RISK_SEVERITIES and not has_machine_check:
        issues.append(
            "high-risk case needs at least one machine-checkable assertion: must_not, forbidden_tools, "
            "forbidden_phrases, required_phrases, expected_citations, or max_tool_calls"
        )

    return case, issues, warnings


def has_machine_check(case: dict[str, Any]) -> bool:
    return any(case.get(field) for field in MACHINE_CHECK_FIELDS)


def quality_for(
    cases: list[dict[str, Any]],
    row_issues: list[dict[str, Any]],
    quality_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = quality_profile or DEFAULT_QUALITY_PROFILE
    recommended_suites = set(profile.get("recommended_suites") or DEFAULT_QUALITY_PROFILE["recommended_suites"])
    owner_keys = set(profile.get("owner_metadata_keys") or DEFAULT_QUALITY_PROFILE["owner_metadata_keys"])
    version_keys = set(profile.get("version_metadata_keys") or DEFAULT_QUALITY_PROFILE["version_metadata_keys"])
    weights = dict(DEFAULT_QUALITY_PROFILE["score_weights"])
    weights.update(profile.get("score_weights") or {})
    thresholds = dict(DEFAULT_QUALITY_PROFILE["readiness_thresholds"])
    thresholds.update(profile.get("readiness_thresholds") or {})

    total_rows = len(cases) + len(row_issues)
    suite_counter = Counter(str(case.get("suite")) for case in cases)
    severity_counter = Counter(str(case.get("severity")) for case in cases)
    expected_counter = Counter(str(case.get("expected")) for case in cases)
    high_risk_cases = [case for case in cases if case.get("severity") in HIGH_RISK_SEVERITIES]
    machine_checkable_cases = [case for case in cases if has_machine_check(case)]
    high_risk_machine_checkable = [case for case in high_risk_cases if has_machine_check(case)]
    owner_cases = [
        case
        for case in cases
        if isinstance(case.get("metadata"), dict)
        and any(key in case["metadata"] for key in owner_keys)
    ]
    versioned_cases = [
        case
        for case in cases
        if isinstance(case.get("metadata"), dict)
        and any(key in case["metadata"] for key in version_keys)
    ]
    benign_cases = [
        case
        for case in cases
        if case.get("suite") == "benign_false_positives" or str(case.get("expected")) in ALLOW_EXPECTED
    ]
    adversarial_cases = [case for case in cases if case not in benign_cases]
    missing_recommended = sorted(recommended_suites - set(suite_counter))

    schema_ratio = (len(cases) / total_rows) if total_rows else 0.0
    machine_ratio = (len(machine_checkable_cases) / len(cases)) if cases else 0.0
    high_risk_machine_ratio = (len(high_risk_machine_checkable) / len(high_risk_cases)) if high_risk_cases else 1.0
    ownership_ratio = (len(owner_cases) / len(cases)) if cases else 0.0
    version_ratio = (len(versioned_cases) / len(cases)) if cases else 0.0
    suite_ratio = (len(set(suite_counter) & recommended_suites) / len(recommended_suites)) if recommended_suites else 1.0
    benign_balance = 1.0 if benign_cases and adversarial_cases else 0.0
    dimensions = {
        "schema_validity": schema_ratio,
        "machine_checkability": machine_ratio,
        "high_risk_machine_checkability": high_risk_machine_ratio,
        "recommended_suite_coverage": suite_ratio,
        "benign_and_adversarial_balance": benign_balance,
        "ownership_traceability": ownership_ratio,
        "version_traceability": version_ratio,
    }

    score = round(
        100
        * sum(float(weights.get(name, 0.0)) * value for name, value in dimensions.items())
    )

    if row_issues:
        readiness = "needs_client_input"
    elif not cases:
        readiness = "empty"
    elif (
        score >= int(thresholds["governance_grade_score"])
        and not missing_recommended
        and ownership_ratio >= float(thresholds["governance_metadata_ratio"])
        and version_ratio >= float(thresholds["governance_metadata_ratio"])
    ):
        readiness = "governance_grade_candidate"
    elif score >= int(thresholds["eval_ready_score"]) and high_risk_machine_ratio == 1.0:
        readiness = "eval_ready"
    else:
        readiness = "structurally_valid_but_coverage_thin"

    improvement_actions: list[str] = []
    if row_issues:
        improvement_actions.append("Resolve row issues before generating DeepEval tests.")
    if missing_recommended:
        improvement_actions.append("Add coverage for missing recommended suites: " + ", ".join(missing_recommended) + ".")
    if machine_ratio < 0.8:
        improvement_actions.append("Add machine-checkable assertions such as forbidden tools, required phrases, citations, max tool calls, or precise must_not outcomes.")
    if high_risk_machine_ratio < 1.0:
        improvement_actions.append("Every blocker/high case needs at least one deterministic assertion.")
    if not benign_cases:
        improvement_actions.append("Add benign false-positive cases so guardrails are tested for overblocking.")
    if ownership_ratio < 0.8:
        improvement_actions.append("Add owner/reviewer/approver metadata for governance traceability.")
    if version_ratio < 0.8:
        improvement_actions.append("Add dataset version or reviewed/approved date metadata.")

    return {
        "profile": {
            "id": profile.get("profile_id", "default"),
            "description": profile.get("description"),
            "recommended_suites": sorted(recommended_suites),
        },
        "readiness": readiness,
        "score": score,
        "dimensions": {name: round(value, 3) for name, value in dimensions.items()},
        "counts": {
            "total_rows": total_rows,
            "valid_cases": len(cases),
            "invalid_cases": len(row_issues),
            "high_risk_cases": len(high_risk_cases),
            "machine_checkable_cases": len(machine_checkable_cases),
            "benign_cases": len(benign_cases),
            "adversarial_cases": len(adversarial_cases),
        },
        "suite_distribution": dict(sorted(suite_counter.items())),
        "severity_distribution": dict(sorted(severity_counter.items())),
        "expected_distribution": dict(sorted(expected_counter.items())),
        "missing_recommended_suites": missing_recommended,
        "improvement_actions": improvement_actions,
    }


def report_for(
    input_path: Path,
    out_path: Path,
    cases: list[dict[str, Any]],
    row_issues: list[dict[str, Any]],
    row_warnings: list[dict[str, Any]],
    quality_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    missing_counter: Counter[str] = Counter()
    for row in row_issues:
        for issue in row["issues"]:
            if issue.startswith("missing required field: "):
                missing_counter[issue.rsplit(": ", 1)[1]] += 1

    questions = []
    for field, count in sorted(missing_counter.items()):
        questions.append(f"Please provide `{field}` for {count} row(s).")
    if any("machine-checkable assertion" in issue for row in row_issues for issue in row["issues"]):
        questions.append(
            "For high-risk cases, please provide forbidden tools/phrases, required phrases, citations, max tool calls, or precise must_not outcomes."
        )

    quality = quality_for(cases, row_issues, quality_profile)
    status = "needs_client_input" if row_issues else quality["readiness"]
    normalized_available = not row_issues
    deepeval_generation_allowed = quality["readiness"] in {"eval_ready", "governance_grade_candidate"}
    return {
        "status": status,
        "schema_status": "ok" if normalized_available else "needs_client_input",
        "deepeval_generation_allowed": deepeval_generation_allowed,
        "input": str(input_path),
        "normalized_out": str(out_path) if normalized_available else None,
        "total_rows": len(cases) + len(row_issues),
        "valid_cases": len(cases),
        "invalid_cases": len(row_issues),
        "missing_required_by_field": dict(sorted(missing_counter.items())),
        "row_issues": row_issues,
        "row_warnings": row_warnings,
        "user_questions": questions,
        "quality": quality,
    }


def write_jsonl(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case, sort_keys=True) + "\n")


def write_report(path: Path | None, report: dict[str, Any]) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize and validate user golden datasets")
    parser.add_argument("--in", dest="input_path", type=Path, required=True, help="User dataset path")
    parser.add_argument("--out", type=Path, required=True, help="Output canonical JSONL path")
    parser.add_argument("--report", type=Path, help="Output validation report JSON path")
    parser.add_argument("--sheet", help="XLSX sheet name. Defaults to the active sheet.")
    parser.add_argument("--default-source", default="client_golden", help="Source when a row omits source")
    parser.add_argument(
        "--quality-profile",
        default="financial",
        help="Quality profile name from evals/quality_profiles.json, such as default, financial, financial_aml, financial_payments, or financial_lending.",
    )
    parser.add_argument(
        "--quality-profile-file",
        type=Path,
        help="Optional custom quality profile JSON file. Defaults to evals/quality_profiles.json.",
    )
    args = parser.parse_args()

    quality_profile = load_quality_profile(args.quality_profile, args.quality_profile_file)
    rows = load_input(args.input_path, args.sheet)
    valid_cases: list[dict[str, Any]] = []
    row_issues: list[dict[str, Any]] = []
    row_warnings: list[dict[str, Any]] = []

    for row_number, row in enumerate(rows, start=2 if args.input_path.suffix.lower() in {".csv", ".xlsx", ".xlsm", ".xltx"} else 1):
        case, issues, warnings = normalize_case(row, row_number, args.default_source)
        if warnings:
            row_warnings.append({"row": row_number, "id": case.get("id"), "warnings": warnings})
        if issues:
            row_issues.append({"row": row_number, "id": case.get("id"), "issues": issues})
        else:
            valid_cases.append(case)

    duplicate_ids = sorted(case_id for case_id, count in Counter(case["id"] for case in valid_cases).items() if count > 1)
    if duplicate_ids:
        for duplicate_id in duplicate_ids:
            row_issues.append({"row": None, "id": duplicate_id, "issues": ["duplicate id"]})
        valid_cases = [case for case in valid_cases if case["id"] not in set(duplicate_ids)]

    report = report_for(args.input_path, args.out, valid_cases, row_issues, row_warnings, quality_profile)
    write_report(args.report, report)

    if row_issues:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    temp_path = args.out.with_suffix(args.out.suffix + ".tmp")
    write_jsonl(temp_path, valid_cases)
    eval_runner.load_cases([temp_path])
    temp_path.replace(args.out)
    report["normalized_out"] = str(args.out)
    write_report(args.report, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "schema_status": report["schema_status"],
                "deepeval_generation_allowed": report["deepeval_generation_allowed"],
                "cases": len(valid_cases),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
