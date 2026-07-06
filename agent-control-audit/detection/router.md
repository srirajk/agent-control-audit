# Detection Router

The router prevents wrong-framework audits. It must run before discovery and must stop when it cannot route safely.

## Official Reference Links

Use these links for freshness checks before making "latest" claims:

- Google ADK: `https://adk.dev/`, `https://adk.dev/tools-custom/confirmation/`
- LangChain: `https://docs.langchain.com/oss/python/langchain/overview`, `https://docs.langchain.com/oss/python/langchain/guardrails`, `https://docs.langchain.com/oss/python/langchain/middleware/overview`
- LangGraph: `https://docs.langchain.com/oss/python/langgraph/overview`
- OpenAI Agents SDK: `https://openai.github.io/openai-agents-python/`, `https://openai.github.io/openai-agents-python/guardrails/`, `https://openai.github.io/openai-agents-python/tools/`, `https://openai.github.io/openai-agents-python/handoffs/`

## Existence Gate

1. Search for agent source files using `rg --files` or an equivalent fast file listing.
2. Include Python, TypeScript, JavaScript, notebooks, and configuration files in the scan when present.
3. Treat a repository as containing an agent only when there is evidence of an agent framework, LLM agent runner, tool-calling loop, graph, handoff, middleware-based agent, or named agent object.
4. If no agent evidence exists, stop with:

```text
no agent found: static audit did not locate an agent entrypoint or supported framework signal
```

## Framework Signals

### OpenAI Agents SDK

Strong signals:

- Python imports from `agents`, including `Agent`, `Runner`, `function_tool`, `input_guardrail`, `output_guardrail`, `tool_input_guardrail`, `tool_output_guardrail`, `GuardrailFunctionOutput`, `FunctionTool`, `handoff`, or `RunConfig`.
- Calls to `Agent(...)`, `Runner.run(...)`, `Runner.run_sync(...)`, `@function_tool`, `@input_guardrail`, `@output_guardrail`, `@tool_input_guardrail`, or `@tool_output_guardrail`.
- Project dependencies named `openai-agents` or equivalent local package metadata that imports as `agents`.

Weak signals:

- Generic `openai` imports without `agents` framework constructs.
- Prompts that mention agents but use no framework.

Route to `adapters/openai_agents_sdk.md` only with at least one strong signal.

### Google ADK

Strong signals:

- Imports from `google.adk`, `google.adk.agents`, `google.adk.tools`, ADK runner/session modules, or `@google/adk`.
- Python/TypeScript agent declarations such as `Agent(...)`, `LlmAgent(...)`, `root_agent = ...`, model/instruction/tools config, or ADK CLI/app config.
- Tool and approval constructs such as `FunctionTool(...)`, `require_confirmation=...`, `RequireConfirmation`, `request_confirmation(...)`, `requestConfirmation(...)`, `ToolContext`, MCP tools, OpenAPI tools, or ADK auth config.
- Workflow constructs such as `SequentialAgent`, `ParallelAgent`, `LoopAgent`, graph workflows, graph routes, human input, dynamic workflows, or collaborative agents.
- Sessions, memory, context, artifacts, events, callbacks, plugins, evaluation, logging, metrics, traces, or Safety/Security sections in project config.
- Dependency metadata for `google-adk`, `@google/adk`, `google.golang.org/adk`, or Google ADK Java/Kotlin artifacts.

When detected, route to `adapters/google_adk.md` and use framework-aware source discovery. State that ADK callback/plugin ordering, graph execution, hosted auth, session state, and deployed tool confirmation still require dynamic proof.

### LangGraph

Strong signals:

- Imports from `langgraph`, including `StateGraph`, `MessagesState`, `START`, `END`, graph nodes/edges, `Command`, `Send`, checkpointers, stores, memory, or `create_react_agent` from LangGraph prebuilt modules.
- Graph topology and runtime constructs such as `add_node`, `add_edge`, `add_conditional_edges`, `compile(checkpointer=...)`, `interrupt(...)`, `ToolNode`, subgraphs, streams/events, `MemorySaver`, or persistent stores.
- Dependency metadata for `langgraph`.

When detected, route to `adapters/langgraph.md` and use framework-aware source discovery. State that dynamic routing, interrupt/resume behavior, checkpoint/store contents, and deployed graph server config still require dynamic proof.

### LangChain

Strong signals:

- Imports from `langchain`, `langchain_core`, `langchain_community`, or `langchain_openai`.
- Calls to `create_agent(...)`, `AgentExecutor(...)`, LangChain tools, middleware, structured output, retrievers, or LangServe configuration.
- Middleware and guardrail constructs such as `HumanInTheLoopMiddleware`, `PIIMiddleware`, custom middleware hooks, `before_agent`, `after_agent`, `before_model`, `after_model`, `wrap_model_call`, retries, fallbacks, rate limits, or early termination.
- Tool and output constructs such as `@tool`, `StructuredTool`, `BaseTool`, `args_schema`, `InjectedToolArg`, `InjectedState`, `ProviderStrategy`, `ToolStrategy`, `response_format`, `structured_response`, or output parsers.
- Memory/eval/deployment constructs such as `RunnableWithMessageHistory`, short-term memory, long-term memory, LangSmith tracing/evaluation, or LangServe `add_routes`.
- Dependency metadata for `langchain`.

When detected, route to `adapters/langchain.md` and use framework-aware source discovery. State that middleware ordering, LangGraph-compiled execution, callback behavior, tool binding, and deployment semantics still require dynamic proof.

## Ambiguity Rules

- If multiple frameworks have strong signals, stop with `framework undetermined: multiple supported frameworks detected` and list the evidence.
- Exception: if the only combination is LangGraph plus LangChain, and explicit LangGraph constructs are present (`StateGraph`, graph nodes/edges, checkpointers, or LangGraph prebuilt agents), route to `adapters/langgraph.md`. LangGraph applications commonly depend on LangChain packages for models, messages, tools, and utilities; those dependency signals alone should not make the route ambiguous.
- Do not route Google ADK as OpenAI only because it contains a bare `Agent(...)`; require an OpenAI Agents SDK import or API-specific SDK signal.
- If only weak signals exist, stop with `framework undetermined: no supported framework signal`.
- Never route by file name alone.
- Never audit a detected framework with a different adapter.

## Discovery Contract

Every adapter returns one framework-blind object:

```json
{
  "framework": "openai_agents_sdk",
  "adapter_status": "implemented",
  "target": {
    "root": "<repo-root>",
    "entrypoints": ["<path>"],
    "agent_symbols": ["<symbol>"]
  },
  "controls_present": [
    {
      "control_id": "C001",
      "type": "input_guardrail",
      "location": "<file>:<line>",
      "symbol": "<name>",
      "inspects": "initial user input",
      "can_block": true,
      "evidence": "<short static evidence>",
      "adequacy_notes": "<coverage and limits>"
    }
  ],
  "architecture": {
    "has_tools": true,
    "has_retrieval": false,
    "has_handoffs": false,
    "has_memory": false,
    "notes": ["<evidence>"]
  },
  "blind_spots": [
    "Static pass cannot verify deployment IAM, gateway policies, production monitoring, or human procedures unless represented in source."
  ],
  "adapter_findings": []
}
```

If a future framework has no supported route, return the same top-level shape with `adapter_status: "not_implemented"`, no `controls_present`, and an adapter finding that stops the run.
