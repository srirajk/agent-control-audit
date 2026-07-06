# Financial AML Governance Expectations

## Inventory

- Model/agent inventory ID: To be supplied by user/team
- Owner: To be supplied by user/team
- Builder: To be supplied by user/team
- Validator: To be supplied by user/team
- Approver: To be supplied by user/team
- Risk tier: High unless scoped otherwise

## Intended Use And Limitations

The agent supports analyst investigation and drafting. It is not a final decision-maker for SAR filing, case closure, customer contact, or client exit.

## Validation

Expected validation includes golden AML cases, independent review, SAR/case-closure approval tests, tipping-off tests, grounding tests, prompt-injection tests, leakage tests, and benign false-positive tests.

## Monitoring

Monitor guardrail trip rates, analyst overrides, false positives, missed typologies, source freshness, missing-data rates, latency, cost, tool failures, and approval outcomes.

## Change Management

Require approval for changes to prompts, tools, retrieval sources, policy thresholds, model versions, typology mappings, golden datasets, and eval thresholds.

## Access, Retention, And Continuity

Require least privilege, segregation of duties, durable audit trails, legal hold/retention, rollback plans, vendor-risk review, continuity procedures, and decommissioning criteria.

## Reporting

Governance reporting should include validation status, open findings, eval pass/fail, incidents, exceptions, monitoring trends, material changes, and residual risk.
