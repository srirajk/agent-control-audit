# Eval Framework Adapter Pattern

Use DeepEval as the default generated suite for client-facing assurance. Keep the skill's canonical dataset/result schema underneath it so the same cases can be rendered into other eval frameworks when required.

## Layers

1. Canonical case schema: `evals/dataset_schema.md`
2. Invocation adapter: HTTP, MCP stdio, SDK/framework, or project-owned command wrapper
3. Result schema: `observed_output`, `tool_calls`, `blocked`, `approval_requested`, `citations`, `notes`
4. Hard assertions: deterministic checks for forbidden tools, skipped approval, leakage, grounding, required phrases, max tool calls, and overblocking
5. Eval framework renderer: DeepEval by default; other frameworks by explicit request or client standard

This separation is required. Do not bake agent invocation or client data normalization directly into a DeepEval metric. Keep them as adapters so the same suite can run against different agent access paths.

## Default Renderer: DeepEval

Generate DeepEval tests whenever the user asks to create evals, golden tests, or client-facing validation artifacts.

Use DeepEval for:

- `LLMTestCase` and dataset/golden representation.
- `assert_test` and `deepeval test run` execution.
- Built-in agent, tool-use, RAG, safety, and custom GEval/DAG metrics.
- Framework tracing for supported stacks such as OpenAI Agents SDK, LangChain, LangGraph, Google ADK, LlamaIndex, CrewAI, Pydantic AI, Strands, and AWS AgentCore.
- Client-facing reports where DeepEval/Confident AI is acceptable.

Always include deterministic gates in the generated DeepEval test file before LLM-as-judge metrics. A DeepEval score must not pass a case that executed a forbidden tool, skipped approval, or violated a structured policy gate. Phrase checks, simple leakage patterns, and output-substring assertions are useful smoke checks, but they must be labeled as text fallbacks rather than semantic proof.

## Secondary Renderers

Add renderers only when the client requires them or when the target risk calls for a specialized framework.

- Ragas: RAG-specific retrieval/generation quality, faithfulness, context precision/recall, and response relevancy.
- LangSmith: LangChain/LangGraph dataset experiments, hosted tracing, and evaluator workflows.
- Promptfoo: declarative prompt/app tests, red-team scans, language-agnostic providers, and adversarial testing.
- Inspect AI: agentic benchmark tasks, external agents, MCP tools, sandboxed evaluations, and model/provider comparisons.
- garak: vulnerability scanning and security probing for LLM applications.
- Arize Phoenix: observability/tracing plus evaluation workflows for LLM apps.

Do not replace DeepEval with a secondary renderer unless the client explicitly standardizes on it. Prefer "DeepEval plus specialized renderer" over "specialized renderer only."

## Renderer Interface

Every renderer should accept:

- `dataset_paths`: one or more canonical JSONL files.
- `command`: target invocation command that accepts one case JSON on stdin and emits result JSON.
- `out`: generated framework-specific artifact.
- `hard_gates`: enabled by default.
- `judge_metrics`: optional LLM-as-judge or framework metrics.

Every generated suite should expose:

- How to run it.
- Required environment variables.
- Dataset hash or source paths.
- Hard gate assertions.
- Framework metrics and thresholds.
- Result/report location.

## Current Implementation

- `scripts/deepeval_export.py`: default DeepEval renderer.
- `scripts/eval_runner.py`: deterministic smoke runner and hard-gate reference implementation.
- `runner_adapters/*.py`: invocation adapters used by either DeepEval-generated suites or the smoke runner.
