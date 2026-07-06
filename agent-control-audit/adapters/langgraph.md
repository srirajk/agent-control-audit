# LangGraph Adapter

Status: framework-aware static source discovery implemented; runtime proof still required.

Primary docs checked:

- `https://docs.langchain.com/oss/python/langgraph/overview`

LangGraph is a low-level orchestration/runtime for long-running stateful agents. It commonly imports LangChain models, messages, tools, and utilities; when explicit graph constructs exist, route to LangGraph even if LangChain imports are also present.

## Static Scan

Scan for:

- Graph definitions: `StateGraph`, `MessagesState`, `START`, `END`, `add_node`, `add_edge`, `add_conditional_edges`, compiled graphs, and graph server entrypoints.
- Control flow: `Command`, `Send`, conditional route functions, node policies, subgraphs, supervisor/router nodes, and explicit allowlists.
- Human-in-loop: `interrupt(...)`, resume/update commands, approval nodes, pending action state, and UI/API human-input bridges.
- Tools/retrieval: `ToolNode`, `create_react_agent`, tool calls inside nodes, retrievers, vector stores, source filters, and citation validators.
- State and memory: typed state, `TypedDict`, annotations, reducers, checkpointers, stores, `MemorySaver`, persistent checkpoint backends, user/session/thread IDs, and long-term memory.
- Runtime/NFRs: recursion limits, max steps, event streaming, retries, timeouts, cancellation, durable execution, rollback, and fault tolerance.
- Evidence: LangSmith traces/evals, graph event streams, node transition logs, test graphs, golden datasets, and regression gates.

## Mapping To Catalog Controls

- `C001/C002`: input/output policy nodes, pre/post-model nodes, route-level guardrails, structured final validators, and fail-closed terminal nodes.
- `C003/C004`: authorization and semantic argument validation inside every tool node or immediately upstream of it.
- `C005`: `interrupt(...)` or approval nodes that pause before risky side effects and resume only with approved state.
- `C006`: graph-level recursion limits, transaction/risk limits, and kill/cancel paths before external writes.
- `C007/C008`: retrieval nodes with tenant/source/freshness filters plus downstream grounding/citation validators.
- `C009/C010`: typed state minimization, payload filters, state reducers, PII redaction, checkpoint/store filtering, and trace sanitization.
- `C011/C014/C021`: node transition logs, event streams, route reasons, trace IDs, durable audit records, and operational alerts.
- `C012/C013`: route allowlists, conditional edge policies, subgraph boundaries, scoped state handoff, and payload sanitization.
- `C017/C018`: prompt-injection/jailbreak/content-safety checks for user input, retrieved content, tool output, and inter-node state.
- `C019/C020`: recursion limits, timeouts, retries, fallbacks, cancellation/resume safety, and fault-tolerance behavior.
- `C022`: graph-level tests/evals that invoke the compiled graph and assert final output plus intermediate interrupts/tool events.

## Adequacy Traps

- A guardrail node is weak if conditional routing lets risky branches bypass it.
- `interrupt(...)` is only an approval gate if the risky action has not happened yet and resume validates the approval payload.
- Checkpointers/stores can retain sensitive customer data; minimization must cover persisted state, not only prompts.
- ToolNode wrappers can hide real side effects; inspect the underlying tool functions.
- Graph tests that call isolated nodes are not enough for assurance; evals must exercise the compiled graph path.
- Event streaming/tracing is not observability unless records are durable, correlated, and monitored.

## Live Eval Adapter

Use `runner_adapters/langgraph_adapter.py`. Invoke the compiled graph, pass configurable thread/session IDs, capture interrupts/resume points, node transitions, tool calls, retrieval citations, final output, checkpoint IDs, and trace IDs.
