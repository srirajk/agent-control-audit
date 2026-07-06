# Local Smoke Test

Run from the repository root.

## 1. Static Audit: Unsafe Fixture Should Block

```bash
python3 -B agent-control-audit/scripts/static_audit.py tests/fixtures/financial_agent
```

Expected:

- `framework`: `openai_agents_sdk`
- `decision`: `block`
- findings include missing authorization, approval, limits, jailbreak/toxicity controls, and eval gate evidence

## 2. Static Audit: Guarded Fixture Should Ship

```bash
python3 -B agent-control-audit/scripts/static_audit.py tests/fixtures/financial_agent_guarded
```

Expected:

- `framework`: `openai_agents_sdk`
- `decision`: `ship`
- no findings

## 2a. Static Audit: ADK AML As-Is Fixture Should Block

```bash
python3 -B agent-control-audit/scripts/static_audit.py tests/fixtures/google_adk_aml_as_is
```

Expected:

- `framework`: `google_adk`
- `decision`: `block`
- findings include missing approval, limits, jailbreak controls, and eval gate evidence

## 2b. Static Audit: ADK AML Guarded Fixture Should Ship

```bash
python3 -B agent-control-audit/scripts/static_audit.py tests/fixtures/google_adk_aml_guarded
```

Expected:

- `framework`: `google_adk`
- `decision`: `ship`
- no findings

## 3. Validate All Starter Datasets

```bash
python3 -B agent-control-audit/scripts/eval_runner.py \
  --validate-only \
  --dataset agent-control-audit/evals/datasets/benign_false_positives.jsonl \
  --dataset agent-control-audit/evals/datasets/financial_advice_traps.jsonl \
  --dataset agent-control-audit/evals/datasets/grounding_failures.jsonl \
  --dataset agent-control-audit/evals/datasets/jailbreak_direct.jsonl \
  --dataset agent-control-audit/evals/datasets/nfr_resilience.jsonl \
  --dataset agent-control-audit/evals/datasets/prompt_injection_indirect.jsonl \
  --dataset agent-control-audit/evals/datasets/sensitive_data_leakage.jsonl \
  --dataset agent-control-audit/evals/datasets/toxicity_and_abuse.jsonl \
  --dataset agent-control-audit/evals/datasets/unauthorized_tool_use.jsonl
```

Expected:

- `status`: `ok`
- `cases`: `18`

## 3a. Validate AML ADK Dataset

```bash
python3 -B agent-control-audit/scripts/eval_runner.py \
  --validate-only \
  --dataset agent-control-audit/evals/datasets/aml_investigation_controls.jsonl
```

Expected:

- `status`: `ok`
- `cases`: `5`

## 4a. Run Deterministic Live Eval Through ADK 1.x Adapter Contract

```bash
PYTHONPATH="$PWD/tests" \
AGENT_ASSURANCE_ADK_RUNNER="fixtures.google_adk_aml_guarded.eval_adapter:run_case" \
python3 -B agent-control-audit/scripts/eval_runner.py \
  --dataset agent-control-audit/evals/datasets/aml_investigation_controls.jsonl \
  --command "python3 -B agent-control-audit/runner_adapters/google_adk_1_adapter.py" \
  --out /tmp/agent_assurance_adk_aml_grades.jsonl \
  --summary /tmp/agent_assurance_adk_aml_summary.json
```

Expected:

- `total`: `5`
- `failed`: `0`
- `pass_rate`: `1.0`

## 4b. Run Deterministic Eval Against ADK OpenAI Example

```bash
PYTHONPATH="$PWD/examples/google_adk_aml_openai" \
AGENT_ASSURANCE_ADK_RUNNER="adk_aml_openai.assurance.eval_adapter:run_case" \
python3 -B agent-control-audit/scripts/eval_runner.py \
  --dataset agent-control-audit/evals/datasets/aml_investigation_controls.jsonl \
  --command "python3 -B agent-control-audit/runner_adapters/google_adk_1_adapter.py" \
  --out /tmp/agent_assurance_adk_openai_grades.jsonl \
  --summary /tmp/agent_assurance_adk_openai_summary.json
```

Expected:

- `total`: `5`
- `failed`: `0`
- `pass_rate`: `1.0`

## 4c. Optional HTTP Wrapper Smoke

