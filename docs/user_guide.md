# Agent Control Audit User Guide

This guide explains the user experience for running `agent-control-audit` against an agent repository. It is written for any team building, reviewing, buying, governing, or operating agents. That may be a client, an internal platform team, a model-risk team, a product team, or an independent builder who needs understandable artifacts, not just JSON.

The example target used throughout is the repo-level Google ADK 1.x reference agent:

- Target repo: `examples/google_adk_aml_openai`
- Framework: Google ADK 1.x style agent
- Domain shape: AML investigation assistant
- Model path: OpenAI-backed ADK example when live credentials are available

## Core Principles

- Static review does not require API keys, dependency installation, or an HTTP/OpenAPI endpoint.
- Dynamic evaluation requires a stable invocation path: HTTP endpoint, MCP tool, SDK runner, CLI wrapper, or framework adapter.
- Do not edit the original target repository during assessment.
- Before any remediation change, create a human-readable observation artifact and a proposed change plan.
- If no golden dataset is provided, ask for one. If the user does not have one, draft a proposed synthetic seed dataset and wait for approval before treating it as eval input.
- JSON and JSONL are evidence artifacts, not the primary user experience. Use Markdown, Excel, or DOCX for human review.
- Generate all artifacts into a clear output folder so the run is easy to review, repeat, and hand off.
- If the target needs secrets, configure them locally through environment variables or an ignored `.env` file. Never put secrets in prompts, datasets, generated evals, reports, or chat.

## Recommended Output Folder

Create one run folder per target and timestamp. If the user does not provide an output folder, Codex should choose one and tell the user before writing artifacts:

```text
outputs/<target-name>/<YYYY-MM-DD-HHMM>/
```

Recommended structure:

```text
outputs/adk-aml-openai/2026-07-05-1432/
├── ARTIFACT_INDEX.md
├── _run_manifest.json
├── 00_intake/
│   ├── scope.md
│   ├── domain_context.md
│   ├── business_expectations.md
│   ├── data_contracts_and_mdm.md
│   ├── domain_extension_reference.md
│   ├── governance_expectations.md
│   ├── quality_profile_notes.md
│   └── source_snapshot_manifest.md
├── 01_observation/
│   └── observation.md
├── 02_static_audit/
│   ├── static_audit.json
│   └── findings.jsonl
├── 03_gap_matrix/
│   ├── gap_matrix.md
│   └── gap_matrix.xlsx
├── 04_change_plan/
│   └── change_plan.md
├── 05_dataset/
│   ├── supplied/
│   ├── proposed/
│   │   ├── proposed_golden_dataset.md
│   │   └── proposed_golden_dataset.jsonl
│   ├── readiness/
│   │   ├── dataset_readiness.md
│   │   └── dataset_readiness.xlsx
│   └── normalized/
│       └── normalized_dataset.jsonl
├── 06_evals/
│   ├── deepeval/
│   │   └── deepeval_suite.py
│   └── results/
│       ├── eval_results.jsonl
│       └── eval_summary.json
├── 07_reports/
│   ├── assurance_report.md
│   ├── assurance_report.xlsx
│   └── assurance_report.docx
├── 08_remediation/
│   ├── proposed_changes.md
│   ├── patch.diff
│   └── patched_copy/
└── evidence/
    ├── evidence_manifest.json
    └── hashes.jsonl
```

Codex should create this structure with `agent-control-audit/scripts/init_output.py` before generating run artifacts. `ARTIFACT_INDEX.md` explains the purpose of each folder so the output is navigable even when many files are produced.

For large repositories, `00_intake/source_snapshot_manifest.md` may contain a sanitized copy reference, a Git commit hash, or a manifest of files reviewed. For small demo repositories, copy the target code into `08_remediation/patched_copy/` only after changes are approved.

The proposed golden dataset files in `05_dataset/proposed/` are only created when the user does not already have a dataset. They are drafts until the user approves them.

## Stage Map

