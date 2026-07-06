# Agent Control Audit Runbook

Use this runbook to prove the `agent-control-audit` skill with the local Google ADK AML reference agent before trying external repositories or client code.

This document is for the person running the demo or assurance workflow. The user should not have to understand JSON, JSONL, Python flags, or internal script names. Those files exist as evidence and machine inputs. The primary user-facing outputs are Markdown, Excel, and DOCX.

Related documents:

- `docs/user_guide.md`: full user journey, stage outcomes, approval gates, and report formats.
- `docs/testing/packaging_boundary.md`: what belongs inside the skill zip.
- `docs/architecture/skill_product_model.md`: why this is one orchestrator skill today.

## Known-Good Target

Start here:

- **Target agent:** `examples/google_adk_aml_openai`
- **Framework:** Google ADK 1.x-style reference agent
- **Domain profile:** `financial_aml`
- **Output folder:** `outputs/adk-aml-openai/<YYYY-MM-DD-HHMM>/`
- **Static review:** no API key required
- **Deterministic dynamic eval:** no API key required
- **HTTP wrapper eval:** no model API key required for the deterministic adapter path
- **Live ADK/OpenAI eval:** requires target dependencies and `OPENAI_API_KEY` configured locally

The known-good outcome should be:

- Static framework: `google_adk`
- Static decision: `ship`
- Dataset readiness: `eval_ready`
- Deterministic eval pass rate: `1.0`
- HTTP wrapper eval pass rate: `1.0`

## Human-Readable Artifact Rule

Every meaningful stage should produce at least one human-readable artifact.

JSON and JSONL files are still useful, but they are evidence and machine contracts. A reviewer, business stakeholder, model-risk partner, or client should first read the Markdown, Excel, or DOCX files.

| Stage | Human Artifact | Machine/Evidence Artifact |
|---|---|---|
| Intake | `00_intake/*.md` | `_run_manifest.json` |
| Observation | `01_observation/observation.md` | Static audit JSON inputs |
| Static audit | `02_static_audit/static_audit_summary.md` | `static_audit.json`, `findings.jsonl` |
| Gap matrix | `03_gap_matrix/gap_matrix.md`, `gap_matrix.xlsx` | Static audit JSON |
| Change plan | `04_change_plan/change_plan.md` | Optional patch/diff later |
| Dataset readiness | `05_dataset/readiness/dataset_readiness.md`, `.xlsx` | readiness JSON, normalized JSONL |
| Eval generation | `06_evals/deepeval/deepeval_suite.py` | generated pytest file |
| Eval results | `06_evals/results/eval_summary.md` | result JSONL, summary JSON |
| Reports | `07_reports/assurance_report.md`, `.xlsx`, `.docx` | report source artifacts |
| Remediation | `08_remediation/proposed_changes.md` | patch/diff if approved |
| Evidence | `evidence/evidence_summary.md` | hashes JSONL, manifest JSON |

## Stage 0: Intake

Purpose: establish what is being assessed, what domain profile applies, and where artifacts will go.

User prompt:

```text
Use agent-control-audit on examples/google_adk_aml_openai.
Use financial_aml as the profile.
Put the run artifacts under outputs/adk-aml-openai/2026-07-05-1432.
Start with the known-good local ADK proof path.
```

Expected human outputs:

- `00_intake/scope.md`
- `00_intake/domain_context.md`
- `00_intake/business_expectations.md`
- `00_intake/data_contracts_and_mdm.md`
- `00_intake/governance_expectations.md`

What to look for:

- Does the target path look right?
- Is the domain/profile right?
- Are business, MDM/data, and governance assumptions marked clearly instead of invented?

## Stage 1: Observation

Purpose: explain what the agent appears to be before judging it.

Expected human output:

- `01_observation/observation.md`

What it should contain:

- Detected framework.
- Business context.
- Autonomy level.
- Whether tools, retrieval, memory, handoffs, and evals appear to exist.
- Why those capabilities create risk.
- A human confirmation request.

This stage matters because if the observation is wrong, the gap matrix will be wrong.

## Stage 2: Static Audit

Purpose: inspect source-visible controls and derive the required controls independently of what the repo claims.

Expected human output:

- `02_static_audit/static_audit_summary.md`

Expected evidence artifacts:

- `02_static_audit/static_audit.json`
- `02_static_audit/findings.jsonl`

What to look for:

- Framework detected as `google_adk`.
- Decision shown clearly.
- Controls detected.
- Findings, if any.
- Blind spots stated plainly.

For the known-good ADK reference, the static decision should be `ship`.

