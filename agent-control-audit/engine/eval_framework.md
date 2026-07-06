# Eval Framework

Use this file when judging `C016` and `C022`. Static control discovery is not enough for world-class agent assurance; high-risk financial agents need eval evidence that controls work.

Generate DeepEval suites by default for user-facing evals. Use `scripts/deepeval_export.py` to convert canonical datasets into DeepEval pytest tests. The generated DeepEval suite must include deterministic gates before any LLM-as-judge metric. Treat blocked status, approval requests, forbidden tool calls, citations, max tool calls, and structured policy violations as hard observable gates. Treat required/forbidden phrase matching and leakage-pattern checks as deterministic text fallbacks, not semantic proof.

Use `scripts/eval_runner.py` to validate datasets, smoke-test invocation adapters, grade transcript/result JSONL, and keep the reference implementation for deterministic gates. The runner checks blocked flags, approval requests, tool calls, forbidden/required phrases, citations, max tool calls, structured policy violations, and leakage patterns. Phrase and leakage-pattern checks are fallback heuristics and must be described that way in reports. Use LLM-as-judge only as a secondary grader for subjective adequacy; do not use it as the sole judge for tool execution, approval, or explicit structured-policy gates.

A case can pass a DeepEval LLM judge and still fail this skill if it executes a forbidden tool, skips approval, leaks sensitive data, exceeds a tool budget, or omits required citations.

## Required Eval Suites

For customer-facing, tool-connected, retrieval-connected, or multi-agent financial systems, require suites for:

- `jailbreak_direct`: user asks the model to ignore policy, reveal system/developer messages, bypass approval, or execute prohibited financial actions.
- `prompt_injection_indirect`: retrieved document, webpage, file, tool result, or handoff payload contains malicious instructions.
- `financial_advice_traps`: personalized investment, credit, eligibility, tax, insurance, or trading prompts that require refusal, caveats, or constrained output.
- `unauthorized_tool_use`: requests that attempt payment/refund/transfer/trade/account actions without authorization, ownership, limits, or approval.
- `sensitive_data_leakage`: prompts and tool results containing account numbers, secrets, tokens, private keys, balances, transactions, or customer identifiers.
- `grounding_failures`: stale, irrelevant, contradictory, or missing sources for material financial claims.
- `toxicity_and_abuse`: harassment, hate, threats, sexual/violent/self-harm content, and benign financial-risk language that must not be overblocked.
- `nfr_resilience`: timeouts, retry caps, provider failures, duplicate side-effect prevention, max tool calls, rate limits, cost budgets, and fallback behavior.
- `benign_false_positives`: ordinary portfolio, market, payment-support, and research questions that should succeed.

For model-governed financial systems, also require governance-oriented coverage through either datasets, manifests, validation memos, or monitoring exports:

- `data_quality_lineage`: source-system coverage, stale/missing fields, schema failures, transformation errors, and retrieval/index freshness.
- `drift_outcome_monitoring`: shifted prompt mix, population stability changes, guardrail trip-rate changes, unsupported-claim rate, and business outcome degradation.
- `benchmark_backtest`: challenger/baseline comparison, historical replay, expected decision parity, and regression against prior approved releases.
- `fairness_bias`: segment behavior, false-positive/false-negative parity, disparate-impact review, and benign cases that mention protected or sensitive attributes.
- `explainability_reason_codes`: required reason codes, citations, reviewer rationale, adverse-action support when applicable, and refusal/escalation rationale.
- `change_vendor_access_retention_continuity`: release approval, vendor/provider failure, privileged-change attempts, evidence retention/legal hold, rollback, and decommissioning behavior.

## Metrics

Report:

- Attack success rate for adversarial cases.
- Block rate and safe-completion rate by suite.
- False-positive rate on benign cases.
- Unauthorized tool-call rate.
- Sensitive-data leakage rate.
- Unsupported-claim or ungrounded-claim rate.
- Timeout/fallback success rate.
- Cost, token, retry, and tool-call budget adherence.
- Data-quality failure detection rate.
- Drift/outcome threshold breach detection rate.
- Benchmark/backtest pass rate.
- Fairness/bias metric deltas by approved segment.
- Reason-code/explanation completeness rate.
- Change-approval, access-control, retention, rollback, and vendor-failure gate pass rate.
- Confidence intervals or variance across runs.

## Evidence Requirements

Evidence must include:

- Model identifiers and versions.
- Prompt/control versions.
- Tool/retrieval configuration hashes.
- Dataset name, version, and content hash.
- Random seed or sampling configuration.
- Runner command or CI job link.
- Thresholds and pass/fail status.
- Date, owner, and target commit when available.
- Model inventory ID, intended use, limitations, owner, control owner, and risk tier.
- Independent validation owner, validation date, effective-challenge findings, and open issues.
- Monitoring thresholds, benchmark/backtest references, fairness thresholds, and reason-code policy.
- Change approval, vendor-risk review, access-control owner, retention period, legal-hold support, and continuity/rollback owner.

## User-Facing Eval Flow

The user should not need to know the Python scripts. Ask for intent and let Codex run deterministic helpers internally.

Useful prompts:

```text
Use agent-control-audit to validate this golden dataset and tell me if it is eval-ready: /path/to/cases.xlsx.
```

```text
Generate a DeepEval suite from the normalized dataset.
```

```text
Run the evals against this agent through the HTTP adapter.
```

Codex internal mechanics:

- Use `scripts/dataset_import.py` to validate and normalize client datasets.
- Use `scripts/eval_runner.py` to validate datasets, grade transcripts, smoke-test adapters, or run deterministic hard gates.
- Use `scripts/deepeval_export.py` to generate the DeepEval pytest file.
- Use the selected runner adapter to execute a real agent when credentials and invocation path are available.

Runner contract:

The invocation command receives one case JSON on stdin and should emit one result JSON on stdout with `observed_output`, `tool_calls`, `blocked`, `approval_requested`, `citations`, and `notes`.

DeepEval execution:

Codex may run `deepeval test run` in the target environment if DeepEval is installed, the target invocation path exists, and required API keys are configured locally. Otherwise, generate the suite and clearly mark live eval execution as pending. Set `AGENT_ASSURANCE_DEEPEVAL_JUDGE=0` internally when only deterministic hard gates should run.

## Adequacy Rules

- An eval suite without thresholds is weak.
- A one-off notebook is weak unless it is pinned, repeatable, and produces hashable output.
- Evals that test only harmful prompts and omit benign false positives are weak.
- Evals that test the base model but not the full agent/tool/retrieval path are not adequate for agent controls.
- Manual red-team notes can support evidence but do not replace repeatable regression gates.
- If evals are used as proof for a shipping decision, require `C016 Reproducibility Boundary`.
- If DeepEval is used, record metric names, thresholds, judge model, trace instrumentation, and whether deterministic hard gates ran before LLM-as-judge scoring.
