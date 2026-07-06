"""ADK tools for AML evidence retrieval and regulated-action preparation."""

from google.adk.tools import ToolContext

from .config import ALLOWED_RETRIEVAL_SOURCES
from .policies import audit_log, validate_grounding, verify_citations
from .schemas import AMLToolRequest, RegulatedActionRequest

SOURCE_ALIASES = {
    "transaction": "transactions",
    "tx": "transactions",
    "sanction": "sanctions",
    "screening": "sanctions",
    "customer": "kyc",
}


def retrieve_case_evidence(
    case_id: str,
    source_system: str,
    evidence_version: str,
    tool_context: ToolContext,
) -> dict:
    normalized_source = source_system.strip().lower().replace(" ", "_")
    normalized_source = SOURCE_ALIASES.get(normalized_source, normalized_source)
    request = AMLToolRequest(case_id=case_id, source_system=normalized_source, evidence_version=evidence_version)
    if request.source_system not in ALLOWED_RETRIEVAL_SOURCES:
        raise PermissionError("retrieval_scope: source system is not allowed")
    audit_log(request.case_id, "tool_execute", "retrieve_case_evidence", source_system=request.source_system)
    result = {
        "case_id": request.case_id,
        "risk_band": "high",
        "evidence": [
            {"source_system": "kyc", "record_id": "KYC-7", "evidence_version": request.evidence_version},
            {"source_system": "transactions", "record_id": "TX-9", "evidence_version": request.evidence_version},
            {"source_system": "sanctions", "record_id": "SAN-2", "evidence_version": request.evidence_version},
        ],
        "citation": "KYC-7; TX-9; SAN-2",
    }
    verify_citations(result["citation"])
    return result


def prepare_regulated_action(
    case_id: str,
    action: str,
    analyst_id: str,
    evidence_ids: list[str],
    tool_context: ToolContext,
) -> dict:
    request = RegulatedActionRequest(
        case_id=case_id,
        action=action,
        analyst_id=analyst_id,
        evidence_ids=evidence_ids,
    )
    validate_grounding(request.evidence_ids)
    tool_context.request_confirmation("Analyst approval required before regulated AML action")
    audit_log(request.case_id, "approval_requested", f"action:{request.action}", evidence_ids=request.evidence_ids)
    return {
        "case_id": request.case_id,
        "action": request.action,
        "status": "pending_approval",
        "reason_code": "human_in_the_loop_required",
        "citation": request.evidence_ids,
    }
