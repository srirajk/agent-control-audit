# Google ADK Assurance Test Pathway

Use this pathway to prove the ADK-first story without needing the client's full AML platform.

## Level 0: Package Health

Run the skill self-test and validator. This proves the scanner, dataset importer, deterministic runner, DeepEval exporter, and package structure still work.

Expected evidence:

- `python3 -B tests/self_test.py` passes.
- Skill validator passes.
- No generated cache files are left in the skill package.

## Level 1: Static ADK Before/After Proof

Run static audit on the two ADK AML fixtures:

- `tests/fixtures/google_adk_aml_as_is/`: should route as `google_adk` and `block`.
- `tests/fixtures/google_adk_aml_guarded/`: should route as `google_adk` and `ship`.

This proves the skill can map missing controls in an ADK 1.x-style AML agent and recognize a source-visible remediation pattern.

## Level 2: Golden Dataset Readiness

Validate the AML golden dataset:

- `agent-control-audit/evals/datasets/aml_investigation_controls.jsonl`

This covers SAR approval, tipping-off prevention, evidence grounding, indirect prompt injection, and PII redaction. Client datasets can be JSONL, JSON, CSV, or XLSX; normalize them with `agent-control-audit/scripts/dataset_import.py` before generating DeepEval.

## Level 3: ADK Runner Adapter Contract

Run `agent-control-audit/scripts/eval_runner.py` against `agent-control-audit/runner_adapters/google_adk_1_adapter.py` using a project-owned runner function:

- `PYTHONPATH="$PWD/tests" AGENT_ASSURANCE_ADK_RUNNER=fixtures.google_adk_aml_guarded.eval_adapter:run_case`

This proves the ADK adapter contract can execute case-by-case and emit the required result JSON without tying the skill to one ADK application layout.

## Level 4: DeepEval Export

Export the AML dataset into a generated DeepEval pytest file. Run the generated file with deterministic gates only first:

- `AGENT_ASSURANCE_DEEPEVAL_JUDGE=0`

Then enable LLM-as-judge when `OPENAI_API_KEY` is configured:

- `AGENT_ASSURANCE_DEEPEVAL_JUDGE=1`

This proves the client-facing eval suite shape.

## Level 5: Live ADK + OpenAI Proof

When dependencies and `OPENAI_API_KEY` are configured, replace the deterministic fixture runner with a live project runner that invokes the actual ADK root agent and returns the same JSON contract.

Expected live-run evidence:

- final output
- tool calls
- blocked flag
- approval_requested flag
- citations/evidence IDs
- trace/session IDs when available
- guardrail denial reasons

The claim after Level 5 is stronger than static assurance: the ADK agent was actually invoked against golden AML cases.

## Level 6: HTTP Serving Proof

Use `examples/google_adk_aml_openai/` when the client wants to see an ADK 1.x-style agent that uses OpenAI and can be tested through a stable HTTP contract.

Options:

- Native ADK HTTP: run the ADK project with `adk api_server` and call ADK's `/run` endpoint.
- Assurance HTTP wrapper: run `PYTHONPATH="$PWD/examples/google_adk_aml_openai" python3 -m uvicorn adk_aml_openai.api.server:app --host 127.0.0.1 --port 8088` and call `/invoke`.

The wrapper is intentionally thin. It exists so the same normalized cases can be tested through the skill's HTTP/CLI runner contract even if the client's ADK deployment uses custom sessions or auth.

For live OpenAI-backed execution, configure `OPENAI_API_KEY` only in the local shell or approved secret store. The deterministic adapter path does not require a model key and is the default smoke-test route.
