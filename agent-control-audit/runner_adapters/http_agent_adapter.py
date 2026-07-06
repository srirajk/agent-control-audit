#!/usr/bin/env python3
"""Generic HTTP runner adapter for agent-control-audit evals.

Configure:
  AGENT_ASSURANCE_HTTP_URL="https://host/agent/invoke"
  AGENT_ASSURANCE_HTTP_METHOD="POST"
  AGENT_ASSURANCE_HTTP_AUTH_HEADER="Authorization: Bearer ..."

Optional response mapping:
  AGENT_ASSURANCE_HTTP_OUTPUT_FIELD="answer"
  AGENT_ASSURANCE_HTTP_TOOL_CALLS_FIELD="tool_calls"
  AGENT_ASSURANCE_HTTP_BLOCKED_FIELD="blocked"
  AGENT_ASSURANCE_HTTP_APPROVAL_FIELD="approval_requested"
  AGENT_ASSURANCE_HTTP_CITATIONS_FIELD="citations"
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


def field(data: dict[str, Any], name: str, default: Any = None) -> Any:
    current: Any = data
    for part in name.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def build_payload(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "input": case["input"],
        "case": case,
        "retrieved_doc": case.get("retrieved_doc"),
        "tool_result": case.get("tool_result"),
        "user_context": case.get("user_context", {}),
    }


def parse_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    raw = os.environ.get("AGENT_ASSURANCE_HTTP_AUTH_HEADER")
    if raw:
        name, value = raw.split(":", 1)
        headers[name.strip()] = value.strip()
    extra = os.environ.get("AGENT_ASSURANCE_HTTP_HEADERS")
    if extra:
        headers.update(json.loads(extra))
    return headers


def normalize_tool_calls(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        names: list[str] = []
        for item in value:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("tool") or item.get("function")
                if name:
                    names.append(str(name))
        return names
    return [str(value)]


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    url = os.environ.get("AGENT_ASSURANCE_HTTP_URL")
    if not url:
        raise RuntimeError("Set AGENT_ASSURANCE_HTTP_URL.")
    method = os.environ.get("AGENT_ASSURANCE_HTTP_METHOD", "POST").upper()
    timeout = int(os.environ.get("AGENT_ASSURANCE_HTTP_TIMEOUT", "60"))

    request = urllib.request.Request(
        url=url,
        method=method,
        data=json.dumps(build_payload(case), sort_keys=True).encode("utf-8"),
        headers=parse_headers(),
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")

    try:
        raw = json.loads(body)
    except json.JSONDecodeError:
        raw = {"observed_output": body}

    output_field = os.environ.get("AGENT_ASSURANCE_HTTP_OUTPUT_FIELD", "observed_output")
    tool_field = os.environ.get("AGENT_ASSURANCE_HTTP_TOOL_CALLS_FIELD", "tool_calls")
    blocked_field = os.environ.get("AGENT_ASSURANCE_HTTP_BLOCKED_FIELD", "blocked")
    approval_field = os.environ.get("AGENT_ASSURANCE_HTTP_APPROVAL_FIELD", "approval_requested")
    citations_field = os.environ.get("AGENT_ASSURANCE_HTTP_CITATIONS_FIELD", "citations")

    output = field(raw, output_field, None)
    if output is None:
        output = field(raw, "answer", field(raw, "output", field(raw, "message", "")))

    return {
        "id": case["id"],
        "suite": case["suite"],
        "observed_output": output if isinstance(output, str) else json.dumps(output, sort_keys=True, default=str),
        "tool_calls": normalize_tool_calls(field(raw, tool_field, [])),
        "blocked": bool(field(raw, blocked_field, False)),
        "approval_requested": bool(field(raw, approval_field, False)),
        "citations": field(raw, citations_field, []) or [],
        "notes": "http adapter",
    }


def main() -> int:
    case = json.load(sys.stdin)
    try:
        result = run_case(case)
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as exc:
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

