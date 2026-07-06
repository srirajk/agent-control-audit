# Runner Adapter Examples

Each adapter reads one golden eval case from stdin and writes one result JSON to stdout. That is the only contract the deterministic runner needs.

Run these commands from the repository root.

Use the mock command first:

```bash
python3 -B agent-control-audit/scripts/eval_runner.py \
  --dataset agent-control-audit/evals/datasets/jailbreak_direct.jsonl \
  --command "python3 -B examples/mock_agent_command.py"
```

Then point the relevant adapter at the real target. Prefer the simplest real access path the client can expose.

Secrets:

- Static audit does not need API keys.
- Dynamic invocation uses the target repo's normal credentials.
- Set keys locally with environment variables or the target repo's `.env`.
- Do not commit, print, normalize, or render API keys.

HTTP:

```bash
AGENT_ASSURANCE_HTTP_URL="https://example.com/agent/invoke" \
AGENT_ASSURANCE_HTTP_AUTH_HEADER="Authorization: Bearer REDACTED" \
python3 -B agent-control-audit/scripts/eval_runner.py \
  --dataset agent-control-audit/evals/datasets/jailbreak_direct.jsonl \
  --command "python3 -B agent-control-audit/runner_adapters/http_agent_adapter.py"
```

MCP stdio:

```bash
AGENT_ASSURANCE_MCP_COMMAND="python3 path/to/mcp_server.py" \
AGENT_ASSURANCE_MCP_TOOL="agent_invoke" \
python3 -B agent-control-audit/scripts/eval_runner.py \
  --dataset agent-control-audit/evals/datasets/jailbreak_direct.jsonl \
  --command "python3 -B agent-control-audit/runner_adapters/mcp_stdio_adapter.py"
```

SDK/framework:

```bash
AGENT_ASSURANCE_OPENAI_AGENT="my_app.agent:root_agent" \
python3 -B agent-control-audit/scripts/eval_runner.py \
  --dataset agent-control-audit/evals/datasets/jailbreak_direct.jsonl \
  --command "python3 -B agent-control-audit/runner_adapters/openai_agents_adapter.py"
```

Framework environment variables:

- HTTP: `AGENT_ASSURANCE_HTTP_URL`, optional auth/header and response-field env vars.
- MCP stdio: `AGENT_ASSURANCE_MCP_COMMAND` and `AGENT_ASSURANCE_MCP_TOOL`.
- OpenAI Agents SDK: `AGENT_ASSURANCE_OPENAI_AGENT="module:agent_object"`.
- LangChain: `AGENT_ASSURANCE_LANGCHAIN_APP="module:runnable_or_callable"`.
- LangGraph: `AGENT_ASSURANCE_LANGGRAPH_APP="module:compiled_graph"`.
- Google ADK 1.x: `AGENT_ASSURANCE_ADK_RUNNER="module:function"` or `AGENT_ASSURANCE_ADK_AGENT="module:root_agent"`.
- Google ADK 2.0 graph workflows: `AGENT_ASSURANCE_ADK_WORKFLOW="module:workflow"`.

DeepEval tracing toggle:

```bash
AGENT_ASSURANCE_ENABLE_DEEPEVAL_TRACE=1 ...
```

Keep project-specific logic in the app repo when the framework runner needs auth/session setup. The best adapter for production evals is often a tiny project-owned wrapper that returns the result JSON directly.