| Stage | Purpose | User Provides | Skill Produces | Human Decision |
|---|---|---|---|---|
| 0. Intake and run setup | Establish scope, domain context, and output location | Target repo path, domain, business expectations, data/MDM expectations, preferred report format | `00_intake/`, `_run_manifest.json`, `ARTIFACT_INDEX.md` | Confirm scope and domain assumptions |
| 1. Agent observation | Explain what the agent appears to do | Target repo only | `01_observation/observation.md` | Confirm the skill understood the agent correctly |
| 2. Static control audit | Identify framework, controls, gaps, and blind spots from source | Target repo only | `02_static_audit/static_audit.json`, `02_static_audit/findings.jsonl`, human summary | Agree the findings are directionally right |
| 3. Gap matrix | Turn findings into a reviewable control table | Static audit artifacts | `03_gap_matrix/gap_matrix.md`, optional `03_gap_matrix/gap_matrix.xlsx` | Prioritize what matters |
| 4. Change plan | Propose remediation without touching original code | Confirmed findings | `04_change_plan/change_plan.md` | Approve, reject, or defer changes |
| 5. Golden dataset readiness | Check whether existing cases are usable, or propose seed cases when none exist | JSONL, JSON, CSV, XLSX, or permission to draft seed cases | `05_dataset/readiness/`, `05_dataset/normalized/`, or `05_dataset/proposed/` | Approve dataset, fill gaps, or stop |
| 6. DeepEval suite generation | Generate user-facing eval tests | Approved normalized dataset | `06_evals/deepeval/deepeval_suite.py` | Confirm eval coverage and thresholds |
| 7. Dynamic invocation readiness | Decide how to call the live agent | HTTP/MCP/SDK/CLI path and local secrets | Invocation plan | Confirm runtime access is safe |
| 8. Dynamic eval run | Execute golden cases against the agent | Working invocation path | `06_evals/results/eval_summary.md`, `eval_summary.json`, optional result JSONL | Decide pass/fail and residual risk |
| 9. Final report | Package the evidence for governance | Audit, dataset, eval artifacts | `07_reports/assurance_report.md`, `.xlsx`, `.docx` | Accept, remediate, or hold release |

## Quick Demo: Phase-By-Phase HTTP Run

Use this path when you want to verify the skill one phase at a time against the local Google ADK 1.x AML demo.

Prerequisites:

- The demo agent is running at `http://127.0.0.1:9124`.
- `http://127.0.0.1:9124/health` returns `{"status":"ok"}`.
- `http://127.0.0.1:9124/invoke` accepts the assurance invocation contract.
- The target repo is `examples/google_adk_aml_openai`.
- The starter AML golden dataset is `agent-control-audit/evals/datasets/aml_investigation_controls.jsonl`.

To start the demo server from the repo root:

```bash
AGENT_ASSURANCE_LIVE_ADK=1 \
AGENT_ASSURANCE_DOTENV=examples/google_adk_aml_openai/.env \
.venv/bin/uvicorn server:app --app-dir examples/google_adk_aml_openai --host 127.0.0.1 --port 9124
```

Do not paste API keys into prompts. The running demo server owns its local `.env`; the audit should receive only the HTTP URL.

Recommended output folder:

```text
outputs/google_adk_aml_openai_http/<YYYY-MM-DD-HHMM>/
```

### Phase 1: Intake And Health

Prompt:

```text
Use agent-control-audit for phase 1 only.
Target repo: examples/google_adk_aml_openai.
Quality profile: financial_aml.
Output folder: outputs/google_adk_aml_openai_http/<YYYY-MM-DD-HHMM>.
Live agent URL: http://127.0.0.1:9124.
Verify /health only, create intake artifacts, and stop before static audit.
Do not edit the source code.
```

Expected artifacts:

- `ARTIFACT_INDEX.md`
- `_run_manifest.json`
- `00_intake/scope.md`
- `00_intake/domain_context.md`
- `00_intake/governance_expectations.md`
- `00_intake/invocation_readiness.md`

Success signal:

- The run confirms the endpoint is reachable, or clearly marks dynamic proof as pending if local HTTP access is blocked.

### Phase 2: Observation And Static Audit

Prompt:

```text
Continue the same agent-control-audit run for phase 2 only.
Create the observation, static audit, baseline-vs-domain comparison, gap matrix, and change plan.
Use financial_aml.
Do not run dynamic evals yet.
Do not edit the source code.
Stop after the change plan.
```

Expected artifacts:

- `01_observation/observation.md`
- `02_static_audit/static_audit.json`
- `02_static_audit/findings.jsonl`
- `02_static_audit/static_audit.md`
- `03_gap_matrix/gap_matrix.md`
- `03_gap_matrix/gap_matrix.xlsx`
- `04_change_plan/change_plan.md`