ADK provides a native API server via `adk api_server`. The example also includes a tiny FastAPI wrapper with a stable `/invoke` contract for the skill's HTTP runner.

Start the wrapper from the repository root:

```bash
PYTHONPATH="$PWD/examples/google_adk_aml_openai" \
python3 -m uvicorn adk_aml_openai.api.server:app \
  --host 127.0.0.1 \
  --port 8088
```

Then run:

```bash
AGENT_ASSURANCE_HTTP_URL="http://127.0.0.1:8088" \
python3 -B agent-control-audit/scripts/eval_runner.py \
  --dataset agent-control-audit/evals/datasets/aml_investigation_controls.jsonl \
  --command "python3 -B examples/google_adk_aml_openai/http_adapter.py" \
  --out /tmp/agent_assurance_adk_http_grades.jsonl \
  --summary /tmp/agent_assurance_adk_http_summary.json
```

Expected:

- `total`: `5`
- `failed`: `0`
- `pass_rate`: `1.0`

## 5. Run Deterministic Live Eval Against Mock Agent

```bash
python3 -B agent-control-audit/scripts/eval_runner.py \
  --dataset agent-control-audit/evals/datasets/benign_false_positives.jsonl \
  --dataset agent-control-audit/evals/datasets/financial_advice_traps.jsonl \
  --dataset agent-control-audit/evals/datasets/grounding_failures.jsonl \
  --dataset agent-control-audit/evals/datasets/jailbreak_direct.jsonl \
  --dataset agent-control-audit/evals/datasets/nfr_resilience.jsonl \
  --dataset agent-control-audit/evals/datasets/prompt_injection_indirect.jsonl \
  --dataset agent-control-audit/evals/datasets/sensitive_data_leakage.jsonl \
  --dataset agent-control-audit/evals/datasets/toxicity_and_abuse.jsonl \
  --dataset agent-control-audit/evals/datasets/unauthorized_tool_use.jsonl \
  --command "python3 -B examples/mock_agent_command.py" \
  --out /tmp/agent_assurance_mock_grades.jsonl \
  --summary /tmp/agent_assurance_mock_summary.json
```

Expected:

- `total`: `18`
- `failed`: `0`
- `pass_rate`: `1.0`

## 6. Normalize A Client Dataset

```bash
python3 -B agent-control-audit/scripts/dataset_import.py \
  --in agent-control-audit/evals/datasets/jailbreak_direct.jsonl \
  --out /tmp/agent_assurance_imported.jsonl \
  --report /tmp/agent_assurance_import_report.json
```

Expected:

- `status`: `ok`
- `cases`: `2`

If the command returns `needs_client_input`, inspect the report and ask the client for the listed `client_questions`.

## 7. Export Default DeepEval Tests

```bash
python3 -B agent-control-audit/scripts/deepeval_export.py \
  --dataset agent-control-audit/evals/datasets/benign_false_positives.jsonl \
  --dataset agent-control-audit/evals/datasets/financial_advice_traps.jsonl \
  --dataset agent-control-audit/evals/datasets/grounding_failures.jsonl \
  --dataset agent-control-audit/evals/datasets/jailbreak_direct.jsonl \
  --dataset agent-control-audit/evals/datasets/nfr_resilience.jsonl \
  --dataset agent-control-audit/evals/datasets/prompt_injection_indirect.jsonl \
  --dataset agent-control-audit/evals/datasets/sensitive_data_leakage.jsonl \
  --dataset agent-control-audit/evals/datasets/toxicity_and_abuse.jsonl \
  --dataset agent-control-audit/evals/datasets/unauthorized_tool_use.jsonl \
  --out /tmp/test_agent_assurance_deepeval.py
```

Expected:

- generated DeepEval pytest file at `/tmp/test_agent_assurance_deepeval.py`
- no DeepEval install required for export; DeepEval is required when running the generated suite

To run the exported file later:

```bash
pip install deepeval pytest
AGENT_ASSURANCE_COMMAND="python3 -B examples/mock_agent_command.py" \
AGENT_ASSURANCE_DEEPEVAL_JUDGE=0 \
deepeval test run /tmp/test_agent_assurance_deepeval.py
```

Set `AGENT_ASSURANCE_DEEPEVAL_JUDGE=1` when model-provider credentials are configured and you want the LLM-as-judge metric.
