# Golden Dataset Schema

Store eval datasets as JSON Lines files in `evals/datasets/`. One line is one case.

When a client supplies JSONL, JSON, CSV, or XLSX, first read `evals/client_dataset_intake.md`, then normalize with:

```bash
python3 -B scripts/dataset_import.py \
  --in /path/to/client_cases.csv \
  --out /tmp/client_cases.normalized.jsonl \
  --report /tmp/client_cases.report.json
```

If required fields are missing, the importer reports `needs_client_input`. Do not use incomplete rows to generate DeepEval tests. If the rows parse but the quality report says `structurally_valid_but_coverage_thin`, run the cases only as exploratory calibration and do not call the dataset governance-grade evidence.

## Required Fields

- `id`: stable case id, unique across all datasets.
- `suite`: one of the suite names in `engine/eval_framework.md`.
- `input`: user prompt or task.
- `expected`: expected behavior label, such as `block`, `allow`, `request_approval`, `answer_with_citations`, or `safe_fallback`.
- `must_not`: list of forbidden observable outcomes.
- `severity`: `blocker`, `high`, `medium`, or `low`.
- `source`: `author_policy`, `synthetic_seed`, `incident`, `external_benchmark`, or another explicit source.

## Optional Fields

- `retrieved_doc`: untrusted retrieved text to inject into RAG context.
- `tool_result`: untrusted tool output to inject into the agent context.
- `user_context`: synthetic user/account context for authorization checks.
- `allowed_tools`: tool names that may be called.
- `forbidden_tools`: tool names that must not be called.
- `required_phrases`: phrases or regex-like substrings expected in output.
- `forbidden_phrases`: phrases or regex-like substrings forbidden in output.
- `expected_citations`: citation/source requirements.
- `max_tool_calls`: max permitted tool calls.
- `metadata`: object for tags, rationale, and owner.

For governance-grade client datasets, prefer metadata fields such as `owner`, `reviewer`, `approved_by`, `version`, `dataset_version`, `reviewed_at`, and `approved_at`.

## Runner Contract

A runner result should include:

- `id`
- `suite`
- `passed`
- `observed_output`
- `tool_calls`
- `blocked`
- `approval_requested`
- `citations`
- `notes`

When a live agent runner is unavailable, use transcript/result JSON to test the grader. Do not claim runtime assurance unless the dataset was executed against the real agent path.

Supported live invocation paths are HTTP, MCP stdio, SDK/framework adapters, or a project-owned command wrapper. DeepEval-generated suites and the smoke runner both use the same command contract; the adapter owns the protocol-specific details.
