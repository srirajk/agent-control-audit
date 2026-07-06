#!/usr/bin/env python3
"""Google ADK 2.0 / graph workflow runner adapter.

Configure:
  AGENT_ASSURANCE_ADK_WORKFLOW="your_package.workflow:workflow"

For ADK 2.0-style graph or collaborative workflows, this adapter treats human
input pauses, approval events, or graph interrupts as approval requests and
extracts visible node/tool events from returned state when present.
"""

from __future__ import annotations

import asyncio
import inspect
import importlib
import json
import os
import sys
from typing import Any


def load_attr(spec: str) -> Any:
    module_name, attr_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    value: Any = module
    for part in attr_name.split("."):
        value = getattr(value, part)
    return value


def build_state(case: dict[str, Any]) -> dict[str, Any]:
    prompt = case["input"]
    if case.get("retrieved_doc"):
        prompt += f"\n\nRetrieved document:\n{case['retrieved_doc']}"
    return {
        "messages": [{"role": "user", "content": prompt}],
        "case": case,
        "user_context": case.get("user_context", {}),
        "assurance": {"case_id": case["id"], "suite": case["suite"]},
    }


async def maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def output_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "messages" in value and value["messages"]:
            return output_text(value["messages"][-1])
        for key in ("observed_output", "final_response", "output", "content", "text"):
            if key in value:
                return output_text(value[key])
        return json.dumps(value, sort_keys=True, default=str)
    for attr in ("final_response", "output", "content", "text"):
        if hasattr(value, attr):
            return output_text(getattr(value, attr))
    return str(value)


def event_names(value: Any, wanted: str) -> list[str]:
    names: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            event_type = str(item.get("type") or item.get("event_type") or item.get("kind") or "").lower()
            name = item.get("tool") or item.get("tool_name") or item.get("node") or item.get("name")
            if name and wanted in event_type:
                names.append(str(name))
            for nested in item.values():
                walk(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                walk(nested)
        else:
            name = getattr(item, "tool_name", None) or getattr(item, "node", None) or getattr(item, "name", None)
            event_type = str(getattr(item, "event_type", "") or getattr(item, "type", "")).lower()
            if name and wanted in event_type:
                names.append(str(name))

    walk(value)
    return sorted(set(names))


def approval_pause(value: Any) -> bool:
    text = json.dumps(value, default=str).lower() if not isinstance(value, str) else value.lower()
    markers = ["approval_required", "human_input", "interrupt", "pause_for_review", "pending_review"]
    return any(marker in text for marker in markers)


async def run_case(case: dict[str, Any]) -> dict[str, Any]:
    spec = os.environ.get("AGENT_ASSURANCE_ADK_WORKFLOW")
    if not spec:
        raise RuntimeError("Set AGENT_ASSURANCE_ADK_WORKFLOW='module:workflow'.")

    if os.environ.get("AGENT_ASSURANCE_ENABLE_DEEPEVAL_TRACE") == "1":
        try:
            from deepeval.integrations.google_adk import instrument_google_adk

            instrument_google_adk()
        except Exception:
            pass

    workflow = load_attr(spec)
    state = build_state(case)

    if hasattr(workflow, "run_async"):
        raw = await workflow.run_async(state)
    elif hasattr(workflow, "run"):
        raw = workflow.run(state)
    elif hasattr(workflow, "ainvoke"):
        raw = await workflow.ainvoke(state)
    elif hasattr(workflow, "invoke"):
        raw = workflow.invoke(state)
    elif callable(workflow):
        raw = await maybe_await(workflow(state))
    else:
        raise RuntimeError("Workflow must be callable or expose run/run_async/invoke/ainvoke.")

    text = output_text(raw)
    return {
        "id": case["id"],
        "suite": case["suite"],
        "observed_output": text,
        "tool_calls": event_names(raw, "tool"),
        "blocked": "blocked" in text.lower() or "safety" in text.lower(),
        "approval_requested": approval_pause(raw),
        "citations": raw.get("citations", []) if isinstance(raw, dict) else [],
        "notes": "google adk 2.0 workflow adapter; nodes=" + ",".join(event_names(raw, "node")),
    }


def main() -> int:
    case = json.load(sys.stdin)
    try:
        result = asyncio.run(run_case(case))
    except Exception as exc:
        result = {
            "id": case.get("id"),
            "suite": case.get("suite"),
            "observed_output": "",
            "tool_calls": [],
            "blocked": False,
            "approval_requested": False,
            "citations": [],
            "notes": f"adapter error: {type(exc).__name__}: {exc}",
        }
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