Success signal:

- The user can read what the agent appears to do, what controls exist, what is missing, and what the skill would change before any code is touched.

### Phase 3: Golden Dataset And DeepEval Export

Prompt:

```text
Continue the same agent-control-audit run for phase 3 only.
Use agent-control-audit/evals/datasets/aml_investigation_controls.jsonl as the approved starter golden dataset.
Validate and normalize the dataset.
Generate the DeepEval suite.
Do not call the live endpoint yet.
Stop after DeepEval generation.
```

Expected artifacts:

- `05_dataset/readiness/dataset_readiness.md`
- `05_dataset/normalized/normalized_dataset.jsonl`
- `05_dataset/normalized/normalized_dataset.md`
- `06_evals/deepeval/deepeval_suite.py`
- `06_evals/deepeval/deepeval_suite.md`

Success signal:

- The dataset is marked usable for this run, or the missing fields are explained in human language.

### Phase 4: Dynamic HTTP Eval

Prompt:

```text
Continue the same agent-control-audit run for phase 4 only.
Run the normalized AML golden dataset against http://127.0.0.1:9124/invoke.
Use DeepEval-first evaluation with deterministic hard gates.
Capture prompt-injection, data-leakage, approval-gate, evidence, and final-decision behavior.
Generate machine-readable results and a human-readable Markdown summary.
Stop before final packaging.
```

Expected artifacts:

- `06_evals/results/eval_summary.json`
- `06_evals/results/eval_summary.md`
- `06_evals/results/eval_results.jsonl`
- `06_evals/results/runtime_transcripts.jsonl`, if transcripts are available

Success signal:

- The output shows pass/fail by golden case and explains failures as release blockers, accepted risks, or test-data issues.

### Phase 5: Final Report And Evidence

Prompt:

```text
Continue the same agent-control-audit run for phase 5 only.
Create the final assurance report and evidence manifest.
Generate Markdown first, and Excel or DOCX if available.
Do not modify the target agent source.
```

Expected artifacts:

- `07_reports/assurance_report.md`
- `07_reports/assurance_report.xlsx`, if requested and supported
- `07_reports/assurance_report.docx`, if requested and supported
- `09_evidence/evidence_manifest.json`
- `09_evidence/hashes.jsonl`

Success signal:

- A governance reviewer can understand the agent, the dataset, the evals, the dynamic proof, remaining gaps, and residual risk without reading raw JSON.

## Stage 0: Intake And Run Setup

Goal: agree what is being assessed and where artifacts will go.

Example prompt:

```text
Use agent-control-audit on examples/google_adk_aml_openai.
Use financial_aml as the quality profile.
Put artifacts under outputs/adk-aml-openai/2026-07-05-1432.
Start with static review only.
```

Inputs:

- Target repo path or GitHub URL.
- Domain profile, such as `financial_aml`, if known.
- Domain/business context, if available.
- Business, MDM/data, and model-governance expectations, if available.
- Output folder. If omitted, Codex should create one under `outputs/<target-name>/<YYYY-MM-DD-HHMM>/`.
- Preferred human report formats: Markdown, Excel, DOCX, or all.

Artifact outcome:

- Structured run folder.
- `ARTIFACT_INDEX.md`.
- `_run_manifest.json`.
- `00_intake/scope.md`.
- `00_intake/domain_context.md`.
- `00_intake/business_expectations.md`.
- `00_intake/data_contracts_and_mdm.md`.
- `00_intake/domain_extension_reference.md`.
- `00_intake/governance_expectations.md`.
- `00_intake/quality_profile_notes.md`.
- `00_intake/source_snapshot_manifest.md`.

Important rule:

- Do not ask for API keys at this stage. Static review does not need them.

## Domain Knowledge And Governance Inputs

Goal: capture the domain assumptions before judging controls or generating golden data.

The skill can run with limited context, but the best result comes when the user/team provides business, data, and governance expectations. If these are not available, Codex should create assumptions in `00_intake/domain_context.md`, mark them as unconfirmed, and ask the user/team to approve or correct them.

## Domain Extension Path

Use the top-level `domain_extensions/` folder when domain knowledge should be reusable across runs.

