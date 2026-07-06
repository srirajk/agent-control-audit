# OpenAI Agents SDK Adapter

Status: implemented for static source discovery.

Reference points verified from the OpenAI Agents SDK docs: agent input/output guardrails attach to agents; tool guardrails attach to function tools; tripwires halt execution; function tools infer schemas from Python signatures and Pydantic constraints; handoffs can use input filters and history mapping. Use the docs as API-shape context, but audit the repository source as evidence.

Primary docs:

- `https://openai.github.io/openai-agents-python/`
- `https://openai.github.io/openai-agents-python/guardrails/`
- `https://openai.github.io/openai-agents-python/tools/`
- `https://openai.github.io/openai-agents-python/handoffs/`

Current source surfaces to treat as first-class review objects include agents, agents-as-tools/handoffs, input/output/tool guardrails, function tools, MCP tools, sessions, tracing, human-in-the-loop approval flows, sandbox agents, realtime/voice workflows when present, and tool-output trimming.

## Static Scan

Prefer AST parsing for Python files. Fall back to text search only when parsing fails, and lower confidence accordingly.

Scan for:

- Imports from `agents`.
- `Agent(...)` declarations.
- `Runner.run(...)` and `Runner.run_sync(...)` entrypoints.
- `@input_guardrail`, `InputGuardrail(...)`, and `input_guardrails=[...]`.
- `@output_guardrail`, `OutputGuardrail(...)`, and `output_guardrails=[...]`.
- `GuardrailFunctionOutput(... tripwire_triggered=...)`.
- `@tool_input_guardrail`, `@tool_output_guardrail`, `ToolGuardrailFunctionOutput`, `tool_input_guardrails=[...]`, and `tool_output_guardrails=[...]`.
- `@function_tool(...)`, bare `@function_tool`, and `FunctionTool(...)`.
- Tool approval settings such as `needs_approval=...`, approval handlers, pending interruptions, `state.approve(...)`, `state.reject(...)`, and `RunConfig.tool_execution`.
- Hosted or local tools such as `FileSearchTool`, `WebSearchTool`, `HostedMCPTool`, `ComputerTool`, `ShellTool`, `ApplyPatchTool`, `LocalShellTool`, `CodeInterpreterTool`, and `ImageGenerationTool`.
- `handoff(...)`, `handoffs=[...]`, `Agent.as_tool(...)`, `input_filter=...`, `handoff_history_mapper`, and `nest_handoff_history`.
- Session/memory classes and persistent state, including SQLAlchemy, SQLite, Redis, MongoDB, Dapr, encrypted, or custom session stores.
- Tracing or logging hooks that record control decisions.
- Sandbox-agent manifests or isolated workspace configuration when specialist agents operate on files, tools, or code.
- Realtime or voice workflows that introduce streaming input/output, events, or separate safety boundaries.
- Prompt-injection, jailbreak, moderation, toxicity, rate/cost, timeout/fallback, metrics/alerting, red-team, eval, and benchmark evidence.

## Mapping To Catalog Controls

### Agent Input Guardrails

Map to `C001 Input Intent Policy` when the guardrail inspects initial user input and can tripwire or otherwise halt. Mark weak when:

- The guardrail only logs or annotates.
- It lacks a `tripwire_triggered` path.
- It is attached to a downstream handoff agent where SDK workflow boundaries mean it will not run on initial input.
- It checks generic safety only and does not cover the financial harm surface required by the regime.

### Agent Output Guardrails

Map to `C002 Output Recommendation Validation` when attached to the final-output agent and able to tripwire. Mark weak or misconfigured when:

- It is attached to an intermediate agent only.
- The agent output is unstructured and the guardrail cannot inspect the relevant fields.
- It checks style but not unsupported financial claims, grounding, or required policy conditions.

### Tool Guardrails And Validation

Map tool input guardrails to `C003`, `C004`, `C010`, or other relevant controls based on what they inspect. Tool guardrails are strongest when attached directly to `@function_tool(... tool_input_guardrails=[...])` or a `FunctionTool` equivalent before execution.

For `@function_tool` signatures:

- Type annotations and generated schemas count as syntax validation only.
- Pydantic `Field` constraints, enums, literals, custom validators, or manual checks in the tool body can support `C004`.
- Business checks such as user/account ownership, entitlement, destination allowlist, currency, amount limit, and idempotency are required for financial side-effect adequacy.

