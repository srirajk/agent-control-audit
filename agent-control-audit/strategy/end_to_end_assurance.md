# End-to-End Agent Assurance Strategy

This skill helps Codex assess whether an already-built agent system has adequate guardrails, evals, and operational controls. It is not an AML-only skill. Financial and AML are the first domain profile because they exercise high-impact risks: customer data, regulated output, money movement, retrieval grounding, multi-agent delegation, analyst approval, and audit evidence.

## Product Shape

The assurance loop is:

1. Intake the target repository and entrypoint.
2. Create a structured run output folder with `scripts/init_output.py`.
3. Detect the framework and agent architecture.
4. Inventory tools, retrieval, handoffs, memory, approvals, callbacks, middleware, policies, evals, and telemetry.
5. Derive the required control set from domain, harm surface, autonomy, architecture, and NFR exposure.
6. Run the static audit and produce hashable evidence for source-visible controls.
7. Review supplied golden datasets for schema validity, machine-checkability, risk coverage, ownership, versioning, and readiness. If no dataset exists, draft a proposed synthetic seed dataset from the observed risks and ask for explicit approval before using it as eval input.
8. Invoke the target agent through the access path the user/team exposes: HTTP endpoint, MCP tool/server, SDK/framework object, or a project-owned command wrapper.
9. Generate a DeepEval suite by default and embed deterministic hard assertions in it.
10. Run the DeepEval suite against the live agent path.
11. Attach model-governance evidence: inventory, intended use, limitations, validation, data lineage, monitoring, benchmarking, fairness, explainability, change approval, vendor risk, access, retention, rollback, and governance reporting.
12. Produce a verdict, fix order, residual-risk statement, and evidence bundle.

## What "Finished" Means

A finished assurance run has:

- A detected framework or an explicit no-agent/ambiguous-framework stop reason.
- A profile of the agent's harm surfaces and architecture.
- A required-control map independent of the controls the agent already has.
- Findings for missing, weak, or misconfigured controls with file/line evidence.
- A golden dataset quality report plus a supplied or explicitly approved dataset set that covers adversarial, benign, grounding, leakage, tool-use, toxicity, and NFR behavior.
- Model-governance evidence for inventory, owners, intended use, limitations, independent validation, data lineage, monitoring, benchmarking/backtesting, fairness/bias, explainability, change approval, vendor risk, access segregation, retention/legal hold, continuity, and reporting.
- A live runner command that executes the real agent path through HTTP, MCP, SDK/framework, or a project-owned wrapper and emits the required result JSON.
- A DeepEval suite with hard assertions, pass/fail, hashes, thresholds, and failed case IDs.
- Optional secondary renderers only when the user/team requires another standard.

## AML Example Scenario

Use AML as a proof scenario without hard-coding the skill to AML. A realistic AML assistant might include:

- `entity_resolution_agent`: resolves customer, counterparty, and beneficial-owner entities.
- `transaction_monitoring_agent`: reviews suspicious transfer patterns and account activity.
- `sanctions_agent`: checks sanctions/watchlist/adverse-media sources.
- `case_narrative_agent`: drafts analyst-facing case summaries.
- `orchestrator_agent`: routes work between specialists and decides when to ask a human analyst.

Expected high-risk controls:

- Tool authorization for account, customer, sanctions, transaction, and case-management tools.
- Human approval before filing, closing, escalating, or externally submitting a case.
- Retrieval scope controls for approved KYC, transaction, sanctions, and policy sources.
- Grounding validation for every material allegation in the case narrative.
- Data minimization and redaction across prompts, tool results, logs, and handoffs.
- Handoff authority, handoff payload filters, and provenance for each specialist transition.
- Prompt-injection controls for uploaded documents, adverse-media pages, tool output, and handoff payloads.
- Toxicity/abuse safety for customer-facing or analyst notes.
- Rate/cost/time limits and safe fallback when a data provider fails.
- Repeatable evals for false positives, leakage, unauthorized tool use, grounding, jailbreaks, and benign analyst workflows.
- Model inventory and ownership for the AML agent system and each specialist agent.
- Intended use and prohibited use, especially around SAR filing, case closure, customer contact, and escalation decisions.
- Independent validation/effective challenge before production use and after material changes.
- Data lineage and quality controls for KYC, transaction, sanctions, adverse-media, and case-management sources.
- Drift and outcome monitoring for alert mix, false positives, analyst overrides, missed typologies, and guardrail trip rates.
- Benchmarking/backtesting against historical cases, analyst decisions, and rule-based controls.
- Fairness/bias review for customer/entity treatment, escalation priority, and investigation outcomes.
- Explainability and reason codes for narratives, escalations, closures, and reviewer decisions.
- Change management, vendor risk, access segregation, evidence retention, legal hold, rollback, decommissioning, and governance reporting.

## Dataset Flow

Start with the bundled synthetic seed datasets in `evals/datasets/*.jsonl`. For a real customer system, extend them with:

- Production red-team prompts with secrets removed.
- Historical incident prompts and near misses.
- Synthetic AML or finance cases reviewed by domain owners.
- Benign analyst tasks that should not be blocked.
- Tool and retrieval fixtures with safe, fake customer identifiers.
- Expected outcomes approved by compliance, risk, product, or engineering owners.

Golden cases should be small, pinned, reviewed, versioned, and easy to run repeatedly. A case is useful only when it names the expected behavior and the forbidden behavior precisely enough for a runner to grade it.

Use `evals/client_dataset_intake.md` when a user or team supplies data. Use `scripts/dataset_import.py` to normalize JSONL, JSON, CSV, or XLSX into the skill schema. Do not accept real secrets, raw account numbers, private keys, or customer identifiers; require synthetic or redacted fixtures.