```text
domain_extensions/
├── _template/
│   ├── domain_profile.md
│   ├── quality_profile.json
│   ├── golden_case_requirements.md
│   ├── business_expectations.md
│   ├── data_mdm_expectations.md
│   └── governance_expectations.md
└── financial_aml/
    ├── domain_profile.md
    ├── quality_profile.json
    ├── golden_case_requirements.md
    ├── business_expectations.md
    ├── data_mdm_expectations.md
    └── governance_expectations.md
```

When a user/team has a domain extension, they can say:

```text
Use the domain extension at domain_extensions/financial_aml.
```

Codex should then:

- Read the extension pack before finalizing observations, gap analysis, golden dataset proposals, or reports.
- Reference the selected pack in `00_intake/domain_extension_reference.md`.
- Use `quality_profile.json` to shape dataset readiness and golden-case expectations.
- Mark missing domain inputs as questions or assumptions.
- Keep proposed golden datasets and remediation changes behind approval gates.

Use `_template/` to create a new domain or sub-business-line pack. Keep extension packs outside the installable skill zip unless a future reusable domain pack becomes intentionally bundled.

### Domain Or Business Team Inputs

Ask for:

- Business line or subdomain, such as AML, payments, lending, wealth, trading, treasury, insurance, healthcare, legal, enterprise IT, or cybersecurity.
- Primary user persona, such as analyst, investigator, customer support agent, relationship manager, underwriter, trader, or operations user.
- Intended use and prohibited use.
- Decisions the agent can recommend versus decisions it can execute.
- Human approval gates, such as SAR filing, case closure, payment/refund execution, adverse action, client exit, customer contact, trade/order action, or privileged IT operation.
- Business policies, SOPs, playbooks, investigation procedures, escalation rules, and exception handling rules.
- Required explanations, reason codes, citations, and evidence standards.
- Regulatory or internal policy constraints the report should name.

Artifact outcome:

- `00_intake/domain_context.md`
- `00_intake/business_expectations.md`

### Data, MDM, And Source-System Inputs

Ask for:

- Source-of-truth systems and approved data sources.
- Entity definitions and join logic, such as customer, account, counterparty, beneficial owner, merchant, alert, case, transaction, SAR, RFI, policy, document, or ticket.
- MDM rules: entity resolution, deduplication, hierarchy, relationship handling, householding, ownership, and survivorship rules.
- Data classification: public, internal, confidential, PII, PHI, PCI, MNPI, secrets, or regulated records.
- Data minimization and redaction expectations.
- Data quality rules: freshness, completeness, lineage, reconciliation, schema checks, and missing-data escalation.
- Retrieval boundaries: approved corpora, tenant filters, jurisdiction filters, business-line filters, and freshness windows.
- Synthetic or redacted fixtures that can safely be used in golden datasets.

Artifact outcome:

- `00_intake/data_contracts_and_mdm.md`

Why this matters:

- Without MDM/source-system expectations, the skill can find generic retrieval and data leakage gaps, but it cannot fully judge whether the agent is using the correct customer, account, transaction, counterparty, or policy evidence.

### Model Governance Or MRM Inputs

Ask for:

- Model/agent inventory ID, owner, risk tier, and intended-use statement.
- Builder, validator, approver, and control owner.
- Validation requirements and independent-review expectations.
- Benchmark, backtest, or challenger-model expectations.
- Monitoring expectations: drift, outcomes, guardrail trip rate, false positives, missed typologies, latency, cost, and incident thresholds.
- Change-management rules for prompts, tools, policies, retrieval sources, models, thresholds, and eval datasets.
- Access control, segregation of duties, retention, legal hold, rollback, continuity, vendor risk, and decommissioning expectations.
- Governance reporting cadence and required audience.

Artifact outcome:

- `00_intake/governance_expectations.md`

### Quality Profile Configuration

The skill has built-in quality profiles such as:

- `default`
- `financial`
- `financial_aml`
- `financial_payments`
- `financial_lending`

A domain team can also provide a custom quality profile when the default suite coverage is not enough.

A quality profile defines:

- Required or recommended eval suites.
- Metadata required for traceability, such as owner, reviewer, approver, version, and reviewed date.
- Readiness thresholds for `eval_ready` and `governance_grade_candidate`.
- Scoring weights for schema quality, machine-checkability, high-risk assertions, suite coverage, benign/adversarial balance, and traceability.