Map `needs_approval` and pause/resume approval flows to `C005 Human Approval Gate` when the approval gates the risky action. Mark weak when approval appears only around an agent-as-tool call while the underlying side-effecting function can still be called directly.

### Retrieval And Grounding

Map hosted retrieval tools, file search, web search, vector store usage, MCP retrieval, or document loaders to RAG architecture. Map explicit allowlists, tenant filters, vector-store restrictions, source freshness checks, or trusted-corpus selection to `C007`.

Map source-to-claim validation, citation verification, contradiction checks, or output guardrails that verify retrieved evidence to `C008`. Retrieval presence alone is not grounding.

### Data Controls

Map redaction before model calls, tool calls, logs, or final output to `C010`. Map field-level prompt/context filtering and scoped `RunContextWrapper.context` construction to `C009`.

Map session stores to memory architecture. For encrypted or persistent sessions, verify retention, tenant isolation, replay controls, minimization, and sensitive-data redaction before giving data-control credit.

### Logging And Tracing

Map structured, durable logging of approvals, denials, tool calls, handoffs, and guardrail trips to `C011`. Mark weak when evidence is limited to `print`, local debug logging, comments, or tracing that is not configured or exported.

### Jailbreak, Toxicity, And NFR Controls

Map prompt-injection and jailbreak controls to `C017` only when they are bound to all untrusted instruction channels in the workflow: user input, retrieved documents, files, web content, tool output, MCP results, and handoff payloads. Prompt text that says "ignore jailbreaks" or an input guardrail that checks only the initial user request is weak for RAG/tool/multi-agent systems.

Map moderation or content-safety guardrails to `C018` when they inspect customer input and final output. Mark weak when they only screen the first message or only rely on base-model safety behavior.

Map explicit rate limits, token/tool-call budgets, max turns, retry caps, quotas, throttles, and cost budgets to `C019`.

Map timeouts, bounded retries, circuit breakers, safe fallback responses, partial-result labeling, and duplicate-side-effect prevention to `C020`.

Map metrics, traces, structured logs, alerts, runbooks, and incident hooks for guardrail trips, denials, approvals, jailbreak attempts, leakage attempts, and eval regressions to `C021`. Tracing alone is weak unless it is configured and operationally consumed.

Map repeatable red-team/eval harnesses to `C022` when they test the full agent path rather than the base model alone. Look for CI/release gates, thresholds, pinned datasets, dataset hashes, model versions, and benign false-positive cases.

Realtime, voice, and sandbox-agent paths must have equivalent evals if they are production paths; do not let a text-only eval suite stand in for a streaming or sandboxed workflow.

### Handoffs

Map `handoff(...)`, `handoffs=[...]`, and `Agent.as_tool(...)` to multi-agent architecture.

- `C012`: destination allowlists, per-handoff policy checks, conditionally enabled handoffs, or scoped authority.
- `C013`: `input_filter`, `handoff_history_mapper`, nested history controls, or explicit payload construction/redaction.
- `C014`: `input_type`, `on_handoff`, trace/log metadata, reason codes, or durable handoff records.

Mark misconfigured when agent-level input/output guardrails are relied on for each handoff step even though SDK workflow boundaries mean they only run for the first input and final output. Prefer tool guardrails for checks around custom function-tool calls inside manager/handoff workflows.

## Architecture Extraction

Set architecture booleans from source evidence:

- `has_tools`: any function, hosted, local, MCP, computer, shell, code, or agent-as-tool declaration.
- `has_retrieval`: file search, web search, vector stores, document loaders, retrieval MCP tools, or instructions that route to retrieval tools.
- `has_handoffs`: `handoffs`, `handoff(...)`, `Agent.as_tool(...)`, or orchestrator-specialist patterns.
- `has_memory`: sessions, persistent stores, memory APIs, vector memory, or state passed across runs.

## Blind Spot Statement

Always return:

```text
Static pass cannot verify controls enforced outside the codebase, including deployment IAM, gateway policies, production approval queues, monitoring, human operating procedures, or runtime-only configuration.
```

If the code references external controls by name but their implementation is not in the repository, include them as `out_of_scope` evidence, not `present`.
