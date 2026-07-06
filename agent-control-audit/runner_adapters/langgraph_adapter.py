#!/usr/bin/env python3
"""LangGraph runner adapter for agent-control-audit evals.

Configure:
  AGENT_ASSURANCE_LANGGRAPH_APP="your_package.graph:compiled_graph"

The object should usually be a compiled graph with invoke/ainvoke. Interrupts
or pause payloads are reported as approval requests for the deterministic gate.
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
    content = case["input"]
    if case.get("retrieved_doc"):
        content += f"\n\nRetrieved document:\n{case['retrieved_doc']}"
    return {
        "messages": [{"role": "user", "content": content}],
        "case": case,
        "user_context": case.get("user_context", {}),
    }


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
        if "messages" in value and value["messages"]:
            return text_from(value["messages"][-1])
        for key in ("output", "content", "text", "answer", "final"):
            if key in value:
                return text_from(value[key])
        return json.dumps(value, sort_keys=True, default=str)
    content = getattr(value, "content", None)
    if content is not None:
        return text_from(content)
    return str(value)


def contains_interrupt(value: Any) -> bool:
    if isinstance(value, dict):
        if "__interrupt__" in value or "interrupt" in value or "human_input" in value:
            return True
        return any(contains_interrupt(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(contains_interrupt(v) for v in value)
    return "__interrupt__" in str(value).lower()


def tool_calls_from(value: Any) -> list[str]:
    calls: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key in ("tool", "tool_name", "name"):
                if key in item and item.get("type") in {None, "tool_call", "tool"}:
                    calls.append(str(item[key]))
            for nested in item.values():
                walk(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                walk(nested)
        else:
            tool_calls = getattr(item, "tool_calls", None)
            if tool_calls:
                walk(tool_calls)

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
    spec = os.environ.get("AGENT_ASSURANCE_LANGGRAPH_APP")
    if not spec:
        raise RuntimeError("Set AGENT_ASSURANCE_LANGGRAPH_APP='module:compiled_graph'.")

    graph = load_attr(spec)
    state = build_state(case)
    config = deepeval_config()

    if hasattr(graph, "ainvoke"):
        raw = await graph.ainvoke(state, config=config or None)
    elif hasattr(graph, "invoke"):
        raw = graph.invoke(state, config=config or None)
    elif callable(graph):
        raw = await maybe_await(graph(state))
    else:
        raise RuntimeError("Target object must be callable or expose invoke/ainvoke.")

    output = text_from(raw)
    return {
        "id": case["id"],
        "suite": case["suite"],
        "observed_output": output,
        "tool_calls": tool_calls_from(raw),
        "blocked": "blocked by guardrail" in output.lower(),
        "approval_requested": contains_interrupt(raw),
        "citations": raw.get("citations", []) if isinstance(raw, dict) else [],
        "notes": "langgraph adapter",
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