Artifact outcome:

- `00_intake/quality_profile_notes.md`

The user/team does not need to know the internal script flags. In plain language, they can say:

```text
Use financial_aml as the domain profile.
Our AML team requires SAR approval, case-closure approval, tipping-off prevention, sanctions grounding, adverse-media prompt-injection checks, and benign false-positive cases.
```

For a custom domain:

```text
Use a custom insurance claims profile.
Required suites are claims_coverage_boundary, claim_denial_reason_codes, fraud_escalation, PII_redaction, prompt_injection_indirect, and benign_false_positives.
Require owner, reviewer, approved_by, dataset_version, and reviewed_at metadata.
```

### Golden Case Expectations From Domain Owners

For golden cases, ask business/domain owners to provide or approve:

- Realistic scenarios or typologies.
- Expected behavior: `block`, `allow`, `request_approval`, `answer_with_citations`, `safe_fallback`, or a domain-specific label.
- Forbidden outcomes: forbidden tools, skipped approvals, fabricated claims, data leakage, wrong entity resolution, stale evidence, policy bypass, or overblocking.
- Severity and release impact.
- Required citations, evidence IDs, reason codes, or structured fields.
- Synthetic or redacted user context, documents, tool outputs, and source-system records.
- Owner/reviewer/version metadata.

Do not treat LLM-generated seed cases as golden until the domain owner or user/team approves them.

## Stage 1: Agent Observation

Goal: produce a plain-English understanding of the agent before judging it.

For the ADK 1.x AML example, `01_observation/observation.md` should contain:

- Agent framework detected or suspected.
- Main entrypoint, such as `agent.py` or `root_agent`.
- Major tools and actions.
- Whether the agent uses retrieval, memory, handoffs, callbacks, or external services.
- Apparent domain and harm surfaces, such as AML case handling, SAR/RFI preparation, customer data, or analyst workflow.
- What the agent seems allowed to do.
- What the agent must not be allowed to do without approval.
- Static-only limitations.

Artifact outcome:

- Primary: `01_observation/observation.md`
- Optional: `01_observation/observation.docx` for executive review

Human decision:

- The user/team confirms, corrects, or narrows the agent understanding before findings are treated as final.

## Stage 2: Static Control Audit

Goal: inspect source-visible controls without running the agent.

Static review can run when:

- No API keys are available.
- Dependencies are not installed.
- The agent has no HTTP endpoint.
- The code can be read locally.

Static review cannot prove:

- Production IAM.
- Hosted gateway controls.
- Runtime callback order.
- Human operating procedures.
- Deployed telemetry.
- Tool behavior hidden outside the repository.

Artifact outcome:

- `02_static_audit/static_audit.json`: machine-readable audit evidence.
- `02_static_audit/findings.jsonl`: hashable finding records.
- Human summary in chat or `03_gap_matrix/gap_matrix.md`.

What the JSON contains:

- Framework detection.
- Architecture profile.
- Required control map.
- Controls detected.
- Missing, weak, or misconfigured findings.
- Blind spots.
- Evidence locations.
- Record hashes.

Important human-facing rule:

- Do not hand the user/team only JSON. JSON is useful evidence, but the review experience should be Markdown, Excel, or DOCX.

## Stage 3: Gap Matrix

Goal: convert static audit results into a human review table.

Recommended Markdown sections:

- Executive summary.
- Top risks.
- Control gap table.
- Why each finding matters.
- Evidence location.
- Recommended fix.
- Static blind spots.

Recommended Excel sheets:

- `Summary`
- `Findings`
- `Controls`
- `Eval`

Artifact outcome:

- `03_gap_matrix/gap_matrix.md` for narrative review.
- `03_gap_matrix/gap_matrix.xlsx` for triage, ownership, status, and prioritization.

Human decision:

- The user/team agrees which findings are real, which are accepted risks, and which require remediation.

## Stage 4: Change Plan Before Code Changes

Goal: propose changes before touching source.

The skill should not immediately edit the target repository. It should first produce `04_change_plan/change_plan.md`.

The change plan should contain:

- Files likely to change.
- Controls each change enables.
- Why the change is required.
- Whether the change uses native framework controls first.
- Expected behavioral change.
- New or updated eval cases required.
- Risks of the change.
- Rollback plan.

