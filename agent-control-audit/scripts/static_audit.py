#!/usr/bin/env python3
"""Static first-pass auditor for agent-control-audit.

This script intentionally stays conservative. It detects framework routes,
extracts obvious source-visible controls, derives a baseline required set, and
emits hashable JSON evidence. Codex should still perform the final adequacy
review using the skill resources.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ENGINE_DIR = SKILL_DIR / "engine"
REGIMES_DIR = SKILL_DIR / "regimes"
DOMAIN_EXTENSIONS_DIR = SKILL_DIR.parent / "domain_extensions"
sys.path.insert(0, str(ENGINE_DIR))

import schema_validate  # noqa: E402


TEXT_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".txt",
}

CONTROL_HEADING_PATTERN = re.compile(r"^### (C\d{3}) (.+)$", re.MULTILINE)


def load_control_names(control_catalog_path: Path) -> dict[str, str]:
    text = control_catalog_path.read_text(encoding="utf-8")
    return {match.group(1): match.group(2).strip() for match in CONTROL_HEADING_PATTERN.finditer(text)}


def reshape_requirements(data: dict[str, Any], control_ids: set[str], source_label: str) -> dict[str, dict[str, Any]]:
    """Validate a requirement_id -> requirement mapping with engine/schema_validate.py
    and reshape it into the {"text", "controls", "severity", "source"} form this
    module uses internally. A malformed regime or domain-overlay file fails loud
    here rather than crashing opaquely downstream or silently omitting requirements."""
    errors = schema_validate.validate_regime_file(data, control_ids, source_label=source_label)
    if errors:
        raise ValueError(f"invalid regime file {source_label}:\n  " + "\n  ".join(errors))
    return {
        requirement_id: {
            "text": entry["requirement_text"],
            "controls": entry["requires_controls"],
            "severity": entry["severity_floor"],
            "source": entry["source"],
        }
        for requirement_id, entry in data.items()
    }


def load_requirements(regime_path: Path, control_ids: set[str]) -> dict[str, dict[str, Any]]:
    """Load a flat requirement_id -> requirement mapping (the domain-overlay shape)."""
    data = json.loads(regime_path.read_text(encoding="utf-8"))
    return reshape_requirements(data, control_ids, str(regime_path))


def load_base_regime(regime_path: Path, control_ids: set[str]) -> dict[str, dict[str, Any]]:
    """Load the author-approved base regime file. Unlike a domain overlay, this file
    must carry an explicit {"author_approved": true, "requirements": {...}} envelope.
    SKILL.md's Fail-Loud Gates require stopping when this regime is missing, empty,
    or not author-approved — this is that check enforced by the runtime loader
    itself, not just prose the LLM has to remember to check."""
    payload = json.loads(regime_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "requirements" not in payload:
        raise ValueError(f"{regime_path}: base regime file must be an object with an 'author_approved' flag and a 'requirements' object")
    if payload.get("author_approved") is not True:
        raise ValueError(f"{regime_path}: author_approved must be true; this regime is not cleared for use")
    return reshape_requirements(payload["requirements"], control_ids, str(regime_path))


CONTROL_NAMES = load_control_names(ENGINE_DIR / "control_catalog.md")
CONTROL_IDS = set(CONTROL_NAMES)
REQUIREMENTS = load_base_regime(REGIMES_DIR / "financial.json", CONTROL_IDS)

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "blocker": 4}


def load_domain_overlay(domain: str) -> tuple[dict[str, dict[str, Any]], Path | None]:
    """Resolve domain_extensions/<domain>/regime_overlay.json if present. Returns
    (overlay_requirements, path_or_None). Overlay requirement ids apply
    unconditionally when this domain is selected — the domain selection itself is
    the applicability condition, unlike the base financial regime's harm-surface
    conditions in derive_required(). An overlay must not reuse a base regime
    requirement id: that would silently replace (not add to) a base requirement's
    controls/severity/provenance wherever compare_controls and derive_required look
    it up by id, which could weaken an existing blocker-level requirement without
    anyone noticing."""
    overlay_path = DOMAIN_EXTENSIONS_DIR / domain / "regime_overlay.json"
    if not overlay_path.exists():
        return {}, None
    overlay_requirements = load_requirements(overlay_path, CONTROL_IDS)
    collisions = sorted(set(overlay_requirements) & set(REQUIREMENTS))
    if collisions:
        raise ValueError(
            f"{overlay_path}: overlay requirement ids collide with base regime ids and would silently "
            f"override them: {collisions}. Domain overlays must use their own id prefix (e.g. FIN-AML-NNN)."
        )
    return overlay_requirements, overlay_path


@dataclass
class SourceFile:
    path: Path
    rel_path: str
    text: str


def read_files(root: Path) -> list[SourceFile]:
    files: list[SourceFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files.append(SourceFile(path=path, rel_path=str(path.relative_to(root)), text=text))
    return files


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def first_match_location(file: SourceFile, pattern: str) -> str | None:
    match = re.search(pattern, file.text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None
    return f"{file.rel_path}:{line_for_offset(file.text, match.start())}"


def detect_framework(files: list[SourceFile]) -> dict[str, Any]:
    signals: dict[str, list[str]] = {
        "openai_agents_sdk": [],
        "google_adk": [],
        "langgraph": [],
        "langchain": [],
    }
    patterns = {
        "openai_agents_sdk": [
            r"from\s+agents\s+import\s+",
            r"import\s+agents\b",
            r"from\s+agents\s+import\s+.*\bRunner\b",
            r"\bRunConfig\s*\(",
            r"@input_guardrail",
            r"@output_guardrail",
            r"@tool_input_guardrail",
            r"@tool_output_guardrail",
            r"@function_tool",
            r"\bGuardrailFunctionOutput\b",
            r"\bToolGuardrailFunctionOutput\b",
            r"\bhandoff\s*\(",
            r"openai-agents",
        ],
        "google_adk": [
            r"from\s+google\.adk",
            r"import\s+google\.adk",
            r"from\s+google\.adk\.agents\s+import\s+",
            r"from\s+google\.adk\.tools\s+import\s+",
            r"\broot_agent\s*=",
            r"\bgoogle-adk\b",
            r"\b@google/adk\b",
            r"\badk\s+web\b",
            r"\bFunctionTool\s*\(",
            r"\brequire_confirmation\s*=",
            r"\brequestConfirmation\s*\(",
            r"\brequest_confirmation\s*\(",
            r"\bSequentialAgent\s*\(",
            r"\bParallelAgent\s*\(",
            r"\bLoopAgent\s*\(",
            r"\bGraphWorkflow\b",
        ],
        "langgraph": [
            r"from\s+langgraph",
            r"import\s+langgraph",
            r"\bStateGraph\s*\(",
            r"\bMessagesState\b",
            r"\bcreate_react_agent\s*\(",
            r"\badd_conditional_edges\s*\(",
            r"\bToolNode\s*\(",
            r"\bMemorySaver\s*\(",
            r"\bcheckpointer\s*=",
            r"\bCommand\s*\(",
        ],
        "langchain": [
            r"from\s+langchain",
            r"from\s+langchain_core",
            r"import\s+langchain",
            r"\blangchain\b",
            r"\bcreate_agent\s*\(",
            r"from\s+langchain(?:_core|_community|_openai)?[.\w]*\s+import\s+.*\bAgentExecutor\b",
            r"\bHumanInTheLoopMiddleware\s*\(",
            r"\bPIIMiddleware\s*\(",
            r"\b@tool\b",
            r"\bStructuredTool\b",
            r"\bToolStrategy\s*\(",
            r"\bProviderStrategy\s*\(",
            r"\bRunnableWithMessageHistory\b",
            r"\badd_routes\s*\(",
        ],
    }
    for file in files:
        for framework, framework_patterns in patterns.items():
            for pattern in framework_patterns:
                location = first_match_location(file, pattern)
                if location:
                    signals[framework].append(f"{location} {pattern}")
                    break

    detected = [name for name, found in signals.items() if found]
    if not detected:
        return {"status": "no_agent_found", "framework": None, "signals": signals}
    if "langgraph" in detected and set(detected).issubset({"langgraph", "langchain"}):
        return {
            "status": "implemented",
            "framework": "langgraph",
            "signals": signals,
            "adapter_mode": "framework_source_first_pass",
            "route_note": "LangGraph selected because explicit graph constructs were detected; LangChain signals are expected dependencies.",
        }
    if len(detected) > 1:
        return {"status": "undetermined", "framework": None, "signals": signals}
    framework = detected[0]
    if framework != "openai_agents_sdk":
        return {"status": "implemented", "framework": framework, "signals": signals, "adapter_mode": "framework_source_first_pass"}
    return {"status": "implemented", "framework": framework, "signals": signals}


def add_control(
    controls: dict[str, dict[str, Any]],
    control_id: str,
    control_type: str,
    location: str,
    evidence: str,
    can_block: bool | str,
    adequacy: str,
    status_hint: str = "present",
) -> None:
    existing = controls.get(control_id)
    record = {
        "control_id": control_id,
        "name": CONTROL_NAMES[control_id],
        "type": control_type,
        "location": location,
        "evidence": evidence,
        "can_block": can_block,
        "adequacy_notes": adequacy,
        "status_hint": status_hint,
    }
    if not existing:
        controls[control_id] = record
        return
    if existing.get("status_hint") == "weak" and status_hint == "present":
        controls[control_id] = record


def discover_source_controls(files: list[SourceFile], framework: str) -> dict[str, Any]:
    controls: dict[str, dict[str, Any]] = {}
    architecture = {
        "has_tools": False,
        "has_retrieval": False,
        "has_handoffs": False,
        "has_memory": False,
        "has_evals": False,
        "notes": [],
    }

    for file in files:
        text = file.text
        if re.search(
            r"@input_guardrail|input_guardrails\s*=|before_agent_callback|before_model_callback|"
            r"beforeModelCallback|beforeAgentCallback|before_model|wrap_model_call|"
            r"input_moderation|input_guard|InputGuardrail|guardrails?\s*=|PIIMiddleware|"
            r"Middleware\s*\(|PromptInjection|prompt_injection|content_filter|"
            r"ToolStrategy\s*\(|ProviderStrategy\s*\(",
            text,
            re.IGNORECASE,
        ):
            location = first_match_location(
                file,
                r"@input_guardrail|input_guardrails\s*=|before_agent_callback|before_model_callback|"
                r"beforeModelCallback|beforeAgentCallback|before_model|wrap_model_call|"
                r"input_moderation|input_guard|InputGuardrail|guardrails?\s*=|PIIMiddleware|"
                r"Middleware\s*\(|PromptInjection|prompt_injection|content_filter|"
                r"ToolStrategy\s*\(|ProviderStrategy\s*\(",
            ) or file.rel_path
            add_control(
                controls,
                "C001",
                "input_guardrail",
                location,
                f"{framework} input guardrail or pre-model policy hook detected.",
                "unknown" if framework != "openai_agents_sdk" else True,
                "Static pass found an input control path; Codex must verify it can block and covers the required financial harm surface.",
            )
        if re.search(
            r"@output_guardrail|output_guardrails\s*=|after_agent_callback|after_model_callback|"
            r"afterModelCallback|afterAgentCallback|after_model|after_agent|wrap_model_call|"
            r"output_moderation|output_guard|OutputGuardrail|structured_response|response_format|"
            r"output_schema|ProviderStrategy\s*\(|ToolStrategy\s*\(|with_structured_output|"
            r"BaseModel\s*\)|JsonOutputParser|PydanticOutputParser",
            text,
            re.IGNORECASE,
        ):
            location = first_match_location(
                file,
                r"@output_guardrail|output_guardrails\s*=|after_agent_callback|after_model_callback|"
                r"afterModelCallback|afterAgentCallback|after_model|after_agent|wrap_model_call|"
                r"output_moderation|output_guard|OutputGuardrail|structured_response|response_format|"
                r"output_schema|ProviderStrategy\s*\(|ToolStrategy\s*\(|with_structured_output|"
                r"BaseModel\s*\)|JsonOutputParser|PydanticOutputParser",
            ) or file.rel_path
            add_control(
                controls,
                "C002",
                "output_guardrail",
                location,
                f"{framework} output guardrail, callback, or structured-output validation detected.",
                "unknown" if framework != "openai_agents_sdk" else True,
                "Static pass found an output control path; Codex must verify it blocks unsupported financial claims and unsafe recommendations.",
            )
        if re.search(
            r"@function_tool|FunctionTool\(|@tool\b|StructuredTool|ToolNode|tools\s*=\s*\[|"
            r"\.bind_tools\(|MCPToolset|before_tool_callback|after_tool_callback|beforeToolCallback|"
            r"afterToolCallback|AgentTool|BaseTool|OpenAPITool|MCP|ToolContext|tool_context|"
            r"HostedMCPTool|WebSearchTool|FileSearchTool|CodeInterpreterTool",
            text,
            re.IGNORECASE,
        ):
            architecture["has_tools"] = True
            architecture["notes"].append(f"{file.rel_path}: tool signal detected")
        if re.search(r"\b(BaseModel|Field\s*\(|Literal\[|Enum\b|validator|field_validator)\b|def\s+\w+\([^)]*:\s*(?:int|float|str|bool|Decimal|date|datetime)\b", text):
            location = first_match_location(file, r"\b(BaseModel|Field\s*\(|Literal\[|Enum\b|validator|field_validator)\b|def\s+\w+\([^)]*:\s*(?:int|float|str|bool|Decimal|date|datetime)\b") or file.rel_path
            add_control(
                controls,
                "C004",
                "argument_validation",
                location,
                "Typed model, enum, field constraint, or typed tool parameter detected.",
                True,
                "Syntax/schema validation detected; mark weak until business semantics are proven.",
                "weak",
            )
        if re.search(r"authorize_tool_call|require_authorized_account|verify_account_owner|entitlement|permission|authorized_user|authz|require_auth|auth_config|AuthConfig|OpenAPI.*auth|ToolContext.*credential", text, re.IGNORECASE):
            location = first_match_location(file, r"authorize_tool_call|require_authorized_account|verify_account_owner|entitlement|permission|authorized_user|authz|require_auth|auth_config|AuthConfig|OpenAPI.*auth|ToolContext.*credential") or file.rel_path
            add_control(
                controls,
                "C003",
                "tool_authorization",
                location,
                "Tool authorization or account ownership check detected.",
                True,
                "Authorization appears bound to the source-visible tool path; Codex must verify subject/account/action coverage.",
            )
        if re.search(r"validate_transfer_request|destination_allowlist|allowed_destination|idempotency_key|semantic_argument_validation|currency_allowed|account_ownership|args_schema|InjectedToolArg|InjectedState|InjectedStore|json_schema|input_schema", text, re.IGNORECASE):
            location = first_match_location(file, r"validate_transfer_request|destination_allowlist|allowed_destination|idempotency_key|semantic_argument_validation|currency_allowed|account_ownership|args_schema|InjectedToolArg|InjectedState|InjectedStore|json_schema|input_schema") or file.rel_path
            add_control(
                controls,
                "C004",
                "argument_validation",
                location,
                "Semantic financial argument validation detected.",
                True,
                "Business validation appears to cover financial semantics; Codex must verify all risky arguments are checked.",
            )
        if re.search(r"\bneeds_approval\b|\bapprove\(|\breject\(|HumanInTheLoop|HumanInTheLoopMiddleware|interrupt\(|require_confirmation\s*=|RequireConfirmation|requireConfirmation|request_confirmation\(|requestConfirmation\(|tool_confirmation|pending_approval|approval_handler|ToolApproval", text):
            location = first_match_location(file, r"\bneeds_approval\b|\bapprove\(|\breject\(|HumanInTheLoop|HumanInTheLoopMiddleware|interrupt\(|require_confirmation\s*=|RequireConfirmation|requireConfirmation|request_confirmation\(|requestConfirmation\(|tool_confirmation|pending_approval|approval_handler|ToolApproval") or file.rel_path
            add_control(
                controls,
                "C005",
                "approval_gate",
                location,
                "Approval or interrupt flow detected.",
                True,
                "Approval evidence found; Codex must verify it gates the risky action.",
            )
        if re.search(r"kill_switch|transaction_limit|daily_limit|max_transfer|MAX_TRANSFER|MAX_DAILY|limit_exceeded|risk_limit|max_iterations|max_execution_time|max_concurrency|recursion_limit|max_tool_calls|max_steps|max_turns", text, re.IGNORECASE):
            location = first_match_location(file, r"kill_switch|transaction_limit|daily_limit|max_transfer|MAX_TRANSFER|MAX_DAILY|limit_exceeded|risk_limit|max_iterations|max_execution_time|max_concurrency|recursion_limit|max_tool_calls|max_steps|max_turns") or file.rel_path
            add_control(
                controls,
                "C006",
                "transaction_limit",
                location,
                "Transaction limit, daily limit, risk limit, or kill switch detected.",
                True,
                "Limit evidence found; Codex must verify it executes before financial side effects.",
            )
        if re.search(r"FileSearchTool|WebSearchTool|GoogleSearch|google_search|Grounding|vector_store|retriev|RAG|qdrant|pinecone|chromadb|VectorStore|Retriever|create_retrieval_chain|as_retriever", text, re.IGNORECASE):
            architecture["has_retrieval"] = True
            architecture["notes"].append(f"{file.rel_path}: retrieval/RAG signal detected")
        if re.search(r"ALLOWED_RETRIEVAL_SOURCES|trusted_corpora|tenant_filter|source_allowlist|retrieval_scope|approved_corpus|metadata_filter|document_filter|namespace|collection_allowlist|grounding_source_allowlist", text, re.IGNORECASE):
            location = first_match_location(file, r"ALLOWED_RETRIEVAL_SOURCES|trusted_corpora|tenant_filter|source_allowlist|retrieval_scope|approved_corpus|metadata_filter|document_filter|namespace|collection_allowlist|grounding_source_allowlist") or file.rel_path
            add_control(
                controls,
                "C007",
                "retrieval_control",
                location,
                "Retrieval source allowlist, tenant filter, or approved corpus detected.",
                True,
                "Retrieval appears scoped; Codex must verify all retrieval tools use the scope.",
            )
        if re.search(r"validate_grounding|verify_citations|citation_required|source_to_claim|grounding_validation|grounded_answer|faithfulness|answer_relevancy|context_precision|context_recall|citation_checker|grounding_check", text, re.IGNORECASE):
            location = first_match_location(file, r"validate_grounding|verify_citations|citation_required|source_to_claim|grounding_validation|grounded_answer|faithfulness|answer_relevancy|context_precision|context_recall|citation_checker|grounding_check") or file.rel_path
            add_control(
                controls,
                "C008",
                "grounding_control",
                location,
                "Grounding or citation validation detected.",
                True,
                "Grounding evidence found; Codex must verify it blocks unsupported material financial claims.",
            )
        if re.search(
            r"handoff\s*\(|handoffs\s*=|Agent\.as_tool|sub_agents\s*=|SequentialAgent|ParallelAgent|"
            r"LoopAgent|StateGraph|GraphWorkflow|workflow|supervisor|collaborative|Command\s*\(|Send\s*\(|"
            r"add_edge\s*\(|add_conditional_edges\s*\(|START|END|subgraph|compiled_graph",
            text,
            re.IGNORECASE,
        ):
            architecture["has_handoffs"] = True
            architecture["notes"].append(f"{file.rel_path}: handoff/workflow signal detected")
        if re.search(
            r"HANDOFF_ALLOWLIST|allowed_handoffs|handoff_authority|authorize_handoff|"
            r"handoff_destination_allowlist|allowed_nodes|route_allowlist|authorized_transition|"
            r"tool_choice|is_enabled\s*=|conditional_edges|route_policy|transition_policy|"
            r"allowed_edges|Command\s*\(|goto\s*=|add_conditional_edges\s*\(",
            text,
            re.IGNORECASE,
        ):
            location = first_match_location(
                file,
                r"HANDOFF_ALLOWLIST|allowed_handoffs|handoff_authority|authorize_handoff|"
                r"handoff_destination_allowlist|allowed_nodes|route_allowlist|authorized_transition|"
                r"tool_choice|is_enabled\s*=|conditional_edges|route_policy|transition_policy|"
                r"allowed_edges|Command\s*\(|goto\s*=|add_conditional_edges\s*\(",
            ) or file.rel_path
            add_control(
                controls,
                "C012",
                "handoff_control",
                location,
                "Handoff destination allowlist or authority check detected.",
                True,
                "Handoff authority evidence found; Codex must verify it gates every handoff path.",
            )
        if re.search(
            r"handoff_input_filter|filter_handoff|redact_handoff|handoff_history_mapper|input_filter|"
            r"scoped_handoff_context|state_schema|MessagesState|typed_state|payload_filter|sanitize_state|"
            r"Annotated\[|TypedDict|InjectedState|InjectedStore|MessagesPlaceholder|trim_messages|"
            r"filter_messages|state_modifier|context_schema",
            text,
            re.IGNORECASE,
        ):
            location = first_match_location(
                file,
                r"handoff_input_filter|filter_handoff|redact_handoff|handoff_history_mapper|input_filter|"
                r"scoped_handoff_context|state_schema|MessagesState|typed_state|payload_filter|sanitize_state|"
                r"Annotated\[|TypedDict|InjectedState|InjectedStore|MessagesPlaceholder|trim_messages|"
                r"filter_messages|state_modifier|context_schema",
            ) or file.rel_path
            add_control(
                controls,
                "C013",
                "handoff_input_filter",
                location,
                "Handoff input filtering or scoped context detected.",
                True,
                "Handoff payload filtering evidence found; Codex must verify sensitive data is removed.",
            )
        if re.search(
            r"handoff_provenance|handoff_reason|record_handoff|on_handoff|handoff_metadata|"
            r"node_transition|route_reason|state_history|trace_id|span_id|astream_events|stream_events|"
            r"event_log|RunConfig|langsmith|LangSmith|traceable",
            text,
            re.IGNORECASE,
        ):
            location = first_match_location(
                file,
                r"handoff_provenance|handoff_reason|record_handoff|on_handoff|handoff_metadata|"
                r"node_transition|route_reason|state_history|trace_id|span_id|astream_events|stream_events|"
                r"event_log|RunConfig|langsmith|LangSmith|traceable",
            ) or file.rel_path
            add_control(
                controls,
                "C014",
                "handoff_provenance",
                location,
                "Handoff provenance, reason, metadata, or record hook detected.",
                "unknown",
                "Provenance evidence found; Codex must verify durability and correlation with audit logs.",
            )
        if re.search(r"Session|memory|checkpointer|checkpoint|store\s*=|MemorySaver|InMemorySaver|SqliteSaver|PostgresSaver|BaseCheckpointSaver|RunnableWithMessageHistory|ConversationBufferMemory|MemoryService|SessionService|state\s*=", text, re.IGNORECASE):
            architecture["has_memory"] = True
            architecture["notes"].append(f"{file.rel_path}: memory/session signal detected")
        if re.search(r"minimize_context|allowed_context_fields|data_minimization|scoped_context|filter_customer_data|least_privilege_context|PIIMiddleware|redact|mask|hash|block|tool_output_trimmer|context_compression|SummarizationMiddleware", text, re.IGNORECASE):
            location = first_match_location(file, r"minimize_context|allowed_context_fields|data_minimization|scoped_context|filter_customer_data|least_privilege_context|PIIMiddleware|redact|mask|hash|block|tool_output_trimmer|context_compression|SummarizationMiddleware") or file.rel_path
            add_control(
                controls,
                "C009",
                "data_minimization",
                location,
                "Data minimization or scoped context construction detected.",
                True,
                "Minimization evidence found; Codex must verify it covers prompts, tools, retrieval, memory, and handoffs.",
            )
        if re.search(r"logging\.|logger\.|trace|metrics|monitor|alert|audit|LangSmith|langsmith|Cloud Trace|telemetry|span|run_id|session_id|callbacks\s*=|BaseCallbackHandler", text, re.IGNORECASE):
            location = first_match_location(file, r"logging\.|logger\.|trace|metrics|monitor|alert|audit|LangSmith|langsmith|Cloud Trace|telemetry|span|run_id|session_id|callbacks\s*=|BaseCallbackHandler") or file.rel_path
            status_hint = "weak" if "print(" in text else "present"
            add_control(
                controls,
                "C011",
                "logging_control",
                location,
                "Logging, trace, metrics, monitor, alert, or audit signal detected.",
                "unknown",
                "Durability and required fields must be verified; print-only logging is weak.",
                status_hint,
            )
            add_control(
                controls,
                "C021",
                "operational_observability",
                location,
                "Operational/audit observability signal detected.",
                "unknown",
                "Incident response quality must be judged from configuration and alert routing.",
                status_hint,
            )
        if re.search(r"redact|mask|hash|pii|PIIMiddleware|secret|account_number|ssn|token|credit_card|apply_to_output|apply_to_tool_results|sanitize", text, re.IGNORECASE):
            location = first_match_location(file, r"redact|mask|hash|pii|PIIMiddleware|secret|account_number|ssn|token|credit_card|apply_to_output|apply_to_tool_results|sanitize") or file.rel_path
            add_control(
                controls,
                "C010",
                "sensitive_data_redaction",
                location,
                "Redaction, PII, secret, token, or sensitive-data signal detected.",
                "unknown",
                "Coverage must be checked across prompts, tools, logs, memory, and output.",
            )
        if re.search(r"prompt.?injection|jailbreak|ignore previous|bypass|prompt shield|indirect prompt|PromptInjection|Injection|untrusted_instruction|unsafe_instruction|guardrails?\s*=", text, re.IGNORECASE):
            location = first_match_location(file, r"prompt.?injection|jailbreak|ignore previous|bypass|prompt shield|indirect prompt|PromptInjection|Injection|untrusted_instruction|unsafe_instruction|guardrails?\s*=") or file.rel_path
            add_control(
                controls,
                "C017",
                "prompt_injection_guardrail",
                location,
                "Prompt-injection, jailbreak, or bypass defense signal detected.",
                "unknown",
                "Prompt-level or partial bypass checks are weak until bound to user input, retrieved content, tool output, and handoff payloads.",
                "weak",
            )
        if re.search(r"check_untrusted_instruction_channels|guard_retrieved_content|tool_output_injection|handoff_payload_injection|indirect_prompt_injection|quarantine_untrusted_instructions", text, re.IGNORECASE):
            location = first_match_location(file, r"check_untrusted_instruction_channels|guard_retrieved_content|tool_output_injection|handoff_payload_injection|indirect_prompt_injection|quarantine_untrusted_instructions") or file.rel_path
            add_control(
                controls,
                "C017",
                "prompt_injection_guardrail",
                location,
                "Bound prompt-injection controls for untrusted channels detected.",
                True,
                "Source-visible controls cover indirect prompt injection channels; Codex must verify runtime binding.",
            )
        if re.search(r"toxicity|toxic|hate|harassment|abuse|moderation|content safety|self-harm|safety_policy|content_filter|HarmCategory|SafetySetting", text, re.IGNORECASE):
            location = first_match_location(file, r"toxicity|toxic|hate|harassment|abuse|moderation|content safety|self-harm|safety_policy|content_filter|HarmCategory|SafetySetting") or file.rel_path
            add_control(
                controls,
                "C018",
                "content_safety_guardrail",
                location,
                "Toxicity, moderation, abuse, or content-safety signal detected.",
                "unknown",
                "Must inspect both user input and final output for customer-facing agents.",
            )
        if re.search(r"rate.?limit|quota|max_tokens|budget|cost|throttle|max_concurrency|recursion_limit|max_iterations|max_tool_calls|max_turns|token_usage|usage_limit", text, re.IGNORECASE):
            location = first_match_location(file, r"rate.?limit|quota|max_tokens|budget|cost|throttle|max_concurrency|recursion_limit|max_iterations|max_tool_calls|max_turns|token_usage|usage_limit") or file.rel_path
            add_control(
                controls,
                "C019",
                "rate_cost_boundary",
                location,
                "Rate, quota, token, budget, cost, or throttle signal detected.",
                True,
                "Must bound model/tool/resource consumption on the production path.",
            )
        if re.search(r"timeout|retry|fallback|circuit.?breaker|degrad|with_retry|with_fallbacks|RetryPolicy|step_timeout|interrupt_after|cancel|resume", text, re.IGNORECASE):
            location = first_match_location(file, r"timeout|retry|fallback|circuit.?breaker|degrad|with_retry|with_fallbacks|RetryPolicy|step_timeout|interrupt_after|cancel|resume") or file.rel_path
            add_control(
                controls,
                "C020",
                "resilience_control",
                location,
                "Timeout, retry, fallback, circuit-breaker, or degradation signal detected.",
                True,
                "Must preserve safe behavior under upstream/model/tool failure.",
            )
        if re.search(r"\bevals?\b|red.?team|benchmark|golden|pytest|unittest|deepeval|langsmith|LangSmith|jailbreak.*dataset|safety.*dataset|test_case|evaluation|Dataset|Example", text, re.IGNORECASE):
            architecture["has_evals"] = True
            location = first_match_location(file, r"\bevals?\b|red.?team|benchmark|golden|pytest|unittest|deepeval|langsmith|LangSmith|jailbreak.*dataset|safety.*dataset|test_case|evaluation|Dataset|Example") or file.rel_path
            add_control(
                controls,
                "C022",
                "eval_harness",
                location,
                "Eval, red-team, benchmark, or test signal detected.",
                "unknown",
                "Must include high-risk scenarios and regression gates to be adequate.",
            )
        if re.search(r"MODEL_VERSION|dataset_hash|random_seed|eval_threshold|temperature\s*=\s*0|pinned_model|reproducible_eval", text, re.IGNORECASE):
            location = first_match_location(file, r"MODEL_VERSION|dataset_hash|random_seed|eval_threshold|temperature\s*=\s*0|pinned_model|reproducible_eval") or file.rel_path
            add_control(
                controls,
                "C016",
                "reproducibility_control",
                location,
                "Pinned model, dataset hash, seed, or eval threshold detected.",
                "unknown",
                "Reproducibility evidence found; Codex must verify all eval-dependent claims use it.",
            )
        governance_patterns = [
            (
                "C023",
                "model_governance",
                r"model_inventory|model_registry|use_case_inventory|model_owner|control_owner|RACI|risk_tier",
                "Model inventory, ownership, RACI, or risk-tier evidence detected.",
                "Inventory evidence must identify the model/agent, owner, control owner, risk tier, and deployment status.",
            ),
            (
                "C024",
                "model_governance",
                r"intended_use|prohibited_use|model_card|limitations|assumptions|use_case_approval",
                "Intended-use, prohibited-use, model-card, assumptions, or limitation evidence detected.",
                "Intended-use evidence must constrain approved use and name limitations/escalation paths.",
            ),
            (
                "C025",
                "model_validation",
                r"independent_validation|effective_challenge|model_validation|validator|second_line|review_committee",
                "Independent validation, effective challenge, validator, or second-line review evidence detected.",
                "Validation evidence must be independent of the builder path and include findings, approvals, and retest cadence.",
            ),
            (
                "C026",
                "data_governance",
                r"data_lineage|data_quality|data_dictionary|feature_store|source_system|dataset_schema|input_data_quality",
                "Data lineage, data quality, source-system, or schema evidence detected.",
                "Data governance evidence must cover source systems, transformations, freshness, and quality thresholds.",
            ),
            (
                "C027",
                "model_monitoring",
                r"drift|outcome_monitoring|performance_monitoring|population_stability|PSI\b|monitoring_threshold",
                "Drift, outcome monitoring, population stability, or monitoring-threshold evidence detected.",
                "Monitoring evidence must include thresholds, cadence, owner action paths, and alerting.",
            ),
            (
                "C028",
                "model_benchmarking",
                r"benchmark|challenger|backtest|back-testing|outcomes_analysis|baseline_model",
                "Benchmarking, challenger, backtesting, outcomes-analysis, or baseline-model evidence detected.",
                "Benchmarking evidence must define baselines, acceptance thresholds, and variance or confidence.",
            ),
            (
                "C029",
                "fairness_testing",
                r"fairness|bias|disparate_impact|protected_class|equal_opportunity|fair_lending",
                "Fairness, bias, disparate-impact, protected-class, or fair-lending evidence detected.",
                "Fairness evidence must include segment tests, thresholds, and mitigations when outcomes affect people or entities.",
            ),
            (
                "C030",
                "explainability_control",
                r"explainability|reason_code|feature_importance|SHAP|LIME|adverse_action|explanation",
                "Explainability, reason-code, feature-importance, or adverse-action evidence detected.",
                "Explainability evidence must be fit for reviewer/customer/regulatory use and tied to output decisions.",
            ),
            (
                "C031",
                "change_management",
                r"change_management|release_approval|model_change|approval_workflow|deployment_approval|version_control",
                "Change-management, release-approval, approval-workflow, or version-control evidence detected.",
                "Change evidence must gate material model, prompt, tool, retrieval, policy, and eval-threshold changes.",
            ),
            (
                "C032",
                "vendor_model_risk",
                r"vendor|third_party|third-party|model_provider|supplier|outsourcing|vendor_risk|third_party_risk",
                "Vendor, third-party, model-provider, supplier, or outsourcing risk evidence detected.",
                "Vendor evidence must cover provider risk, data boundaries, dependencies, SLAs, and contingency plans.",
            ),
            (
                "C033",
                "access_control",
                r"RBAC|role_based_access|segregation_of_duties|least_privilege|access_control|privileged_access",
                "RBAC, segregation-of-duties, least-privilege, or privileged-access evidence detected.",
                "Access evidence must separate builder, approver, deployer, and production-configuration privileges where required.",
            ),
            (
                "C034",
                "evidence_retention",
                r"retention|legal_hold|evidence_retention|records_retention|audit_trail|tamper_evident",
                "Evidence-retention, legal-hold, records-retention, audit-trail, or tamper-evident evidence detected.",
                "Retention evidence must preserve prompts, evals, approvals, traces, decisions, and evidence bundles for the required period.",
            ),
            (
                "C035",
                "continuity_control",
                r"business_continuity|disaster_recovery|rollback|decommission|kill_switch|recovery_time|RTO\b|RPO\b",
                "Business-continuity, disaster-recovery, rollback, decommission, or recovery-objective evidence detected.",
                "Continuity evidence must define rollback, fail-closed behavior, recovery objectives, and decommission criteria.",
            ),
            (
                "C036",
                "governance_reporting",
                r"model_governance_report|risk_committee|board_report|model_risk_report|governance_dashboard|status_report",
                "Model-governance reporting, risk-committee, board-report, or governance-dashboard evidence detected.",
                "Governance reporting evidence must show periodic status, issues, incidents, validation, monitoring, and exceptions.",
            ),
        ]
        for control_id, control_type, pattern, evidence, adequacy in governance_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                location = first_match_location(file, pattern) or file.rel_path
                add_control(
                    controls,
                    control_id,
                    control_type,
                    location,
                    evidence,
                    "unknown",
                    adequacy,
                )

    result = {
        "controls_present": list(controls.values()),
        "architecture": architecture,
        "blind_spots": [
            "Static pass cannot verify deployment IAM, gateway policies, production approval queues, monitoring, human procedures, or runtime-only configuration."
        ],
    }
    if framework != "openai_agents_sdk":
        result["blind_spots"].append(
            f"{framework} was checked with a framework-aware source pass; runtime callback order, hosted configuration, and deployed control enforcement still require dynamic proof."
        )
    return result


def infer_profile(files: list[SourceFile], discovery: dict[str, Any]) -> dict[str, Any]:
    combined = "\n".join(file.text.lower() for file in files)
    architecture = discovery.get("architecture", {})
    harm_surfaces: set[str] = set()

    if re.search(r"transfer|payment|refund|trade|order checkout|checkout|cancel payment|wire|ach", combined):
        harm_surfaces.add("money_movement")
    if re.search(r"investment|portfolio|valuation|dcf|recommendation|advice|equity|stock|credit|eligibility", combined):
        harm_surfaces.add("financial_recommendation")
    if re.search(r"customer|account|transaction|balance|merchant|private key|payment", combined):
        harm_surfaces.add("customer_financial_data")
    if architecture.get("has_retrieval") or re.search(r"rag|sec filing|10-k|10-q|retriev|vector", combined):
        harm_surfaces.add("retrieval_grounded_financial_answer")
    if re.search(r"email|telegram|api|fastapi|streamlit|customer-facing|report|external", combined):
        harm_surfaces.add("regulated_customer_communication")

    if architecture.get("has_tools") and "money_movement" in harm_surfaces:
        autonomy = "autonomous_tool_use"
    elif architecture.get("has_tools"):
        autonomy = "tool_with_confirmation"
    elif architecture.get("has_handoffs"):
        autonomy = "delegated_multi_agent"
    else:
        autonomy = "answer_only"

    arch_names = []
    if architecture.get("has_tools"):
        arch_names.append("tool_agent")
    if architecture.get("has_retrieval"):
        arch_names.append("rag_agent")
    if architecture.get("has_handoffs"):
        arch_names.append("multi_agent_handoff")
    if architecture.get("has_memory"):
        arch_names.append("stateful_memory")
    if not arch_names:
        arch_names.append("single_agent")

    return {
        "business": "financial agent inferred from repository text",
        "harm_surfaces": sorted(harm_surfaces),
        "autonomy": autonomy,
        "architecture": arch_names,
        "external_or_customer_facing": bool(re.search(r"api|fastapi|streamlit|telegram|web|customer|user", combined)),
        "has_safety_claims_or_evals": bool(architecture.get("has_evals") or re.search(r"safety|benchmark|eval|red.?team|confidence|accuracy", combined)),
    }


def derive_required(profile: dict[str, Any], requirements_catalog: dict[str, dict[str, Any]] = REQUIREMENTS) -> dict[str, list[str]]:
    requirements: dict[str, list[str]] = {}
    surfaces = set(profile["harm_surfaces"])
    architecture = set(profile["architecture"])
    high_risk_architecture = bool({"rag_agent", "tool_agent", "multi_agent_handoff", "agent_as_tool"} & architecture)
    customer_or_external = bool(profile.get("external_or_customer_facing"))
    data_driven = bool(
        {"customer_financial_data", "retrieval_grounded_financial_answer", "financial_recommendation", "credit_or_eligibility", "regulated_customer_communication"}
        & surfaces
    )

    if "money_movement" in surfaces:
        requirements["FIN-001"] = requirements_catalog["FIN-001"]["controls"]
    if {"financial_recommendation", "credit_or_eligibility", "regulated_customer_communication"} & surfaces:
        requirements["FIN-002"] = requirements_catalog["FIN-002"]["controls"]
    if "customer_financial_data" in surfaces:
        requirements["FIN-003"] = requirements_catalog["FIN-003"]["controls"]
    if "rag_agent" in architecture or "retrieval_grounded_financial_answer" in surfaces:
        requirements["FIN-004"] = requirements_catalog["FIN-004"]["controls"]
    if "multi_agent_handoff" in architecture or "agent_as_tool" in architecture:
        requirements["FIN-005"] = requirements_catalog["FIN-005"]["controls"]
    if profile.get("has_safety_claims_or_evals"):
        requirements["FIN-006"] = requirements_catalog["FIN-006"]["controls"]
    if profile.get("external_or_customer_facing") or {"rag_agent", "tool_agent"} & architecture:
        requirements["FIN-007"] = requirements_catalog["FIN-007"]["controls"]
    if profile.get("external_or_customer_facing"):
        requirements["FIN-008"] = requirements_catalog["FIN-008"]["controls"]
        requirements["FIN-009"] = requirements_catalog["FIN-009"]["controls"]
    if surfaces or {"rag_agent", "tool_agent", "multi_agent_handoff"} & architecture:
        requirements["FIN-010"] = requirements_catalog["FIN-010"]["controls"]
    if surfaces or high_risk_architecture or customer_or_external:
        requirements["FIN-011"] = requirements_catalog["FIN-011"]["controls"]
    if profile.get("has_safety_claims_or_evals") or data_driven or high_risk_architecture:
        requirements["FIN-012"] = requirements_catalog["FIN-012"]["controls"]
    if data_driven:
        requirements["FIN-013"] = requirements_catalog["FIN-013"]["controls"]
    if customer_or_external or high_risk_architecture:
        requirements["FIN-014"] = requirements_catalog["FIN-014"]["controls"]
    return requirements


def merge_domain_overlay(required: dict[str, list[str]], overlay_requirements: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """Add domain-overlay requirement ids into a derive_required() result. Overlay
    requirements apply unconditionally once merged — the caller only invokes this
    when a --domain was selected and its regime_overlay.json was found and validated."""
    merged = dict(required)
    for requirement_id, entry in overlay_requirements.items():
        merged[requirement_id] = entry["controls"]
    return merged


def max_severity(requirement_ids: list[str], status: str, requirements_catalog: dict[str, dict[str, Any]] = REQUIREMENTS) -> str:
    severity = "low"
    for requirement_id in requirement_ids:
        candidate = requirements_catalog[requirement_id]["severity"]
        if SEVERITY_ORDER[candidate] > SEVERITY_ORDER[severity]:
            severity = candidate
    if status == "weak" and severity == "blocker":
        return "blocker"
    if status in {"out_of_scope", "not_checked"} and SEVERITY_ORDER[severity] < SEVERITY_ORDER["medium"]:
        return "medium"
    return severity


def canonical_hash(record: dict[str, Any]) -> str:
    clean = dict(record)
    clean["record_hash"] = None
    payload = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def compare_controls(
    root: Path,
    required: dict[str, list[str]],
    present: list[dict[str, Any]],
    requirements_catalog: dict[str, dict[str, Any]] = REQUIREMENTS,
) -> list[dict[str, Any]]:
    present_by_id = {control["control_id"]: control for control in present}
    control_to_requirements: dict[str, list[str]] = {}
    for requirement_id, control_ids in required.items():
        for control_id in control_ids:
            control_to_requirements.setdefault(control_id, []).append(requirement_id)

    records: list[dict[str, Any]] = []
    for idx, control_id in enumerate(sorted(control_to_requirements), start=1):
        requirement_ids = control_to_requirements[control_id]
        control = present_by_id.get(control_id)
        if not control:
            status = "missing"
            location = None
            evidence = []
            adequacy = "No source-visible control was detected for this required control."
        else:
            status = "weak" if control.get("status_hint") == "weak" else "present"
            location = control.get("location")
            evidence = [control.get("evidence", "")]
            adequacy = control.get("adequacy_notes", "")
        if status == "present":
            continue

        primary_requirement = requirement_ids[0]
        record = {
            "schema_version": "1.0",
            "audit_id": "aca-static-first-pass",
            "finding_id": f"ACA-{idx:03d}",
            "target": {"repo": str(root), "entrypoint": None, "commit": None},
            "control": {
                "id": control_id,
                "name": CONTROL_NAMES[control_id],
                "type": control["type"] if control else "unknown",
            },
            "requirement": {
                "id": primary_requirement,
                "text": requirements_catalog[primary_requirement]["text"],
                "source": requirements_catalog[primary_requirement].get("source", "author_policy"),
            },
            "all_requirement_ids": requirement_ids,
            "status": status,
            "severity": max_severity(requirement_ids, status, requirements_catalog),
            "location": location,
            "detection_method": "static_audit_py",
            "evidence": evidence,
            "adequacy": adequacy,
            "recommendation": recommendation_for(control_id),
            "eval_evidence": {
                "suite": None,
                "dataset_hash": None,
                "runner": None,
                "metrics": None,
                "thresholds": None,
                "passed": None,
            },
            "coverage": {
                "static_only": True,
                "blind_spots": [
                    "Runtime behavior, deployed infrastructure, external approval queues, and production telemetry were not executed or verified."
                ],
            },
            "confidence": "medium",
            "record_hash": None,
            "signature": None,
            "signature_algorithm": None,
            "signed_by": None,
            "signed_at": None,
        }
        record["record_hash"] = canonical_hash(record)
        records.append(record)
    records.sort(key=lambda r: (-SEVERITY_ORDER[r["severity"]], r["control"]["id"]))
    return records


def recommendation_for(control_id: str) -> str:
    recommendations = {
        "C001": "Add a blocking input guardrail for unsupported financial requests, bypass attempts, and authority boundaries.",
        "C002": "Add final-output validation for unsupported claims, grounding, required caveats, and regulated financial advice.",
        "C003": "Bind authorization checks to each sensitive or side-effecting tool invocation.",
        "C004": "Add semantic validation for account ownership, destination allowlists, currency, idempotency, and limits.",
        "C005": "Add an approval gate that pauses before high-impact financial actions execute.",
        "C006": "Enforce transaction amount/frequency/recipient limits and a kill switch before side effects.",
        "C007": "Restrict retrieval to approved corpora, tenants, accounts, and freshness windows.",
        "C008": "Validate that material financial claims are grounded in cited authoritative sources.",
        "C009": "Minimize customer financial data in prompts, retrieval payloads, memory, tools, and handoffs.",
        "C010": "Redact sensitive financial data and secrets across prompts, tools, logs, memory, and outputs.",
        "C011": "Emit durable structured audit logs for tool calls, guardrail trips, approvals, denials, and final outcomes.",
        "C012": "Constrain handoff destinations and transferred authority with explicit policy checks.",
        "C013": "Filter handoff inputs and redact unnecessary history/tool/customer data.",
        "C014": "Record handoff reason, source, destination, accepted responsibility, and data moved.",
        "C016": "Pin model/runtime versions, datasets, seeds, and report variance for eval-dependent safety claims.",
        "C017": "Add prompt-injection and jailbreak defenses for user input, retrieved content, tool output, and handoff payloads.",
        "C018": "Add toxicity and abusive-content moderation on customer input and final output.",
        "C019": "Set rate, quota, token, budget, and tool-call limits on production paths.",
        "C020": "Add timeouts, retries, safe fallback behavior, and degradation paths for model/tool/data failures.",
        "C021": "Add metrics, traces, alerts, runbooks, and incident hooks for safety-relevant events.",
        "C022": "Create CI-gated eval suites for jailbreaks, prompt injection, leakage, grounding, tool misuse, and benign false positives.",
        "C023": "Register the agent/model in inventory with owner, control owner, risk tier, deployment status, and approval links.",
        "C024": "Document approved intended use, prohibited use, assumptions, limitations, and escalation boundaries.",
        "C025": "Add independent validation/effective-challenge evidence with reviewer ownership, findings, approvals, and retest cadence.",
        "C026": "Document data lineage, source systems, transformations, freshness, schema, and quality thresholds.",
        "C027": "Add drift and outcome monitoring with thresholds, cadence, alerting, and owner action paths.",
        "C028": "Add benchmark, challenger, or backtesting evidence with acceptance thresholds and variance/confidence reporting.",
        "C029": "Add fairness and bias tests for affected customer/entity segments with thresholds and mitigation actions.",
        "C030": "Add reason codes, citations, or explainability artifacts tied to regulated recommendations or decisions.",
        "C031": "Gate material model, prompt, tool, retrieval, policy, dataset, and eval-threshold changes through release approval.",
        "C032": "Document third-party/model-provider risk, data boundaries, SLAs, dependencies, and contingency plans.",
        "C033": "Enforce least privilege, privileged-access review, and segregation between builders, approvers, and deployers.",
        "C034": "Define evidence retention and legal-hold handling for prompts, evals, approvals, traces, and decisions.",
        "C035": "Add rollback, fail-closed continuity, recovery objectives, dependency maps, and decommission criteria.",
        "C036": "Add governance reporting for validation status, incidents, exceptions, drift, eval regressions, and open issues.",
    }
    return recommendations.get(control_id, "Implement an adequate source-visible control for this requirement.")


def verdict_for(findings: list[dict[str, Any]]) -> tuple[str, str]:
    if any(f["severity"] == "blocker" for f in findings):
        return "critical", "block"
    if any(f["severity"] == "high" for f in findings):
        return "elevated", "hold"
    if any(f["severity"] == "medium" for f in findings):
        return "moderate", "ship_with_conditions"
    return "low", "ship"


def audit(root: Path, domain: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    files = read_files(root)
    route = detect_framework(files)
    domain_overlay_requirements, domain_overlay_path = load_domain_overlay(domain) if domain else ({}, None)
    domain_info = {
        "domain": domain,
        "domain_overlay_loaded": domain_overlay_path is not None,
        "domain_overlay_path": str(domain_overlay_path) if domain_overlay_path else None,
        "domain_overlay_requirement_ids": sorted(domain_overlay_requirements),
        "domain_overlay_catalog": domain_overlay_requirements,
    }
    if route["status"] != "implemented":
        risk_tier = "critical" if route["status"] in {"undetermined", "not_implemented", "no_agent_found"} else "low"
        decision = "block" if route["status"] in {"undetermined", "not_implemented", "no_agent_found"} else "ship"
        return {
            "target": str(root),
            "framework": route["framework"],
            "adapter_status": route["status"],
            "adapter_mode": route.get("adapter_mode"),
            "risk_tier": risk_tier,
            "decision": decision,
            "signals": route["signals"],
            "controls_present": [],
            "required_controls": {},
            "findings": [],
            "coverage_statement": coverage_statement(route["status"], route["framework"]),
            **domain_info,
        }

    discovery = discover_source_controls(files, route["framework"])
    profile = infer_profile(files, discovery)
    requirements_catalog = {**REQUIREMENTS, **domain_overlay_requirements}
    required = derive_required(profile, requirements_catalog)
    if domain_overlay_requirements:
        required = merge_domain_overlay(required, domain_overlay_requirements)
    findings = compare_controls(root, required, discovery["controls_present"], requirements_catalog)
    risk_tier, decision = verdict_for(findings)
    return {
        "target": str(root),
        "framework": route["framework"],
        "adapter_status": route["status"],
        "adapter_mode": route.get("adapter_mode", "framework_static_adapter"),
        "risk_tier": risk_tier,
        "decision": decision,
        "signals": route["signals"],
        "profile": profile,
        "architecture": discovery["architecture"],
        "controls_present": discovery["controls_present"],
        "required_controls": required,
        "findings": findings,
        "coverage_statement": coverage_statement(route["status"], route["framework"]),
        "blind_spots": discovery["blind_spots"],
        **domain_info,
    }


def coverage_statement(status: str, framework: str | None) -> str:
    if status == "no_agent_found":
        return "Static audit did not locate an agent entrypoint or supported framework signal."
    if status == "undetermined":
        return "Static audit found ambiguous framework signals and stopped rather than guessing."
    if status == "not_implemented":
        return f"Static audit detected {framework}, but this adapter is not implemented yet."
    if framework != "openai_agents_sdk":
        return (
            f"Static first-pass audit checked source-visible {framework} framework APIs, tools, retrieval, "
            "workflow/handoff controls, memory/session signals, NFR signals, model-governance signals, eval signals, and hashable "
            "evidence. It did not execute the agent or verify deployment-only controls, runtime callback order, or hosted configuration."
        )
    return (
        "Static first-pass audit checked source-visible framework signals, OpenAI Agents SDK guardrails, "
        "tools, retrieval, handoffs, NFR signals, model-governance signals, eval signals, and hashable evidence. It did not execute "
        "the agent or verify deployment-only controls."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Static first-pass agent control audit")
    parser.add_argument("target", type=Path, help="Agent repository or fixture path to audit")
    parser.add_argument("--out", type=Path, help="Optional path for full audit JSON output")
    parser.add_argument("--jsonl", type=Path, help="Optional path for finding records as JSON Lines")
    parser.add_argument(
        "--domain",
        help="Domain pack name under domain_extensions/<domain>/. When its regime_overlay.json exists, "
        "its requirements are validated and merged into the required-control set for this run.",
    )
    args = parser.parse_args()

    result = audit(args.target, domain=args.domain)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.jsonl:
        args.jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.jsonl.open("w", encoding="utf-8") as handle:
            for finding in result.get("findings", []):
                handle.write(json.dumps(finding, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
