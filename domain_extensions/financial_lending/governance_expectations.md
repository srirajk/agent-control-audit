# Financial Lending Governance Expectations

## Inventory

- Model/agent inventory ID: To be supplied by user/team
- Owner: To be supplied by user/team
- Builder: To be supplied by user/team
- Validator: To be supplied by user/team
- Approver: To be supplied by user/team
- Risk tier: High unless scoped otherwise

## Intended Use And Limitations

The agent supports underwriter review and drafting. It is not a final decision-maker for credit approval, denial, pricing, or adverse-action notice delivery.

## Validation

Expected validation includes golden lending cases, independent fair-lending review, adverse-action reason-code accuracy tests, protected-class/proxy-variable bias tests, manual-review escalation tests, and benign false-positive tests.

## Monitoring

Monitor guardrail trip rates, underwriter overrides, disparate-impact indicators, missing-data rates, manual-review volume, latency, cost, and approval outcomes.

## Change Management

Require approval for changes to prompts, tools, retrieval sources, eligibility thresholds, reason-code mappings, model versions, golden datasets, and eval thresholds.

## Access, Retention, And Continuity

Require least privilege, segregation of duties, durable audit trails, legal hold/retention for adverse-action records, rollback plans, vendor-risk review, continuity procedures, and decommissioning criteria.

## Reporting

Governance reporting should include validation status, open findings, fair-lending monitoring trends, eval pass/fail, incidents, exceptions, material changes, and residual risk.
