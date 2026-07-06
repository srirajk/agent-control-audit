# Domain Extension Guide

Use this when adding a new domain or sub-business-line profile to `agent-control-audit`.

The engine should remain domain-neutral. Add domain knowledge as a regime profile, dataset pack, and report vocabulary instead of hard-coding it into the scanner unless the evidence pattern is broadly useful across domains.

## Domain Pack Shape

A domain pack should define:

- `domain_id`: stable lowercase identifier such as `financial`, `financial_aml`, `healthcare`, or `enterprise_it`.
- `business_lines`: subdomains covered by this profile.
- `harm_surfaces`: risky capabilities or outcomes the agent can touch.
- `requirements`: requirement IDs, text, applies-when logic, required controls, severity floor, and source.
- `eval_suites`: golden dataset categories that prove the required controls work.
- `quality_profile`: recommended suite coverage, metadata keys, scoring weights, and readiness thresholds.
- `evidence_expectations`: artifacts a client may provide outside source code.
- `accepted_exclusions`: cases where a control is not required and what evidence proves that.
- `report_terms`: domain language for the final report.

## Financial Subdomain Pattern

Financial services should usually stay under the financial regime, with optional overlays for sub-business lines:

- `financial_aml`: SAR/case closure, alert triage, KYC, transaction monitoring, sanctions, adverse media, analyst approval, narrative grounding.
- `financial_payments`: ACH/wire/refund/payment session, merchant operations, transaction limits, idempotency, fraud escalation, settlement impact.
- `financial_lending`: credit eligibility, adverse action, fair lending, explainability, protected-class analysis, model validation.
- `financial_wealth`: suitability boundaries, investment advice traps, portfolio recommendations, source freshness, disclosure controls.
- `financial_markets`: trading support, order routing, market data freshness, pre-trade approval, surveillance, benchmark/backtest evidence.
- `financial_treasury`: liquidity, reconciliation, treasury ops, reporting, dual control, change approval, continuity.
- `financial_customer_support`: regulated communication, complaint handling, customer data minimization, escalation, toxicity, retention.

Do not create a separate engine for each subdomain. Add applies-when logic, datasets, and evidence expectations that refine the base financial controls.

## Requirement Template

```markdown
### <DOMAIN>-<NNN> <Short Requirement Name>

- `requirement_id`: `<DOMAIN>-<NNN>`
- `requirement_text`: <one or two sentences>
- `applies_when`: <machine-checkable or reviewer-checkable trigger>
- `requires_controls`: `C001`, `C002`
- `severity_floor`: `medium|high|blocker`
- `source`: `author_policy` or approved source identifier
```

## Dataset Pack Template

Each domain should include cases for:

- Benign allowed behavior.
- Direct policy bypass attempts.
- Indirect prompt injection through files, retrieval, tools, or handoffs.
- Unauthorized tool use.
- Sensitive-data leakage.
- Ungrounded or stale claims.
- Domain-specific high-risk decisions.
- Toxicity/abuse when humans interact with the agent.
- NFR failures: timeout, retry, cost, rate, fallback, duplicate side effects.
- Governance evidence checks when model risk or release readiness is claimed.

Use the canonical dataset schema in `evals/dataset_schema.md`. Do not invent a new schema unless the canonical schema cannot represent the domain case.

## Evidence Expectations

A mature domain profile should accept evidence from:

- Source code and configuration.
- Model cards or intended-use documents.
- Control inventories.
- Validation reports.
- Data lineage and quality reports.
- Monitoring dashboards or exports.
- Benchmark/backtest summaries.
- Fairness/bias reports.
- Access-control and change-approval records.
- Incident, retention, legal-hold, continuity, and decommissioning procedures.

Static source evidence can be enough for early triage. Governance acceptance usually requires external artifacts represented in the target repository or supplied by the client.

## Adding A New Domain

1. Create `regimes/<domain>.md` using the requirement template.
2. Add domain-specific starter datasets under `evals/datasets/` only when they are synthetic and broadly reusable.
3. Add or update a profile in `evals/quality_profiles.json` so dataset readiness checks match the domain.
4. Update `engine/mapping.md` if the domain introduces new harm surfaces or applies-when rules.
5. Update `scripts/static_audit.py` only for broadly reusable source patterns or when deterministic detection is needed.
6. Update `output/report_template.md` only if the report needs a reusable section.
7. Add a guarded fixture only when the domain needs acceptance testing.
8. Run the repository's deterministic scanner/eval smoke tests and the skill quick validator.

## Quality Profile Template

```json
{
  "my_domain": {
    "profile_id": "my_domain",
    "description": "Dataset quality expectations for my domain.",
    "extends": "default",
    "recommended_suites": [
      "jailbreak_direct",
      "prompt_injection_indirect",
      "domain_specific_high_risk_decision",
      "benign_false_positives"
    ],
    "owner_metadata_keys": ["owner", "reviewer", "approved_by"],
    "version_metadata_keys": ["dataset_version", "reviewed_at"],
    "readiness_thresholds": {
      "eval_ready_score": 70,
      "governance_grade_score": 85,
      "governance_metadata_ratio": 0.8
    }
  }
}
```

## Quality Bar

A domain pack is not "done" when it has many requirements. It is done when:

- The required controls are explainable to a domain owner.
- The eval cases catch realistic failures and include benign false positives.
- The evidence expectations match artifacts clients actually have.
- The report points to actionable remediation.
- The profile avoids pretending that missing runtime or governance evidence is present.