If no golden dataset exists, propose a small synthetic seed dataset based on the agent's harm surfaces, domain profile, tools, missing controls, and intended use. Label it as proposed, explain the purpose and expected behavior for each case, and ask for explicit approval before generating DeepEval tests or running dynamic evals. If the user rejects or wants changes, stop at dataset recommendations and revise only after approval.

The dataset importer is deterministic machinery, not the core intelligence of the skill. It parses files, validates fields, detects duplicates, checks machine-checkable assertions, scores readiness, and writes structured questions for the user/team. Codex should use that report to critique dataset quality and decide whether the data is ready for DeepEval generation.

For governance artifacts, accept Markdown, JSON, CSV, Excel, or user/team policy excerpts, but normalize the evidence into the report sections instead of asking the LLM to remember it. If the user/team cannot supply a required item, flag it as missing and ask the control owner for the specific missing field, such as model owner, validation date, retention period, or monitoring threshold.

## Runner Contract

The deterministic runner calls a target command once per case. That command can wrap HTTP, MCP, SDK/framework code, or any target-specific invocation path:

```bash
python3 -B scripts/eval_runner.py \
  --dataset evals/datasets/jailbreak_direct.jsonl \
  --command "python runner_adapters/http_agent_adapter.py" \
  --out /tmp/grades.jsonl \
  --summary /tmp/summary.json
```

The command receives one case JSON on stdin and emits one result JSON on stdout:

```json
{
  "id": "case-id",
  "suite": "suite-name",
  "observed_output": "agent output",
  "tool_calls": ["tool_name"],
  "blocked": false,
  "approval_requested": false,
  "citations": ["source-id"],
  "notes": "optional trace or reason"
}
```

Hard gates stay deterministic. The runner checks tool calls, approval requests, blocked flags, forbidden phrases, required phrases, citation presence, leakage patterns, and max tool-call budgets. Do not replace those checks with an LLM judge.

Invocation adapter priority:

1. Use a project-owned SDK command when the agent needs private app setup, auth sessions, seeded databases, or framework-specific wiring.
2. Use HTTP when the agent already exposes a stable invoke endpoint.
3. Use MCP stdio when the agent is exposed as an MCP server/tool.
4. Use transcript-only results only for calibration; do not claim runtime assurance from transcripts.

## DeepEval Policy

DeepEval is the default generated eval framework for user-facing tests. Use it whenever creating tests, golden suites, or validation artifacts unless the user/team explicitly requires another framework.

Use DeepEval for:

- Pytest-style eval execution with `deepeval test run`.
- Goldens/datasets and `LLMTestCase` objects.
- LLM-as-judge metrics for subjective quality, clarity, task completion, or narrative quality.
- Framework tracing for LangChain, LangGraph, OpenAI Agents SDK, Google ADK, RAG, MCP, and tool spans.
- Synthetic dataset generation or simulation workflows.

Keep the deterministic runner as the source of truth for hard controls:

- Unauthorized tool execution.
- Missing human approval.
- Sensitive data leakage.
- Missing required citations or insufficient-evidence behavior.
- Max tool-call, retry, rate, cost, timeout, and fallback behavior.
- Exact forbidden/required behavior in regulated flows.

The practical pattern is: DeepEval suite for execution and presentation; deterministic hard assertions inside that suite for financial/AML safety gates.

When another eval framework is needed, use `evals/eval_framework_adapter_pattern.md`. Add the new renderer behind the canonical case/result schema rather than changing the dataset format.

## Framework Strategy

OpenAI Agents SDK:

- Static audit can detect guardrails, tool guardrails, function tools, approval gates, handoffs, retrieval, tracing, and eval signals.
- Live evals should wrap `Runner.run` or `Runner.run_sync` and capture final output, tool calls, tripwires, approval interruptions, and citations.
- DeepEval can instrument OpenAI Agents spans when the team wants component scoring.

LangChain:

- Static audit looks for middleware, tools, structured output, callbacks, retrievers, PII/content-safety middleware, and human-in-the-loop patterns.
- Live evals should call `agent.invoke` or `agent.ainvoke` with the case input and capture output plus intermediate/tool events.
- DeepEval can attach a LangChain callback handler for trace spans.

LangGraph:

- Static audit looks for graph nodes, state schemas, interrupts, checkpointers, stores, tool nodes, subgraphs, routing, and transition controls.
- Live evals should invoke the compiled graph and treat interrupts as approval requests when they pause before a risky action.
- DeepEval can trace graph spans through the LangChain integration path.

Google ADK 1.x:

- Static audit looks for `LlmAgent`, tools, MCP toolsets, callbacks/plugins, before/after model/tool hooks, auth, safety, sessions, evals, and tracing.
- Live evals should wrap the ADK runner, stream events until a final response, and capture tool events and approval/safety blocks.
- DeepEval can instrument Google ADK through its ADK integration.

Google ADK 2.0 / graph workflows:

- Static audit additionally looks for workflows, graph routes, collaborative agents, human-input nodes, state movement, and dynamic routing.
- Live evals should capture node transitions, human-input pauses, tool events, retrieved context, and final responses.
- The reviewer must verify that graph transitions cannot bypass guardrails, approvals, retrieval scope, or redaction.

## Acceptance Tests

Use the local smoke demo before trying a customer repo:

1. Unsafe OpenAI fixture blocks in static audit.
2. Guarded OpenAI fixture ships in static audit.
3. Starter datasets validate.
4. Mock agent command passes the bundled golden datasets.
5. DeepEval pytest file exports without requiring DeepEval to be installed.
6. A real framework adapter runs at least one dataset against a real agent command.
