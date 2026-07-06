# Control Catalog

This catalog names the control universe. A regime decides which controls are required; the catalog only defines what each control means and what counts as adequate evidence.

## Discovery Fields

Every discovered control must be reported with:

- `control_id`: one of the catalog IDs below, or `UNMAPPED:<short-name>` when a control is real but not in the catalog.
- `type`: input guardrail, output guardrail, tool guardrail, approval gate, argument validation, retrieval control, grounding control, handoff control, logging control, NFR control, eval control, or runtime/external control.
- `location`: file path plus line or symbol when available.
- `inspects`: the input, output, tool arguments, tool result, retrieved documents, handoff payload, state, or event stream the control examines.
- `can_block`: `true`, `false`, or `unknown`, with reason.
- `adequacy_notes`: concise notes about coverage and known weaknesses.

## Control IDs

### C001 Input Intent Policy

Classifies user requests before the primary agent can act. Adequate evidence includes an input guardrail or equivalent pre-run validator that can block unsupported financial tasks, prompt injection, attempts to bypass controls, and requests outside the agent's authority. Prompt-only instructions are weak unless paired with an enforceable tripwire or halt path.

### C002 Output Recommendation Validation

Checks final financial-facing output before release. Adequate evidence includes an output guardrail, structured output validation, or deterministic reviewer that can block unsupported claims, ungrounded personalized recommendations, missing required caveats, or policy-violating advice.

### C003 Tool Authorization

Ensures the caller, user, account, and requested action are authorized before a tool performs a side effect or exposes sensitive financial data. Adequate evidence must bind authorization to the actual tool invocation, not only to a natural-language instruction.

### C004 Tool Argument Validation

Validates tool arguments against business constraints before execution. Adequate evidence includes typed schemas plus semantic checks such as ownership, account scope, currency, destination allowlists, amount limits, date windows, and idempotency keys when relevant. Type hints alone are weak for financial tools.

### C005 Human Approval Gate

Requires explicit approval before high-impact, irreversible, or externally visible financial action. Adequate evidence includes SDK approval gates, pending-interruption flows, review queues, or application code that pauses execution and records approve/reject decisions.

### C006 Transaction Limits And Kill Switch

Bounds financial side effects by amount, frequency, recipient, account, or risk score, and provides a stop path when limits are exceeded. Adequate evidence must be enforceable at or before the action boundary.

### C007 Retrieval Scope Control

Restricts retrieval to approved corpora, vector stores, documents, indexes, or tools. Adequate evidence includes allowlisted retrieval sources, tenant/account filters, document freshness constraints, or explicit rejection of untrusted sources.

### C008 Grounding Validation

Verifies that user-facing financial claims are supported by retrieved or otherwise authoritative sources. Adequate evidence includes citation checks, source-to-claim validation, stale-source handling, or contradiction handling that can block or revise unsupported answers.

### C009 Data Minimization

Limits collection, retention, propagation, and prompt inclusion of customer financial data to what the task needs. Adequate evidence includes field filters, scoped context objects, redaction before model/tool calls, and controls on handoff or retrieval payloads.

### C010 Sensitive Data Redaction

Detects and redacts secrets, account numbers, tokens, personal identifiers, or sensitive financial data from prompts, tool arguments, tool results, logs, and final output. Adequate evidence must cover the relevant channel, not just one UI layer.

### C011 Audit Logging

Records security- and compliance-relevant decisions, tool calls, approvals, denials, and final outcomes. Adequate evidence includes structured logs with correlation IDs, actor/account/action fields, and tamper-resistant or externally durable storage. `print()` statements are weak unless the surrounding runtime captures them as durable logs.

### C012 Handoff Authority Boundary

Constrains which agents may hand off to which destinations and what authority transfers. Adequate evidence includes destination allowlists, reason codes, policy checks before transfer, or per-destination scopes.

### C013 Handoff Input Filter

Controls what conversation history, tool outputs, files, and sensitive data are visible to the receiving agent. Adequate evidence includes explicit input filters, history mappers, redaction, or scoped context construction.

### C014 Handoff Provenance

Preserves why a handoff occurred, who initiated it, what data moved, and which agent accepted responsibility. Adequate evidence includes structured handoff metadata, trace spans, or durable logs tied to the audit trail.

### C015 Runtime Monitoring Boundary

Detects unsafe behavior at runtime outside the static code path. Static audits cannot verify this unless configuration or code is present in the repository. When required by a regime but invisible, report `out_of_scope`, not `present`.

### C016 Reproducibility Boundary

Pins model/runtime versions, datasets, evaluation seeds, and audit inputs where the agent's safety claims depend on repeatable model behavior. Adequate evidence includes explicit model identifiers, deterministic eval configuration, and variance reporting.

### C017 Prompt Injection And Jailbreak Resistance

Prevents user input, retrieved content, tool output, files, webpages, or handoff payloads from overriding system/developer policy, exfiltrating secrets, escalating tool authority, or bypassing safety controls. Adequate evidence includes a control bound to every untrusted instruction channel, separate treatment of instructions vs data, indirect prompt-injection handling for RAG/web/file content, blocking or quarantine behavior, and eval coverage for known and novel jailbreak families. Generic "do not obey jailbreaks" prompt text is weak unless paired with a runtime or deterministic detector.

### C018 Toxicity And Abuse Content Safety

Blocks or safely handles abusive, hateful, harassing, threatening, sexual, self-harm, violent, or brand-damaging content in user input and final output. Adequate evidence includes moderation or content-safety checks on customer-facing paths, escalation behavior for severe content, and false-positive handling for legitimate financial text such as risk, loss, fraud, or market-crash discussion.

