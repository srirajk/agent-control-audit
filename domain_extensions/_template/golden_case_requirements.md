# Golden Case Requirements Template

## Required Case Families

- Benign allowed behavior.
- Direct jailbreak or policy bypass.
- Indirect prompt injection through retrieved content, files, tool output, or handoffs.
- Unauthorized tool use.
- Sensitive-data leakage.
- Grounding or stale-source failure.
- Domain-specific high-risk decision.
- Toxicity or abusive interaction.
- NFR failure: timeout, retry, rate, cost, fallback, duplicate side effect.
- Governance evidence check when release readiness is claimed.

## Required Fields Per Case

- Stable case ID.
- Suite/category.
- User input.
- Expected behavior.
- Forbidden outcome.
- Severity.
- Source.
- Owner or reviewer.
- Dataset version or reviewed date.
- Machine-checkable assertion.

## Machine-Checkable Assertion Examples

- Forbidden tool must not be called.
- Approval must be requested.
- Required phrase or reason code must appear.
- Forbidden phrase must not appear.
- Citation/evidence ID must be present.
- Maximum tool calls must not be exceeded.
- Output must be blocked or redacted.

## Approval Rule

Generated seed cases are only proposed cases. They become golden only after domain owner or user/team approval.
