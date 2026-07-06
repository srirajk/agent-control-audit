#!/usr/bin/env python3
"""Render agent-control-audit reports as Markdown, XLSX, or DOCX.

The renderer intentionally uses a fixed report template and Python standard
library writers so Codex does not have to improvise client-facing report shape.
"""

from __future__ import annotations

import argparse
import html
import json
import zipfile
from pathlib import Path
from typing import Any


def load_json(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def severity_rank(value: str) -> int:
    return {"blocker": 4, "high": 3, "medium": 2, "low": 1}.get(value, 0)


def top_findings(audit: dict[str, Any], limit: int = 8) -> list[dict[str, Any]]:
    findings = list(audit.get("findings") or [])
    findings.sort(key=lambda row: (-severity_rank(row.get("severity", "")), row.get("control", {}).get("id", "")))
    return findings[:limit]


def control_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for control in audit.get("controls_present") or []:
        rows.append(
            {
                "control_id": control.get("control_id", ""),
                "name": control.get("name", ""),
                "type": control.get("type", ""),
                "location": control.get("location", ""),
                "status": control.get("status_hint", "present"),
                "can_block": str(control.get("can_block", "")),
                "adequacy_notes": control.get("adequacy_notes", ""),
            }
        )
    return rows


def finding_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for finding in audit.get("findings") or []:
        control = finding.get("control") or {}
        requirement = finding.get("requirement") or {}
        rows.append(
            {
                "finding_id": finding.get("finding_id", ""),
                "severity": finding.get("severity", ""),
                "status": finding.get("status", ""),
                "control_id": control.get("id", ""),
                "control_name": control.get("name", ""),
                "requirement": requirement.get("id", ""),
                "location": finding.get("location") or "",
                "recommendation": finding.get("recommendation", ""),
                "record_hash": finding.get("record_hash", ""),
            }
        )
    return rows


def summary_rows(audit: dict[str, Any], eval_summary: dict[str, Any] | None) -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = [
        ("Target", audit.get("target", "")),
        ("Framework", audit.get("framework", "")),
        ("Adapter status", audit.get("adapter_status", "")),
        ("Adapter mode", audit.get("adapter_mode", "")),
        ("Risk tier", audit.get("risk_tier", "")),
        ("Decision", audit.get("decision", "")),
        ("Finding count", len(audit.get("findings") or [])),
        ("Controls present", len(audit.get("controls_present") or [])),
    ]
    if eval_summary:
        rows.extend(
            [
                ("Eval total", eval_summary.get("total", "")),
                ("Eval passed", eval_summary.get("passed", "")),
                ("Eval failed", eval_summary.get("failed", "")),
                ("Eval pass rate", eval_summary.get("pass_rate", "")),
                ("Dataset hash", eval_summary.get("dataset_hash", "")),
            ]
        )
    return rows


def render_markdown(audit: dict[str, Any], eval_summary: dict[str, Any] | None) -> str:
    lines = [
        "# Agent Assurance Report",
        "",
        "## Executive Summary",
        "",
    ]
    for key, value in summary_rows(audit, eval_summary):
        lines.append(f"- **{key}:** {value}")
    lines.extend(["", "## Top Findings", ""])

    findings = top_findings(audit)
    if not findings:
        lines.append("No findings were detected in the static first-pass audit.")
    else:
        for finding in findings:
            control = finding.get("control") or {}
            lines.extend(
                [
                    f"### {finding.get('finding_id')} - {control.get('id')} {control.get('name')}",
                    "",
                    f"- **Severity:** {finding.get('severity')}",
                    f"- **Status:** {finding.get('status')}",
                    f"- **Location:** {finding.get('location') or 'not detected'}",
                    f"- **Recommendation:** {finding.get('recommendation')}",
                    f"- **Record hash:** `{finding.get('record_hash')}`",
                    "",
                ]
            )

    lines.extend(["## Eval Summary", ""])
    if eval_summary:
        for suite, row in sorted((eval_summary.get("by_suite") or {}).items()):
            lines.append(
                f"- **{suite}:** {row.get('passed')}/{row.get('total')} passed, "
                f"failed={row.get('failed')}, pass_rate={row.get('pass_rate')}"
            )
    else:
        lines.append("No eval summary was provided.")

    lines.extend(["", "## Controls Detected", ""])
    controls = control_rows(audit)
    if controls:
        lines.append("| Control | Name | Status | Location |")
        lines.append("| --- | --- | --- | --- |")
        for control in controls:
            lines.append(
                f"| {control['control_id']} | {control['name']} | {control['status']} | {control['location']} |"
            )
    else:
        lines.append("No source-visible controls were detected.")

    lines.extend(["", "## Coverage Statement", "", audit.get("coverage_statement", "")])
    blind_spots = audit.get("blind_spots") or []
    if blind_spots:
        lines.extend(["", "## Blind Spots", ""])
        for spot in blind_spots:
            lines.append(f"- {spot}")
    return "\n".join(lines) + "\n"


def xlsx_col(index: int) -> str:
    name = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def sheet_xml(rows: list[list[Any]]) -> str:
    body = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row):
            ref = f"{xlsx_col(col_index)}{row_index}"
            text = html.escape(str(value if value is not None else ""))
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        body.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(body)}</sheetData></worksheet>'
    )