For Google ADK 1.x, the change plan should prefer native ADK concepts first:

- Callbacks for input, model, tool, and output controls.
- Tool confirmation for high-risk actions.
- Session/state for correlation IDs and evidence version.
- ADK evals when already present.
- Then add domain controls that ADK does not know about, such as AML tipping-off, SAR approval, evidence grounding, and model-governance metadata.

Artifact outcome:

- `04_change_plan/change_plan.md`

Human decision:

- Approve changes before Codex edits a copy or branch.

Source safety rule:

- If changes are approved, work in a copied repo, branch, or output snapshot. Do not mutate the original source silently.

## Stage 5: Golden Dataset Readiness

Goal: determine whether the supplied dataset is usable as golden data, or help the user create a proposed seed dataset when none exists.

Accepted inputs:

- JSONL
- JSON array
- JSON object with `cases`
- CSV
- XLSX

If no dataset is supplied, ask:

```text
Do you already have a golden dataset for this agent? If not, I can draft a proposed synthetic seed dataset from the observed risks and wait for your approval before generating DeepEval tests.
```

If the user says they do not have one, create proposed dataset artifacts:

- `05_dataset/proposed/proposed_golden_dataset.md`: human-readable explanation of proposed suites, cases, expected behavior, forbidden behavior, severity, and why each case matters.
- `05_dataset/proposed/proposed_golden_dataset.jsonl`: machine-readable draft cases in the expected schema.

Consent gate:

- Do not call the proposed file golden yet.
- Do not generate DeepEval tests from it yet.
- Do not run dynamic evals from it yet.
- Ask the user to approve, edit, or reject it.
- If the user rejects it or wants changes, stop at recommendations and revise the proposal.
- Move forward only after approval.

The dataset review checks:

- Required fields.
- Expected behavior.
- Forbidden outcomes.
- Severity.
- Machine-checkable assertions.
- Coverage across suites.
- Duplicate IDs.
- Owner/reviewer/version metadata.
- Whether high-risk cases have deterministic assertions.

Artifact outcome:

- If dataset supplied: `05_dataset/readiness/dataset_readiness.md`, a human-readable readiness report and user questions.
- If dataset supplied and usable: `05_dataset/normalized/normalized_dataset.jsonl`, canonical eval input.
- If no dataset supplied: `05_dataset/proposed/proposed_golden_dataset.md` and `05_dataset/proposed/proposed_golden_dataset.jsonl`, both pending approval.
- Optional `05_dataset/readiness/dataset_readiness.xlsx`: row-level issues and ownership tracking.

Readiness statuses:

- `needs_client_input`: missing fields or assertions; do not generate serious evals yet.
- `structurally_valid_but_coverage_thin`: can be explored, but should not be treated as strong governance evidence.
- `eval_ready`: usable for deterministic and DeepEval generation.
- `governance_grade_candidate`: strong enough to support governance review.

Human decision:

- The user approves the proposed dataset, edits it, rejects it, or supplies missing expected outcomes, forbidden outcomes, severity, owners, or assertions.

## Stage 6: DeepEval Suite Generation

Goal: generate the user-facing eval suite.

DeepEval generation does not call the target agent and does not invoke an LLM. It converts approved normalized cases into a pytest/DeepEval test file.

Artifact outcome:

- `06_evals/deepeval/deepeval_suite.py`

The generated suite should contain:

- One test path per golden case or suite.
- Deterministic gates for observable controls such as approval required, blocked action, forbidden tool call, missing citations, timeout/fallback, and max tool calls. Text leakage and phrase checks are useful fallbacks, but they are not semantic proof by themselves.
- Optional LLM-as-judge metrics only after deterministic gates.

Human decision:

- The user confirms the suites and thresholds are right before running them as release evidence.

## Stage 7: Dynamic Invocation Readiness

Goal: decide how to call the real agent safely.

Static review does not need an endpoint. Dynamic evaluation does.

Supported invocation paths:

- HTTP endpoint, including a stable `/invoke` route or an OpenAPI-described API.
- MCP stdio server/tool.
- SDK/framework adapter.
- Project-owned CLI wrapper.
- Transcript-only for calibration, not runtime proof.

For the ADK 1.x example:

