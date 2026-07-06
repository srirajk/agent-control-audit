# Verdict Schema

Emit a concise verdict before the evidence file path. Use Markdown or JSON, but include every field below.

## Required Fields

- `audit_id`: stable identifier for the run.
- `target`: repository path, commit or file hash when available, and audited entrypoints.
- `framework`: detected framework or stop reason.
- `adapter_status`: `implemented`, `not_implemented`, `undetermined`, or `no_agent_found`.
- `adapter_mode`: optional, such as `framework_static_adapter` or `framework_source_first_pass`.
- `risk_tier`: `critical`, `elevated`, `moderate`, or `low`.
- `decision`: `block`, `hold`, `ship_with_conditions`, or `ship`.
- `top_fixes`: minimum ranked list of fixes, ordered by severity and causal importance.
- `nfr_summary`: jailbreak, toxicity, rate/cost, resilience, observability, and eval-gate coverage.
- `coverage_statement`: what was checked and what was not checked.
- `blind_spots`: static-only limitations and external controls not visible in source.
- `justified_exclusions`: at least one control not required and why, unless no exclusion is available.
- `evidence_file`: path to the single evidence file.

## Decision Rules

- `block`: any blocker finding, no safe framework route, or detected framework with no adapter.
- `hold`: no blockers but one or more high findings.
- `ship_with_conditions`: no blockers/highs but medium findings remain.
- `ship`: all required controls are present, or any out-of-scope items are justified with adequate evidence and no medium-or-higher residual findings.

## Coverage Statement Template

```text
This was a static audit of <framework/entrypoints>. It checked source-visible agent guardrails, tools, approvals, retrieval, handoffs, logging, schema/validation evidence, jailbreak/NFR guardrails, and eval evidence. It did not verify controls enforced only in deployment infrastructure, external gateways, human procedures, production telemetry, IAM, or runtime configuration absent from this repository.
```

## Top Fixes Rule

List the smallest set of changes that would change the verdict first. Do not list every low-severity improvement in the verdict; keep details in evidence records.
