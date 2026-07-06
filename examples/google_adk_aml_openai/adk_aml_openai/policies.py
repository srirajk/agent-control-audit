"""Reusable policy checks shared by callbacks and tools."""

from __future__ import annotations

import logging

from .config import HANDOFF_ALLOWLIST, REQUIRED_CITATION_FIELDS, SENSITIVE_FIELDS

logger = logging.getLogger("adk_aml_openai")


def audit_log(case_id: str, event_type: str, reason_code: str, **extra: object) -> None:
    logger.info(
        "audit_trail case_id=%s event_type=%s reason_code=%s extra=%s",
        case_id,
        event_type,
        reason_code,
        extra,
    )


def redact(value: object) -> object:
    if isinstance(value, dict):
        return {key: ("<redacted>" if key in SENSITIVE_FIELDS else redact(val)) for key, val in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def authorize_tool_call(case_id: str, analyst_id: str | None = None) -> None:
    if analyst_id == "suspended":
        raise PermissionError("access_control: analyst is not allowed to execute this action")
    if not case_id.startswith("CASE-"):
        raise PermissionError("require_authorized_account: invalid case scope")


def validate_grounding(evidence_ids: list[str]) -> None:
    if not evidence_ids:
        raise ValueError("citation_required: material AML claims need source evidence")


def verify_citations(citation: object) -> None:
    if isinstance(citation, dict) and REQUIRED_CITATION_FIELDS.issubset(citation):
        return
    if isinstance(citation, str) and citation.strip():
        return
    raise ValueError("grounding_validation failed: citation evidence is required")


def check_untrusted_instruction_channels(text: str) -> None:
    lowered = text.lower()
    if any(marker in lowered for marker in ["ignore previous", "bypass", "reveal the system prompt", "exfiltrate"]):
        raise ValueError("prompt_injection: untrusted instruction detected")


def content_safety_policy(text: str) -> None:
    lowered = text.lower()
    if "harassment" in lowered or "self-harm" in lowered:
        raise ValueError("content_safety: abusive or unsafe request")


def handoff_authority(destination: str, payload: dict) -> dict:
    if destination not in HANDOFF_ALLOWLIST:
        raise PermissionError("handoff_destination_allowlist violation")
    payload_filter = {
        key: value
        for key, value in payload.items()
        if key in {"case_id", "risk_band", "evidence_ids", "route_reason"}
    }
    audit_log(
        str(payload_filter.get("case_id", "CASE-UNKNOWN")),
        "handoff_provenance",
        f"handoff_reason:{destination}",
        accepted_responsibility=destination,
        moved_fields=sorted(payload_filter),
    )
    return payload_filter
