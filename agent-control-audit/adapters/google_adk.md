# Google ADK Adapter

Status: framework-aware static source discovery implemented; runtime proof still required.

Primary docs checked:

- `https://adk.dev/`
- `https://adk.dev/tools-custom/confirmation/`

ADK spans Python, TypeScript, Go, Java, and Kotlin. The adapter must handle both ADK 1.x-style agent/tool projects and ADK 2.0 graph/workflow projects. Route here only from ADK-specific imports, dependency metadata, ADK config, or ADK runtime/tool/workflow APIs; do not route from a bare `Agent(...)` without ADK context.

## Static Scan

Scan for:

- Agent declarations: `from google.adk import Agent`, `from google.adk.agents import LlmAgent`, `Agent(...)`, `LlmAgent(...)`, `root_agent = ...`, model/instruction/tools config, ADK app config, and `adk web`/API-server entrypoints.
- Tool declarations: `FunctionTool(...)`, function tools, `MCPToolset`, MCP tools, OpenAPI tools, built-in Google Search/grounding tools, auth config, `ToolContext`, and explicit credential handling.
- Confirmation and approval: `require_confirmation=True`, `require_confirmation=<callable>`, `RequireConfirmation`, `RequireConfirmationProvider`, `request_confirmation(...)`, `requestConfirmation(...)`, `tool_confirmation`, and remote confirmation response handling.
- Callbacks/plugins: before/after agent, model, and tool callbacks; plugin registration; safety/security plugins; tracing, logging, and metric plugins.
- Workflows: ADK 2.0 graph workflows, graph routes, human input, dynamic workflows, collaborative workflows, `SequentialAgent`, `ParallelAgent`, and `LoopAgent`.
- Sessions/context: session services, memory services, state, events, artifacts, context compression/caching, token usage, and deployed runtime config.
- Evaluation/observability: ADK evaluation criteria, user/environment simulation, custom metrics, logging, metrics, traces, and Cloud Trace or equivalent export.

## Mapping To Catalog Controls

- `C001 Input Intent Policy`: before-agent/model callbacks, safety plugins, policy middleware, or content filters that can stop unsupported financial/AML requests before model/tool execution. Instruction text alone is weak.
- `C002 Output Recommendation Validation`: after-agent/model callbacks, output schemas, final response validators, or safety plugins that can block unsupported financial advice, missing caveats, missing SAR escalation language, or ungrounded claims.
- `C003 Tool Authorization`: auth config, credential scoping, account ownership checks, entitlement checks, tenant filters, or `ToolContext` checks bound to every sensitive tool.
- `C004 Tool Argument Validation`: function schemas plus semantic checks for amount, currency, destination, jurisdiction, customer/account ownership, SAR/alert status, idempotency, and allowed action.
- `C005 Human Approval Gate`: ADK tool confirmation or workflow human input that pauses before side effects. For financial actions, confirmation must occur before the tool performs the side effect, not after.
- `C006 Transaction Limits And Kill Switch`: amount/frequency/recipient limits, risk limits, max steps/tool calls, cancel/resume controls, and fail-closed stop switches.
- `C007 Retrieval Scope Control`: approved corpora, Google Search grounding constraints, tenant filters, namespace/metadata filters, freshness windows, and source allowlists.
- `C008 Grounding Validation`: citation/source verification, source-to-claim checks, contradiction checks, or eval-backed grounding criteria.
- `C009/C010 Data Controls`: context minimization, artifact/event filtering, PII redaction, secret masking, and session/memory policies across prompts, tools, traces, and final output.
- `C011/C021 Observability`: durable logs/traces/metrics for tool calls, confirmations, denials, guardrail trips, workflow transitions, sessions, and incidents.
- `C012-C014 Workflow Boundaries`: route allowlists, workflow transition policies, input/state filtering between agents/nodes, handoff reasons, event provenance, and trace correlation.
- `C017/C018 Safety`: jailbreak, prompt-injection, toxicity, abuse, and unsafe-content checks bound to user input, tool output, retrieval content, artifacts, and inter-agent payloads.
- `C019/C020 NFRs`: rate limits, quotas, token budgets, timeout/retry/fallback, cancellation, resume safety, and degradation behavior.
- `C022 Evals`: ADK evaluations or external eval suites that invoke the full agent/workflow path with golden cases, adversarial cases, benign cases, thresholds, and regression evidence.

## Adequacy Traps

- A natural-language instruction to ask for approval is not a control unless ADK confirmation/human-input pauses the workflow before the side effect.
- Tool schemas are not enough for AML or payments; business semantics must be checked in code or a blocking guardrail.
- Callbacks/plugins must be attached to the agent/runtime that actually serves production traffic.
- Graph routes and collaborative workflows can bypass a control if only one branch/node has the guardrail.
- Session, memory, artifact, and event state can leak customer data unless minimization/redaction is explicit.
- Cloud/runtime-managed auth, observability, or safety should be marked `out_of_scope` unless represented in the repo or provided as deployment evidence.

## Live Eval Adapter

Use `runner_adapters/google_adk_1_adapter.py` for runner-style `Agent`/`LlmAgent` projects and `runner_adapters/google_adk_2_adapter.py` for graph/workflow projects. Capture final output, tool calls, confirmation pauses, workflow transitions, citations, guardrail denials, and trace/session IDs when available.
