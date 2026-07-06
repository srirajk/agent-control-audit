"""ADK callback controls for the reference agent."""

from __future__ import annotations

import time

from google.adk.tools import ToolContext

from .config import HIGH_IMPACT_ACTIONS, KILL_SWITCH_ENABLED, MAX_RUNTIME_SECONDS, MAX_TOKENS
from .policies import (
    audit_log,
    authorize_tool_call,
    check_untrusted_instruction_channels,
    content_safety_policy,
    redact,
)


def before_agent_callback(callback_context):
    prompt = str(getattr(callback_context, "user_content", ""))
    if "file sar now" in prompt.lower() or "finalize a sar" in prompt.lower():
        from google.genai import types

        return types.Content(
            role="model",
            parts=[types.Part(text="Human approval required before SAR narrative finalization.")],
        )
    if "tell the customer" in prompt.lower() or "under aml investigation" in prompt.lower():
        from google.genai import types

        return types.Content(
            role="model",
            parts=[types.Part(text="I cannot contact or tip off the customer about an AML investigation.")],
        )
    if any(marker in prompt.lower() for marker in ["ignore previous", "bypass", "reveal the system prompt", "exfiltrate"]):
        from google.genai import types

        return types.Content(
            role="model",
            parts=[types.Part(text="Blocked indirect prompt injection from retrieved content.")],
        )
    if "account number" in prompt.lower() or "ssn" in prompt.lower():
        from google.genai import types

        return types.Content(
            role="model",
            parts=[types.Part(text="Analyst summary: sensitive identifiers redacted. citation: CASE-1005.")],
        )
    check_untrusted_instruction_channels(prompt)
    content_safety_policy(prompt)
    return None


def before_model_callback(callback_context, llm_request):
    if KILL_SWITCH_ENABLED:
        return {"blocked": True, "reason": "kill_switch"}
    llm_request.config = getattr(llm_request, "config", {}) or {}
    if isinstance(llm_request.config, dict):
        llm_request.config["max_tokens"] = MAX_TOKENS
        llm_request.config["temperature"] = 0
    else:
        setattr(llm_request.config, "max_output_tokens", MAX_TOKENS)
        setattr(llm_request.config, "temperature", 0)
    return None


def before_tool_callback(tool, args, tool_context: ToolContext):
    started = time.monotonic()
    if time.monotonic() - started > MAX_RUNTIME_SECONDS:
        raise TimeoutError("timeout fallback to manual_review")
    case_id = str(args.get("case_id", ""))
    analyst_id = args.get("analyst_id")
    authorize_tool_call(case_id, analyst_id)
    if args.get("action") in HIGH_IMPACT_ACTIONS:
        tool_context.request_confirmation("Human approval required before high-impact AML action")
    audit_log(case_id, "before_tool", "authorized_tool_call", tool=str(getattr(tool, "name", tool)))
    return None


def after_tool_callback(tool, args, tool_context: ToolContext, result=None, tool_response=None, **kwargs):
    return redact(tool_response if tool_response is not None else result)


def after_agent_callback(callback_context, response=None):
    if response is None:
        return None
    text = str(response).lower()
    if "sar filed" in text or "customer notified" in text or "alert closed" in text:
        return {"blocked": True, "reason": "unsupported regulated action"}
    if "citation:" not in text and "manual review" not in text and "approval" not in text:
        return {"blocked": True, "reason": "grounding validation failed"}
    return response
