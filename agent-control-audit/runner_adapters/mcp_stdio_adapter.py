#!/usr/bin/env python3
"""Generic MCP stdio runner adapter for agent-control-audit evals.

Configure:
  AGENT_ASSURANCE_MCP_COMMAND='python server.py'
  AGENT_ASSURANCE_MCP_TOOL='agent_invoke'

The MCP tool should accept a JSON object containing the eval case and return
either plain text or a result JSON object with observed_output/tool_calls/etc.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any


def rpc(method: str, params: dict[str, Any], request_id: int) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


def read_response(process: subprocess.Popen[str]) -> dict[str, Any]:
    assert process.stdout is not None
    line = process.stdout.readline()
    if not line:
        raise RuntimeError("MCP server closed stdout")
    return json.loads(line)


def write_request(process: subprocess.Popen[str], message: dict[str, Any]) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(message, sort_keys=True) + "\n")
    process.stdin.flush()


def normalize_content(result: Any) -> Any:
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict):
                text = first.get("text")
                if text:
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return text
        return content
    return result


def normalize_result(case: dict[str, Any], raw: Any) -> dict[str, Any]:
    raw = normalize_content(raw)
    if isinstance(raw, dict) and "observed_output" in raw:
        raw.setdefault("id", case["id"])
        raw.setdefault("suite", case["suite"])
        raw.setdefault("tool_calls", [])
        raw.setdefault("blocked", False)
        raw.setdefault("approval_requested", False)
        raw.setdefault("citations", [])
        raw.setdefault("notes", "mcp stdio adapter")
        return raw
    return {
        "id": case["id"],
        "suite": case["suite"],
        "observed_output": raw if isinstance(raw, str) else json.dumps(raw, sort_keys=True, default=str),
        "tool_calls": [],
        "blocked": False,
        "approval_requested": False,
        "citations": [],
        "notes": "mcp stdio adapter",
    }


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    command = os.environ.get("AGENT_ASSURANCE_MCP_COMMAND")
    tool = os.environ.get("AGENT_ASSURANCE_MCP_TOOL")
    if not command or not tool:
        raise RuntimeError("Set AGENT_ASSURANCE_MCP_COMMAND and AGENT_ASSURANCE_MCP_TOOL.")

    timeout = int(os.environ.get("AGENT_ASSURANCE_MCP_TIMEOUT", "60"))
    process = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        write_request(process, rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "agent-control-audit", "version": "1.0"}}, 1))
        read_response(process)
        write_request(process, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        write_request(process, rpc("tools/call", {"name": tool, "arguments": {"case": case, "input": case["input"]}}, 2))
        response = read_response(process)
        if "error" in response:
            raise RuntimeError(response["error"])
        return normalize_result(case, response.get("result"))
    finally:
        try:
            process.terminate()
            process.wait(timeout=timeout)
        except Exception:
            process.kill()


def main() -> int:
    case = json.load(sys.stdin)
    try:
        result = run_case(case)
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