### C019 Rate Limit And Cost Boundary

Constrains model calls, tool calls, tokens, retries, retrieval breadth, concurrent runs, external API spend, and queue growth. Adequate evidence includes enforceable per-user/per-tenant/per-run budgets, rate limits, max iterations, max tool calls, and runaway-loop termination.

### C020 Timeout Fallback And Degradation

Keeps the agent safe under model, tool, retrieval, network, provider, or database failure. Adequate evidence includes timeouts, retries with caps, circuit breakers, safe fallback responses, partial-result labeling, and prevention of duplicate financial side effects during retry.

### C021 Operational Observability And Incident Response

Makes safety-relevant runtime behavior visible and actionable. Adequate evidence includes metrics, traces, structured logs, alerts, runbooks, correlation IDs, and incident hooks for guardrail trips, tool denials, approval decisions, jailbreak attempts, data leakage attempts, and eval regressions.

### C022 Eval Harness And Regression Gate

Tests whether controls work before release and after model/prompt/tool/retrieval changes. Adequate evidence includes a pinned eval harness with representative benign cases, adversarial jailbreak/prompt-injection cases, financial advice traps, sensitive-data leakage cases, unauthorized tool-call attempts, grounding tests, toxicity cases, thresholds, CI or release gates, and variance/confidence reporting.

### C023 Model Inventory And Ownership

Records the agent, model, provider, version, business owner, technical owner, model-risk/control owner, and downstream systems in an approved inventory or registry. Adequate evidence includes a model inventory ID, ownership/RACI metadata, risk tier, deployment status, and links to approval or governance records.

### C024 Intended Use And Limitations

Defines what the agent/model is approved to do, what it must not do, assumptions, user populations, limitations, and escalation paths. Adequate evidence includes model-card-style intended use, prohibited use, limitation statements, and policy checks that prevent use outside the approved scope.

### C025 Independent Validation And Effective Challenge

Shows independent review of the model/agent design, controls, datasets, evals, assumptions, and residual risks by a qualified reviewer outside the builder path. Adequate evidence includes independent validation ownership, effective-challenge records, issue tracking, approval decisions, and retest cadence.

### C026 Data Lineage And Quality

Documents source systems, dataset construction, feature/retrieval inputs, transformations, quality checks, freshness, and known data limitations. Adequate evidence includes data lineage, schema/data dictionaries, quality thresholds, stale-data handling, and reconciliation checks for financial records.

### C027 Drift And Outcome Monitoring

Monitors population drift, prompt/task mix shifts, retrieval changes, tool behavior, outcome quality, guardrail trip rates, and business outcomes after release. Adequate evidence includes monitoring thresholds, review cadence, alerting, and owner action paths for degraded performance.

### C028 Benchmarking And Backtesting

Compares the agent/model against baselines, challenger models, historical outcomes, rule-based controls, or expected decisions. Adequate evidence includes benchmark datasets, backtesting/outcomes analysis, acceptance thresholds, and documented variance or confidence.

### C029 Fairness And Bias Testing

Tests whether the agent/model creates unfair, discriminatory, or disparate outcomes for protected or sensitive groups when used in credit, eligibility, recommendations, customer treatment, investigations, or prioritization. Adequate evidence includes fairness metrics, segment analysis, bias mitigations, and owner-approved thresholds.

### C030 Explainability And Reason Codes

Provides decision explanations, reason codes, evidence citations, or feature attribution appropriate to the financial use case. Adequate evidence includes reason-code generation, citation-backed rationale, adverse-action support when applicable, and reviewer visibility into why a recommendation or escalation occurred.

### C031 Change Management And Release Approval

Controls changes to models, prompts, tools, policies, datasets, retrieval sources, thresholds, and eval gates before release. Adequate evidence includes version control, approval workflow, release notes, rollback criteria, and model-risk or control-owner signoff for material changes.

### C032 Third-Party And Vendor Model Risk

Manages external model providers, APIs, tools, datasets, MCP servers, and hosted services that influence agent behavior. Adequate evidence includes vendor inventory, risk assessment, contract/control mapping, SLA/failure handling, data-use boundaries, and contingency plans.

### C033 Access Control And Segregation Of Duties

Restricts who can change prompts, tools, retrieval indexes, eval thresholds, releases, approvals, and production configuration. Adequate evidence includes least-privilege roles, privileged-access review, separation between builder/approver/deployer where required, and audit trails for changes.

### C034 Evidence Retention And Legal Hold

Preserves audit evidence, eval outputs, approvals, prompts, model versions, datasets, tool traces, and user-impacting decisions for the required retention period. Adequate evidence includes retention policy, tamper-resistant storage, legal-hold support, and reproducible evidence bundles.

### C035 Business Continuity Rollback And Decommissioning

Ensures the agent can fail closed, roll back, switch to a safe fallback, recover from outages, and be decommissioned without losing evidence or leaving unsafe automation active. Adequate evidence includes rollback playbooks, kill switches, recovery objectives, dependency maps, and decommission criteria.

### C036 Model Governance Reporting

Reports model/agent risk, validation status, incidents, exceptions, drift, performance, eval regressions, and open issues to the appropriate governance forum. Adequate evidence includes dashboards or periodic reports for control owners, model-risk committees, senior management, or board-level reporting where applicable.

## Adequacy Rule

Credit a control only when it is bound to the execution point it claims to protect. A detector that observes but cannot block may satisfy monitoring requirements but not blocking requirements. A schema that validates type but not business meaning may satisfy syntax validation but remains weak for financial side effects.
