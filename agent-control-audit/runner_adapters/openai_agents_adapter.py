#!/usr/bin/env python3
"""OpenAI Agents SDK runner adapter for agent-control-audit evals.

Configure:
  AGENT_ASSURANCE_OPENAI_AGENT="your_package.agent:root_agent"

Then run:
  python3 -B scripts/eval_runner.py \
    --dataset evals/datasets/jailbreak_direct.jsonl \
    --command "python3 -B runner_adapters/openai_agents_adapter.py"
"""

from __future__ import annotations

import asyncio
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


def build_input(case: dict[str, Any]) -> str:
    parts = [case["input"]]
    if case.get("retrieved_doc"):
        parts.append(f"\nRetrieved document:\n{case['retrieved_doc']}")
    if case.get("user_context"):
        parts.append("\nUser context JSON:\n" + json.dumps(case["user_context"], sort_keys=True))
    return "\n".join(parts)


def extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("final_output", "output", "content", "text", "message"):
            if key in value:
                return extract_text(value[key])
        return json.dumps(value, sort_keys=True, default=str)
    for attr in ("final_output", "output", "content", "text"):
        if hasattr(value, attr):
            return extract_text(getattr(value, attr))
    return str(value)


def extract_tool_calls(value: Any) -> list[str]:
    calls: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            if item.get("type") in {"tool_call", "function_call"}:
                name = item.get("name") or item.get("tool") or item.get("function")
                if name:
                    calls.append(str(name))
            for nested in item.values():
                walk(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                walk(nested)
        else:
            name = getattr(item, "name", None) or getattr(item, "tool_name", None)
            item_type = getattr(item, "type", None)
            if item_type in {"tool_call", "function_call"} and name:
                calls.append(str(name))
            for attr in ("new_items", "items", "raw_responses"):
                if hasattr(item, attr):
                    walk(getattr(item, attr))

    walk(value)
    return sorted(set(calls))


async def run_case(case: dict[str, Any]) -> dict[str, Any]:
    try:
        from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered, Runner
    except Exception as exc:  # pragma: no cover - example depends on caller environment
        raise RuntimeError("Install and configure the OpenAI Agents SDK in the target app environment.") from exc

    spec = os.environ.get("AGENT_ASSURANCE_OPENAI_AGENT")
    if not spec:
        raise RuntimeError("Set AGENT_ASSURANCE_OPENAI_AGENT='module:agent_object'.")

    agent = load_attr(spec)
    try:
        result = await Runner.run(agent, build_input(case), context=case.get("user_context"))
        return {
            "id": case["id"],
            "suite": case["suite"],
            "observed_output": extract_text(result),
            "tool_calls": extract_tool_calls(result),
            "blocked": False,
            "approval_requested": "__interrupt__" in extract_text(result).lower(),
            "citations": getattr(result, "citations", []) or [],
            "notes": "openai agents adapter",
        }
    except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered) as exc:
        return {
            "id": case["id"],
            "suite": case["suite"],
            "observed_output": "Blocked by guardrail.",
            "tool_calls": [],
            "blocked": True,
            "approval_requested": False,
            "citations": [],
            "notes": type(exc).__name__,
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