- Static path: run against `examples/google_adk_aml_openai`.
- SDK adapter path: use the ADK runner adapter with a project-owned runner function.
- HTTP path: start the FastAPI wrapper and call `/invoke`.

Dynamic prerequisites:

- Dependencies installed in the target environment.
- Required local API keys configured.
- Stable one-case-in, one-result-out invocation contract.
- Sandbox or fake credentials for high-risk tools.
- No real customer data or real side-effecting credentials in demo runs.

Artifact outcome:

- Invocation plan in Markdown.
- Optional endpoint contract or wrapper code.

Human decision:

- Confirm the invocation path and secrets are safe to use.

## Stage 8: Dynamic Eval Run

Goal: run golden cases against the real agent or approved wrapper.

Result JSON should capture:

- Case ID.
- Observed output.
- Tool calls.
- Whether the agent blocked.
- Whether approval was requested.
- Citations/evidence IDs.
- Trace/session IDs when available.
- Guardrail denial reasons.

Artifact outcome:

- `06_evals/results/eval_summary.md`: human-readable run summary.
- `06_evals/results/eval_summary.json`: machine-readable eval summary.
- Optional `06_evals/results/eval_results.jsonl`: per-case results.
- Optional Excel summary when requested.

Human decision:

- Decide whether failures are release blockers, accepted risk, or test/data issues.

## Stage 9: Final Assurance Report

Goal: package the result for the audience.

Recommended formats:

- Markdown: engineering and review narrative.
- Excel: findings, ownership, status, controls, eval summary.
- DOCX: concise governance memo.

The final report should contain:

- Executive summary.
- Target and framework.
- Scope and assumptions.
- Static findings.
- Dataset readiness.
- Dynamic eval status.
- Top risks.
- Required remediations.
- Residual risk.
- Blind spots.
- Evidence hashes.

Artifact outcome:

- `07_reports/assurance_report.md`
- `07_reports/assurance_report.xlsx`
- `07_reports/assurance_report.docx`

## ADK 1.x Example Experience

Use this when demonstrating the skill with the repo-level ADK example.

Static-only prompt:

```text
Use agent-control-audit on examples/google_adk_aml_openai.
Create an observation artifact, static gap matrix, and change plan.
Do not run dynamic evals yet.
Do not edit the source code.
```

Expected artifacts:

- `01_observation/observation.md`
- `02_static_audit/static_audit.json`
- `02_static_audit/findings.jsonl`
- `03_gap_matrix/gap_matrix.md`
- `03_gap_matrix/gap_matrix.xlsx`
- `04_change_plan/change_plan.md`

If no golden dataset is available yet:

```text
I do not have a golden dataset.
Please draft a proposed seed dataset for this ADK 1.x AML example and wait for my approval.
```

Expected dataset proposal artifacts:

- `05_dataset/proposed/proposed_golden_dataset.md`
- `05_dataset/proposed/proposed_golden_dataset.jsonl`

The workflow stops here until the user approves or edits the proposed dataset.

Dynamic prompt after credentials and invocation path are ready:

```text
Use agent-control-audit to run the approved AML golden dataset against the ADK 1.x example.
Use the approved ADK runner or HTTP /invoke endpoint.
Generate the eval summary and final report as Markdown, Excel, and DOCX.
```

Expected additional artifacts:

- `05_dataset/normalized/normalized_dataset.jsonl`
- `06_evals/deepeval/deepeval_suite.py`
- `06_evals/results/eval_summary.json`
- `07_reports/assurance_report.md`
- `07_reports/assurance_report.xlsx`
- `07_reports/assurance_report.docx`

## What Good Looks Like

The best run does not jump straight to remediation. It follows this sequence:

1. Understand the agent.
2. Confirm the understanding with the user/team.
3. Identify missing controls.
4. Convert gaps into a human-readable matrix.
5. Propose changes before editing.
6. Ask for a golden dataset; if none exists, propose one and wait for approval.
7. Validate or improve the approved golden dataset.
8. Generate DeepEval tests.
9. Run dynamic evals only when invocation is safe.
10. Produce a final report with evidence and residual risk.

That is the experience this skill should provide: not just a scanner, but a guided assurance workflow that helps the user/team understand what exists, what is missing, what evidence proves it, and what must change before the agent is trusted.
