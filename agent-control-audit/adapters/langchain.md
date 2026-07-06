# LangChain Adapter

Status: framework-aware static source discovery implemented; runtime proof still required.

Primary docs checked:

- `https://docs.langchain.com/oss/python/langchain/overview`
- `https://docs.langchain.com/oss/python/langchain/guardrails`
- `https://docs.langchain.com/oss/python/langchain/middleware/overview`

This adapter targets modern LangChain agent projects built around `create_agent`, tools, middleware, structured output, retrieval, memory, LangServe, and LangSmith. LangChain agents may compile to LangGraph internally; route to LangGraph only when explicit LangGraph graph constructs are present.

## Static Scan

Scan for:

- Agent harnesses: `from langchain.agents import create_agent`, `create_agent(...)`, `AgentExecutor`, model/tool/prompt/middleware config, and invoke/ainvoke/stream entrypoints.
- Tools: `@tool`, `StructuredTool`, `BaseTool`, `args_schema`, `InjectedToolArg`, `InjectedState`, `InjectedStore`, tool binding, MCP tools, and LangServe exposed routes.
- Middleware and guardrails: `HumanInTheLoopMiddleware`, `PIIMiddleware`, custom middleware, before/after agent hooks, before/after/wrap model hooks, retries, fallbacks, rate limits, early termination, and content filters.
- Structured output: `response_format`, `structured_response`, `ProviderStrategy`, `ToolStrategy`, Pydantic models, JSON/Pydantic parsers, and final validators.
- Retrieval/grounding: retrievers, vector stores, RAG chains, document loaders, source metadata filters, citation validators, and grounding metrics.
- Memory/context: short-term memory, long-term memory, `RunnableWithMessageHistory`, summarization/context middleware, and history trimming.
- Evals/observability: LangSmith tracing/evaluation, tests, golden datasets, DeepEval, benchmark thresholds, callbacks, run IDs, alerts, and deployment config.

## Mapping To Catalog Controls

- `C001 Input Intent Policy`: before-agent/model middleware, custom guardrails, prompt-injection/content filters, or deterministic request policy checks that can stop the agent loop.
- `C002 Output Recommendation Validation`: after-agent middleware, structured output validators, schema strategies, final-response guardrails, and grounding/citation validators.
- `C003 Tool Authorization`: per-tool subject/account/action authorization, credential scoping, injected state/store controls, and protected tool arguments.
- `C004 Tool Argument Validation`: Pydantic schemas, `args_schema`, enums/literals, field validators, and financial semantic checks.
- `C005 Human Approval Gate`: `HumanInTheLoopMiddleware` or equivalent interrupt/approval flow that matches the risky tool name and pauses before execution.
- `C007/C008 Retrieval Controls`: scoped retrievers, source allowlists, metadata filters, freshness constraints, citation checks, and faithfulness/grounding tests.
- `C009/C010 Data Controls`: PII middleware, redaction/masking/hashing/blocking, context trimming, summarization, log sanitization, and output redaction.
- `C017/C018 Safety`: prompt-injection, jailbreak, toxicity, abuse, and content-safety middleware across user input, retrieved documents, tool outputs, and final output.
- `C019/C020 NFRs`: middleware or runtime config for rate limits, quotas, max iterations, token budgets, retries, fallbacks, timeouts, and safe degradation.
- `C021/C022 Evidence`: LangSmith traces/evaluations, DeepEval/pytest suites, golden datasets, thresholds, model/dataset hashes, and release gates.

## Adequacy Traps

- Middleware order matters; a guardrail after tool execution does not protect a side-effecting tool.
- `HumanInTheLoopMiddleware` must match the exact tool names exposed to the agent.
- Structured output does not prove financial correctness unless the fields are validated for policy and grounding.
- `PIIMiddleware` must cover output, tool arguments/results, and logs where those paths can carry sensitive data.
- LangServe or custom HTTP wrappers can bypass local invoke paths; inspect deployment entrypoints.
- LangSmith tracing is evidence capture, not a guardrail, unless connected to alerting/release gates.

## Live Eval Adapter

Use `runner_adapters/langchain_adapter.py`. Invoke the same `invoke`/`ainvoke`/LangServe path used by the app, and capture final output, tool calls, middleware/approval events, retrieval sources, structured response, and trace IDs.
