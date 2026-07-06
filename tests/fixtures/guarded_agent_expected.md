# Guarded Agent Expected Result

`tests/fixtures/financial_agent_guarded/` demonstrates source-visible controls for the same financial agent shape as `tests/fixtures/financial_agent/`.

The static first pass should detect OpenAI Agents SDK and source-visible evidence for:

- `C001` input guardrail
- `C002` output guardrail
- `C003` tool authorization
- `C004` semantic argument validation
- `C005` human approval gate
- `C006` transaction limits and kill switch
- `C007` retrieval source scope
- `C008` grounding validation
- `C009` data minimization
- `C010` sensitive data redaction
- `C011` audit logging
- `C012` handoff authority boundary
- `C013` handoff input filter
- `C014` handoff provenance
- `C016` reproducibility evidence
- `C017` prompt-injection and jailbreak resistance
- `C018` toxicity and abuse content safety
- `C019` rate/cost boundary
- `C020` timeout/fallback behavior
- `C021` operational observability hooks
- `C022` eval harness evidence

This fixture is still static evidence only. It is a demonstration of what the auditor should recognize, not a claim that a production deployment is safe.