def write_xlsx(path: Path, sheets: dict[str, list[list[Any]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet_entries = []
    rel_entries = []
    overrides = []
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + "".join(
                f'<Override PartName="/xl/worksheets/sheet{idx}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for idx in range(1, len(sheets) + 1)
            )
            + "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/></Relationships>',
        )
        for idx, (name, rows) in enumerate(sheets.items(), start=1):
            safe_name = html.escape(name[:31])
            sheet_entries.append(
                f'<sheet name="{safe_name}" sheetId="{idx}" '
                f'r:id="rId{idx}"/>'
            )
            rel_entries.append(
                f'<Relationship Id="rId{idx}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{idx}.xml"/>'
            )
            overrides.append(f"xl/worksheets/sheet{idx}.xml")
            archive.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml(rows))
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets>{"".join(sheet_entries)}</sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(rel_entries)
            + "</Relationships>",
        )


def render_xlsx(path: Path, audit: dict[str, Any], eval_summary: dict[str, Any] | None) -> None:
    summary = [["Field", "Value"]] + [[key, value] for key, value in summary_rows(audit, eval_summary)]
    findings = [["Finding ID", "Severity", "Status", "Control", "Name", "Requirement", "Location", "Recommendation", "Hash"]]
    findings += [
        [
            row["finding_id"],
            row["severity"],
            row["status"],
            row["control_id"],
            row["control_name"],
            row["requirement"],
            row["location"],
            row["recommendation"],
            row["record_hash"],
        ]
        for row in finding_rows(audit)
    ]
    controls = [["Control ID", "Name", "Type", "Location", "Status", "Can Block", "Adequacy Notes"]]
    controls += [
        [
            row["control_id"],
            row["name"],
            row["type"],
            row["location"],
            row["status"],
            row["can_block"],
            row["adequacy_notes"],
        ]
        for row in control_rows(audit)
    ]
    eval_rows = [["Suite", "Total", "Passed", "Failed", "Pass Rate", "Failed IDs"]]
    if eval_summary:
        eval_rows += [
            [
                suite,
                row.get("total", ""),
                row.get("passed", ""),
                row.get("failed", ""),
                row.get("pass_rate", ""),
                ", ".join(row.get("failed_ids") or []),
            ]
            for suite, row in sorted((eval_summary.get("by_suite") or {}).items())
        ]
    write_xlsx(path, {"Summary": summary, "Findings": findings, "Controls": controls, "Eval": eval_rows})


def paragraph(text: str, style: str | None = None) -> str:
    style_xml = f"<w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>" if style else ""
    safe = html.escape(text)
    return f"<w:p>{style_xml}<w:r><w:t xml:space=\"preserve\">{safe}</w:t></w:r></w:p>"


def render_docx(path: Path, audit: dict[str, Any], eval_summary: dict[str, Any] | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [paragraph("Agent Assurance Report", "Title"), paragraph("Executive Summary", "Heading1")]
    for key, value in summary_rows(audit, eval_summary):
        parts.append(paragraph(f"{key}: {value}"))
    parts.append(paragraph("Top Findings", "Heading1"))
    findings = top_findings(audit)
    if not findings:
        parts.append(paragraph("No findings were detected in the static first-pass audit."))
    for finding in findings:
        control = finding.get("control") or {}
        parts.append(paragraph(f"{finding.get('finding_id')} - {control.get('id')} {control.get('name')}", "Heading2"))
        parts.append(paragraph(f"Severity: {finding.get('severity')}"))
        parts.append(paragraph(f"Status: {finding.get('status')}"))
        parts.append(paragraph(f"Location: {finding.get('location') or 'not detected'}"))
        parts.append(paragraph(f"Recommendation: {finding.get('recommendation')}"))
    parts.append(paragraph("Coverage Statement", "Heading1"))
    parts.append(paragraph(audit.get("coverage_statement", "")))
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{"".join(parts)}<w:sectPr/></w:body></w:document>'
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/></Relationships>',
        )
        archive.writestr("word/document.xml", document)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render agent-control-audit reports")
    parser.add_argument("--audit-json", type=Path, required=True, help="Full static audit JSON")
    parser.add_argument("--eval-summary", type=Path, help="Optional eval summary JSON")
    parser.add_argument("--format", choices=["md", "xlsx", "docx"], required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    audit = load_json(args.audit_json)
    assert audit is not None
    eval_summary = load_json(args.eval_summary)
    if args.format == "md":
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(render_markdown(audit, eval_summary), encoding="utf-8")
    elif args.format == "xlsx":
        render_xlsx(args.out, audit, eval_summary)
    else:
        render_docx(args.out, audit, eval_summary)
    print(json.dumps({"status": "ok", "format": args.format, "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

