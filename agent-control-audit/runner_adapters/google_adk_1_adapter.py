#!/usr/bin/env python3
"""Google ADK 1.x-style runner adapter for agent-control-audit evals.

Configure one of:
  AGENT_ASSURANCE_ADK_RUNNER="your_package.eval_adapter:run_case"
  AGENT_ASSURANCE_ADK_AGENT="your_package.agent:root_agent"

The recommended path is AGENT_ASSURANCE_ADK_RUNNER: a small project-owned
function that receives the case dict and returns either the final response or
the result JSON. That keeps this adapter independent of ADK application wiring.
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


def build_prompt(case: dict[str, Any]) -> str:
    prompt = case["input"]
    if case.get("retrieved_doc"):
        prompt += f"\n\nRetrieved document:\n{case['retrieved_doc']}"
    if case.get("user_context"):
        prompt += "\n\nUser context JSON:\n" + json.dumps(case["user_context"], sort_keys=True)
    return prompt


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
        for key in ("observed_output", "final_response", "output", "content", "text"):
            if key in value:
                return output_text(value[key])
        return json.dumps(value, sort_keys=True, default=str)
    for attr in ("final_response", "output", "content", "text"):
        if hasattr(value, attr):
            return output_text(getattr(value, attr))
    return str(value)


def tool_calls_from(value: Any) -> list[str]:
    calls: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            event_type = str(item.get("type") or item.get("event_type") or "").lower()
            name = item.get("tool") or item.get("tool_name") or item.get("name")
            if name and ("tool" in event_type or item.get("tool_call")):
                calls.append(str(name))
            for nested in item.values():
                walk(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                walk(nested)
        else:
            name = getattr(item, "tool_name", None) or getattr(item, "name", None)
            event_type = str(getattr(item, "event_type", "") or getattr(item, "type", "")).lower()
            if name and "tool" in event_type:
                calls.append(str(name))

    walk(value)
    return sorted(set(calls))


def normalize_result(case: dict[str, Any], raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and "observed_output" in raw:
        raw.setdefault("id", case["id"])
        raw.setdefault("suite", case["suite"])
        raw.setdefault("tool_calls", [])
        raw.setdefault("blocked", False)
        raw.setdefault("approval_requested", False)
        raw.setdefault("citations", [])
        raw.setdefault("notes", "google adk 1.x project runner")
        return raw

    text = output_text(raw)
    return {
        "id": case["id"],
        "suite": case["suite"],
        "observed_output": text,
        "tool_calls": tool_calls_from(raw),
        "blocked": "blocked" in text.lower() or "safety" in text.lower(),
        "approval_requested": "approval" in text.lower() and "required" in text.lower(),
        "citations": raw.get("citations", []) if isinstance(raw, dict) else [],
        "notes": "google adk 1.x adapter",
    }


async def run_with_project_runner(case: dict[str, Any], spec: str) -> Any:
    runner = load_attr(spec)
    return await maybe_await(runner(case))


async def run_with_adk_agent(case: dict[str, Any], spec: str) -> Any:
    agent = load_attr(spec)
    prompt = build_prompt(case)

    if os.environ.get("AGENT_ASSURANCE_ENABLE_DEEPEVAL_TRACE") == "1":
        try:
            from deepeval.integrations.google_adk import instrument_google_adk

            instrument_google_adk()
        except Exception:
            pass

    if hasattr(agent, "run_async"):
        return await agent.run_async(prompt)
    if hasattr(agent, "run"):
        return agent.run(prompt)
    if hasattr(agent, "ainvoke"):
        return await agent.ainvoke({"messages": [{"role": "user", "content": prompt}], "case": case})
    if hasattr(agent, "invoke"):
        return agent.invoke({"messages": [{"role": "user", "content": prompt}], "case": case})
    if callable(agent):
        return await maybe_await(agent(prompt))
    raise RuntimeError("ADK target must be callable or expose run/run_async/invoke/ainvoke.")


async def run_case(case: dict[str, Any]) -> dict[str, Any]:
    project_runner = os.environ.get("AGENT_ASSURANCE_ADK_RUNNER")
    agent_spec = os.environ.get("AGENT_ASSURANCE_ADK_AGENT")
    if project_runner:
        raw = await run_with_project_runner(case, project_runner)
    elif agent_spec:
        raw = await run_with_adk_agent(case, agent_spec)
    else:
        raise RuntimeError("Set AGENT_ASSURANCE_ADK_RUNNER or AGENT_ASSURANCE_ADK_AGENT.")
    return normalize_result(case, raw)


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

