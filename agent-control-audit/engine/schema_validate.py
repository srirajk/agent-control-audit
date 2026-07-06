"""Schema validation for regime requirement files (regimes/financial.json,
domain_extensions/<domain>/regime_overlay.json).

Domain packs rot fast without this: a malformed overlay (missing field, wrong
type, a `requires_controls` entry pointing at a control_id that doesn't exist)
should fail loud at load time, per SKILL.md's Fail-Loud Gates, rather than
crash opaquely deep in the mapper or silently produce an incomplete audit.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SEVERITY_FLOORS = {"blocker", "high", "medium", "low"}
CONTROL_ID_PATTERN = re.compile(r"^### (C\d{3})\b", re.MULTILINE)
REQUIRED_FIELDS = {"requirement_text", "requires_controls", "severity_floor", "source"}


def load_control_ids(control_catalog_path: Path) -> set[str]:
    text = control_catalog_path.read_text(encoding="utf-8")
    return set(CONTROL_ID_PATTERN.findall(text))


def validate_regime_file(entries: dict[str, Any], control_ids: set[str], *, source_label: str) -> list[str]:
    """Validate a loaded regime/overlay requirements mapping. Returns a list of
    human-readable errors; empty means valid."""
    errors: list[str] = []
    if not isinstance(entries, dict):
        return [f"{source_label}: file must contain a JSON object of requirement_id -> requirement"]

    for requirement_id, entry in entries.items():
        prefix = f"{source_label}:{requirement_id}"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: requirement must be an object")
            continue

        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            errors.append(f"{prefix}: missing fields {sorted(missing)}")
            continue

        if not isinstance(entry["requirement_text"], str) or not entry["requirement_text"].strip():
            errors.append(f"{prefix}: requirement_text must be a non-empty string")

        if not isinstance(entry["source"], str) or not entry["source"].strip():
            errors.append(f"{prefix}: source must be a non-empty string")

        if entry["severity_floor"] not in SEVERITY_FLOORS:
            errors.append(f"{prefix}: severity_floor {entry['severity_floor']!r} must be one of {sorted(SEVERITY_FLOORS)}")

        controls = entry["requires_controls"]
        if not isinstance(controls, list) or not controls:
            errors.append(f"{prefix}: requires_controls must be a non-empty list")
            continue
        for control_id in controls:
            if control_id not in control_ids:
                errors.append(f"{prefix}: requires_controls references unknown control_id {control_id!r}")

    return errors
