#!/usr/bin/env python3
"""LangChain runner adapter for agent-control-audit evals.

Configure:
  AGENT_ASSURANCE_LANGCHAIN_APP="your_package.agent:agent"

The object may be a Runnable with invoke/ainvoke, or a callable that accepts the
case payload. Set AGENT_ASSURANCE_ENABLE_DEEPEVAL_TRACE=1 to attach DeepEval's
LangChain callback handler when DeepEval is installed.
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


def build_payload(case: dict[str, Any]) -> dict[str, Any]:
    content = case["input"]
    if case.get("retrieved_doc"):
        content += f"\n\nRetrieved document:\n{case['retrieved_doc']}"
    if case.get("user_context"):
        content += "\n\nUser context JSON:\n" + json.dumps(case["user_context"], sort_keys=True)
    return {"messages": [{"role": "user", "content": content}], "case": case}


async def maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def text_from(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("output", "content", "text", "answer", "final"):
            if key in value:
                return text_from(value[key])
        if "messages" in value and value["messages"]:
            return text_from(value["messages"][-1])
        return json.dumps(value, sort_keys=True, default=str)
    content = getattr(value, "content", None)
    if content is not None:
        return text_from(content)
    return str(value)


def tool_calls_from(value: Any) -> list[str]:
    calls: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            if item.get("tool") or item.get("tool_name") or item.get("name"):
                if item.get("type") in {None, "tool_call", "tool"}:
                    calls.append(str(item.get("tool") or item.get("tool_name") or item.get("name")))
            for nested in item.values():
                walk(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                walk(nested)
        else:
            tool_calls = getattr(item, "tool_calls", None)
            if tool_calls:
                walk(tool_calls)
            name = getattr(item, "name", None) or getattr(item, "tool", None)
            if name and getattr(item, "type", None) in {None, "tool_call", "tool"}:
                calls.append(str(name))

    walk(value)
    return sorted(set(calls))


def deepeval_config() -> dict[str, Any]:
    if os.environ.get("AGENT_ASSURANCE_ENABLE_DEEPEVAL_TRACE") != "1":
        return {}
    try:
        from deepeval.integrations.langchain import CallbackHandler
    except Exception:
        return {}
    return {"callbacks": [CallbackHandler()]}


async def run_case(case: dict[str, Any]) -> dict[str, Any]:
    spec = os.environ.get("AGENT_ASSURANCE_LANGCHAIN_APP")
    if not spec:
        raise RuntimeError("Set AGENT_ASSURANCE_LANGCHAIN_APP='module:runnable_or_callable'.")

    app = load_attr(spec)
    payload = build_payload(case)
    config = deepeval_config()

    if hasattr(app, "ainvoke"):
        raw = await app.ainvoke(payload, config=config or None)
    elif hasattr(app, "invoke"):
        raw = app.invoke(payload, config=config or None)
    elif callable(app):
        raw = await maybe_await(app(payload))
    else:
        raise RuntimeError("Target object must be callable or expose invoke/ainvoke.")

    output = text_from(raw)
    return {
        "id": case["id"],
        "suite": case["suite"],
        "observed_output": output,
        "tool_calls": tool_calls_from(raw),
        "blocked": "blocked by guardrail" in output.lower(),
        "approval_requested": "approval" in output.lower() and "required" in output.lower(),
        "citations": raw.get("citations", []) if isinstance(raw, dict) else [],
        "notes": "langchain adapter",
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
