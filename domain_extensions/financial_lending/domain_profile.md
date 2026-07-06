# Financial Lending Domain Profile

## Identity

- `domain_id`: `financial_lending`
- Domain name: Credit, lending, and eligibility assistance
- Business line or sub-business line: Loan origination support, credit eligibility screening, adverse-action drafting, underwriter-facing summaries
- Owner: To be supplied by user/team
- Reviewer/approver: To be supplied by user/team
- Version: Draft
- Reviewed date: To be supplied by user/team

## Intended Use

Assist underwriters and loan officers with application intake summarization, document/evidence review, credit-eligibility explanation, adverse-action reason-code drafting, and applicant-facing status communication drafts.

## Prohibited Use

The agent must not autonomously approve, deny, or price a credit decision; issue a final adverse-action notice without underwriter review; use protected-class or proxy attributes as a basis for eligibility reasoning; or disclose another applicant's data in a co-applicant or household context.

## User Personas

- Loan officer.
- Underwriter.
- Credit risk analyst.
- Fair-lending or compliance reviewer.
- Model-risk reviewer.

## Harm Surfaces

- Credit/eligibility decision support that functions as a de facto decision.
- Adverse-action reason-code generation and disclosure.
- Protected-class or proxy-variable bias in reasoning or output.
- Co-applicant and household data cross-contamination.
- Sensitive applicant financial and identity data.
- Prompt injection from uploaded financial statements, pay stubs, or third-party data sources.
- Manual-review escalation boundary (edge cases that must not be auto-resolved).
- Missing or stale bureau/verification data.

## Required Human Approval Gates

- Approve the credit-eligibility explanation before it is treated as a decision rationale.
- Approve adverse-action reason codes and notice language before disclosure to an applicant.
- Approve any case routed to manual review before further automated action.
- Approve any output that references a co-applicant's or household member's data.

## Required Evidence Standard

Eligibility reasoning and adverse-action reason codes must cite the specific bureau, application, or verification fields that drove them. If required verification data is missing or stale, the agent should say so and route to manual review rather than infer a result.

## Accepted Exclusions

If the agent cannot execute final decisioning, pricing, or applicant-facing notice delivery, the team may mark those side-effect controls as out of scope only when source code, configuration, or deployment evidence proves the capability is absent.