## Stage 3: Gap Matrix

Purpose: turn required controls into a reviewable control table.

Expected human outputs:

- `03_gap_matrix/gap_matrix.md`
- `03_gap_matrix/gap_matrix.xlsx`

What to look for:

- Each required financial control maps to a status.
- Evidence locations are readable.
- Notes explain what still needs runtime or governance confirmation.

Use the Excel file when the audience wants filtering, ownership, or triage. Use Markdown when the audience wants a quick engineering/governance read.

## Stage 4: Change Plan

Purpose: propose changes before touching the target code.

Expected human output:

- `04_change_plan/change_plan.md`

What to look for:

- If gaps exist, the plan should say what to change and how to prove the fix.
- If no static gaps exist, the plan should say no source-code remediation is proposed and list remaining dynamic or deployment checks.

The skill should not silently edit the target repository before this stage exists.

## Stage 5: Dataset Readiness

Purpose: decide whether the supplied dataset is actually ready for eval generation.

For the local demo, the starter AML dataset is used. In a client run, ask the user for their dataset first. If they do not have one, propose a seed dataset and wait for approval.

Expected human outputs:

- `05_dataset/readiness/dataset_readiness.md`
- `05_dataset/readiness/dataset_readiness.xlsx`

Expected machine artifact:

- `05_dataset/normalized/normalized_dataset.jsonl`

What to look for:

- Status such as `eval_ready` or `needs_client_input`.
- Case counts.
- Machine-checkability.
- Missing governance metadata.
- Improvement actions.
- Client questions.

Important: do not ask the user to interpret JSONL. Explain that normalized JSONL is the canonical machine file used by eval generation.

## Stage 6: DeepEval Suite And Deterministic Eval

Purpose: generate client-facing DeepEval tests and run hard deterministic gates.

Expected human output:

- `06_evals/results/eval_summary.md`

Expected machine/test artifacts:

- `06_evals/deepeval/deepeval_suite.py`
- `06_evals/results/eval_results.jsonl`
- `06_evals/results/eval_summary.json`

What to look for:

- Total cases.
- Passed and failed counts.
- Pass rate.
- Failed IDs, if any.
- Dataset hash.

For the known-good ADK reference, deterministic eval should pass 5/5.

## Stage 7: HTTP Wrapper Proof

Purpose: prove the same cases can run through an invocation boundary similar to a real deployed agent.

Expected human output:

- `06_evals/results/http_eval_summary.md`

Expected evidence artifacts:

- `06_evals/results/http_eval_results.jsonl`
- `06_evals/results/http_eval_summary.json`

What to look for:

- `/health` returns OK.
- `/invoke` receives each normalized case.
- HTTP eval pass rate is `1.0` for the known-good local example.

If localhost binding is blocked by the environment, mark HTTP proof as pending instead of treating it as an agent failure.

## Stage 8: Reports And Evidence

Purpose: package the run for a reviewer.

Expected human outputs:

- `07_reports/assurance_report.md`
- `07_reports/assurance_report.xlsx`
- `07_reports/assurance_report.docx`
- `evidence/evidence_summary.md`

Expected evidence artifacts:

- `evidence/evidence_manifest.json`
- `evidence/hashes.jsonl`

What to look for first:

1. `01_observation/observation.md`
2. `03_gap_matrix/gap_matrix.md`
3. `05_dataset/readiness/dataset_readiness.md`
4. `06_evals/results/eval_summary.md`
5. `07_reports/assurance_report.md`
6. `evidence/evidence_summary.md`

That order tells the story without forcing the reader into JSON.

## Current Known-Good Output

The latest local proof run is under:

```text
outputs/adk-aml-openai/2026-07-05-1432/
```

It contains the full stage set:

- Intake Markdown files.
- Observation Markdown.
- Static audit summary.
- Gap matrix Markdown and Excel.
- Change plan Markdown.
- Dataset readiness Markdown and Excel.
- DeepEval suite.
- Deterministic eval summary Markdown.
- HTTP eval summary Markdown.
- Markdown, Excel, and DOCX final reports.
- Evidence summary and hash manifest.

## Optional External Repository Validation

Only use external repositories after the local ADK reference journey is clear.

The purpose of external repos is not to replace the local proof. It is to show that the skill can inspect unfamiliar agent code and still produce the same stage artifacts.

Recommended prompt:

```text
Use agent-control-audit on this external repo: <path>.
Use the same stage artifact contract as the ADK runbook.
Start with static audit only and do not request API keys yet.
```

Useful external targets are tracked in:

- `docs/research/github_targets.md`
