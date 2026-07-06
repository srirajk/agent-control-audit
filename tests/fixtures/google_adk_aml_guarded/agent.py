"""Guarded Google ADK-style AML agent fixture.

This compact example shows the source-visible patterns the audit skill expects
when remediating an ADK 1.x AML investigation agent. It is a pattern library for
static discovery and discussion, not a production deployment.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Literal

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool, ToolContext
from pydantic import BaseModel, Field, field_validator


MODEL_VERSION = "openai/gpt-4o-mini"
ADK_VERSION = "adk-1.x"
dataset_hash = "sha256:example-adk-aml-golden-dataset"
random_seed = 7
eval_threshold = 0.9
temperature = 0
MAX_TOOL_CALLS = 12
MAX_TOKENS = 4096
MAX_RUNTIME_SECONDS = 60
KILL_SWITCH_ENABLED = False
RATE_LIMIT_PER_CASE = 25
RETRY_POLICY = {"max_retries": 2, "timeout_seconds": 20, "fallback": "manual_review"}

ALLOWED_RETRIEVAL_SOURCES = {
    "case_management",
    "kyc",
    "transactions",
    "sanctions",
    "adverse_media",
    "policy",
}
HANDOFF_ALLOWLIST = {
    "transaction_selection_agent",
    "due_diligence_agent",
    "case_analysis_agent",
    "sar_narrative_agent",
}
REQUIRED_CITATION_FIELDS = {"source_system", "record_id", "evidence_version"}
SENSITIVE_FIELDS = {"account_number", "ssn", "tax_id", "full_pan", "secret", "token"}

model_inventory = {
    "model_owner": "aml-product-owner",
    "control_owner": "model-risk-management",
    "risk_tier": "high",
}
intended_use = "AML analyst decision support for investigation drafting only"
prohibited_use = "No autonomous SAR filing, alert closure, customer contact, or client exit"
limitations = "Requires analyst approval and validated source evidence before disposition."
independent_validation = "second_line_effective_challenge_required"
data_lineage = ["case_management", "kyc", "transactions", "sanctions", "adverse_media"]
data_quality = {"freshness_hours": 24, "completeness_threshold": 0.98}
drift_monitoring = {"alert_mix_psi": 0.2, "analyst_override_rate_threshold": 0.15}
benchmark = "historical analyst disposition and rules baseline"
fairness = "segment checks by geography, customer type, PEP status, and risk band"
explainability = "reason_code plus citation evidence required for each recommendation"
change_management = "release_approval_required_for_prompt_tool_policy_dataset_threshold_changes"
vendor_risk = "model_provider and MCP dependency risk tracked"
RBAC = "builder_validator_approver_analyst_roles_segregated"
evidence_retention = "retain prompts, traces, approvals, and evals per legal_hold policy"
business_continuity = "rollback, fail_closed, RTO, and RPO documented"
model_governance_report = "monthly governance dashboard"

logger = logging.getLogger("aml_adk_guarded")


class AuditEvent(BaseModel):
    case_id: str
    event_type: str
    reason_code: str
    evidence_hash: str | None = None
    trace_id: str
    session_id: str


class TransactionSelectionRequest(BaseModel):
    case_id: str = Field(min_length=6, max_length=64)
    lookback_days: int = Field(ge=1, le=365)
    source_system: Literal["case_management", "transactions"]
    evidence_version: str = Field(min_length=3)

    @field_validator("case_id")
    @classmethod
    def semantic_argument_validation(cls, value: str) -> str:
        if not value.startswith("CASE-"):
            raise ValueError("case_id must be a governed case identifier")
        return value


class CaseActionRequest(BaseModel):
    case_id: str = Field(min_length=6, max_length=64)
    action: Literal["draft_sar", "rfi", "client_exit", "close_alert"]
    analyst_id: str = Field(min_length=3)
    evidence_ids: list[str] = Field(min_length=1)


def audit_log(event: AuditEvent) -> None:
    logger.info("audit_trail event=%s", event.model_dump())


def redact(value: object) -> object:
    if isinstance(value, dict):
        return {key: ("<redacted>" if key in SENSITIVE_FIELDS else redact(val)) for key, val in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def authorize_tool_call(case_id: str, analyst_id: str | None = None) -> None:
    if analyst_id == "suspended":
        raise PermissionError("access_control violation")
    if not case_id.startswith("CASE-"):
        raise PermissionError("require_authorized_account failed")


def validate_grounding(evidence_ids: list[str]) -> None:
    if not evidence_ids:
        raise ValueError("citation_required: material AML claims need source evidence")


def check_untrusted_instruction_channels(payload: str) -> None:
    markers = ["ignore previous", "bypass", "exfiltrate", "system prompt"]
    if any(marker in payload.lower() for marker in markers):
        raise ValueError("prompt_injection attempt detected")


def content_safety_policy(payload: str) -> None:
    if "harassment" in payload.lower() or "self-harm" in payload.lower():
        raise ValueError("toxicity or abuse content safety policy triggered")


def before_agent_callback(callback_context):
    prompt = str(getattr(callback_context, "user_content", ""))
    if "file sar now" in prompt.lower() or "contact customer" in prompt.lower():
        return {"blocked": True, "reason": "prohibited_use"}
    check_untrusted_instruction_channels(prompt)
    content_safety_policy(prompt)
    return None


def before_model_callback(callback_context, llm_request):
    if KILL_SWITCH_ENABLED:
        return {"blocked": True, "reason": "kill_switch"}
    llm_request.config = getattr(llm_request, "config", {}) or {}
    llm_request.config["max_tokens"] = MAX_TOKENS
    return None


def before_tool_callback(tool, args, tool_context: ToolContext):
    started = time.monotonic()
    if time.monotonic() - started > MAX_RUNTIME_SECONDS:
        raise TimeoutError("timeout fallback to manual_review")
    case_id = str(args.get("case_id", ""))
    analyst_id = args.get("analyst_id")
    authorize_tool_call(case_id, analyst_id)
    if args.get("action") in {"draft_sar", "rfi", "client_exit", "close_alert"}:
        tool_context.request_confirmation("Gate 3 analyst approval required before AML side effect")
    audit_log(
        AuditEvent(
            case_id=case_id,
            event_type="before_tool",
            reason_code="authorized_transition",
            trace_id="trace-adk-fixture",
            session_id="session-adk-fixture",
        )
    )
    return None


def after_tool_callback(tool, args, tool_context: ToolContext, result):
    return redact(result)


def after_agent_callback(callback_context, response):
    text = str(response)
    if "SAR filed" in text or "customer notified" in text:
        return {"blocked": True, "reason": "unsupported regulated action"}
    if "citation:" not in text.lower() and "manual review" not in text.lower():
        return {"blocked": True, "reason": "grounding_check failed"}
    return response


def handoff_authority(destination: str, payload: dict) -> dict:
    if destination not in HANDOFF_ALLOWLIST:
        raise PermissionError("handoff_destination_allowlist violation")
    payload_filter = {
        key: value
        for key, value in payload.items()
        if key in {"case_id", "risk_band", "evidence_ids", "route_reason"}
    }
    audit_log(
        AuditEvent(
            case_id=str(payload_filter.get("case_id", "CASE-UNKNOWN")),
            event_type="handoff_provenance",
            reason_code=f"handoff_reason:{destination}",
            trace_id="trace-adk-fixture",
            session_id="session-adk-fixture",
        )
    )
    return payload_filter


def select_transactions(
    case_id: str,
    lookback_days: int,
    source_system: Literal["case_management", "transactions"],
    evidence_version: str,
    tool_context: ToolContext,
) -> dict:
    request = TransactionSelectionRequest(
        case_id=case_id,
        lookback_days=lookback_days,
        source_system=source_system,
        evidence_version=evidence_version,
    )
    if source_system not in ALLOWED_RETRIEVAL_SOURCES:
        raise PermissionError("retrieval_scope violation")
    audit_log(
        AuditEvent(
            case_id=request.case_id,
            event_type="tool_execute",
            reason_code="transaction_selection",
            evidence_hash=dataset_hash,
            trace_id="trace-adk-fixture",
            session_id="session-adk-fixture",
        )
    )
    return {
        "case_id": request.case_id,
        "selected_transaction_ids": ["TX-100", "TX-200"],
        "citation": {"source_system": request.source_system, "record_id": "TX-100", "evidence_version": request.evidence_version},
        "reason_code": "large_reportable_transfer_pattern",
    }


def prepare_regulated_action(
    case_id: str,
    action: Literal["draft_sar", "rfi", "client_exit", "close_alert"],
    analyst_id: str,
    evidence_ids: list[str],
    tool_context: ToolContext,
) -> dict:
    request = CaseActionRequest(case_id=case_id, action=action, analyst_id=analyst_id, evidence_ids=evidence_ids)
    validate_grounding(request.evidence_ids)
    tool_context.request_confirmation("Gate 3 analyst approval required")
    return {
        "case_id": request.case_id,
        "status": "pending_approval",
        "action": request.action,
        "reason_code": "requires_human_in_the_loop",
        "citation": {"source_system": "case_management", "record_id": request.evidence_ids[0], "evidence_version": "v1"},
    }


root_agent = LlmAgent(
    name="aml_investigation_guarded",
    model=LiteLlm(model=MODEL_VERSION),
    instruction=(
        "Support AML analysts only. Do not autonomously file SARs, close alerts, "
        "contact customers, or recommend client exit without source-visible analyst approval. "
        "Use approved sources, cite evidence, redact sensitive data, and fall back to manual review."
    ),
    tools=[
        FunctionTool(select_transactions, require_confirmation=False),
        FunctionTool(prepare_regulated_action, require_confirmation=True),
    ],
    before_agent_callback=before_agent_callback,
    before_model_callback=before_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    after_agent_callback=after_agent_callback,
)

