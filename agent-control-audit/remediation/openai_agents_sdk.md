# OpenAI Agents SDK Remediation

Use this file when an audit finds missing or weak OpenAI Agents SDK controls and the user asks to enable or fix them. Keep fixes narrow and bind each control to the execution point it protects.

## Fix Order

1. Block high-risk input before the primary agent acts: `C001`, `C017`, `C018`.
2. Protect side-effecting tools before execution: `C003`, `C004`, `C005`, `C006`, `C011`.
3. Scope and validate RAG: `C007`, `C008`, `C009`, `C010`, `C017`.
4. Constrain handoffs: `C012`, `C013`, `C014`.
5. Add NFR controls: `C019`, `C020`, `C021`.
6. Add eval and reproducibility evidence: `C016`, `C022`.

## Required Implementation Patterns

### Input And Output Guardrails

- Add `@input_guardrail` functions for unsupported financial requests, jailbreak attempts, content safety, and authority boundaries.
- Add `@output_guardrail` functions for financial claims, grounding, caveats, and regulated communication.
- Ensure guardrails return a blocking/tripwire path, not only notes.

### Tool Controls

- Bind authorization checks inside or immediately before every sensitive tool.
- Add semantic argument validation beyond schema typing: account ownership, destination allowlist, currency, idempotency key, amount limits, daily limits, and kill switch.
- Add approval gates such as `needs_approval=True` or an equivalent pause/review flow before money movement, refunds, trades, account changes, or external notifications.
- Record structured audit logs for allow, deny, approve, reject, and execute outcomes.

### RAG Controls

- Restrict retrieval to approved corpora, tenants, accounts, and freshness windows.
- Treat retrieved documents, webpages, files, and tool results as untrusted data.
- Detect or quarantine indirect prompt injection in retrieved/tool content.
- Validate material financial claims against citations before final output.

### Handoff Controls

- Use destination allowlists and explicit authority checks.
- Filter handoff input and redact unnecessary history, customer data, tool outputs, and retrieved content.
- Record handoff provenance: source, destination, reason, data moved, and accepted responsibility.

### NFR Controls

- Add rate limits, quotas, token budgets, max tool calls, max turns, and cost budgets.
- Add timeouts, bounded retries, fallback responses, circuit breakers, and duplicate-side-effect prevention.
- Add metrics, traces, alerts, correlation IDs, and incident hooks for guardrail trips, tool denials, approval decisions, jailbreak attempts, and eval regressions.

### Eval Controls

- Add golden datasets under `evals/datasets/`.
- Run `scripts/eval_runner.py` against recorded or live agent results.
- Store dataset hash, model version, seed, thresholds, and summary.
- Gate release on jailbreak, prompt-injection, data-leakage, grounding, unauthorized-tool, toxicity, NFR, and benign false-positive suites.

## Remediation Shape

A guarded OpenAI Agents SDK financial agent should demonstrate:

- Input and output guardrails.
- Authorization, semantic validation, approval, limits, and audit logging.
- Retrieval scope and grounding validation.
- Data minimization and redaction.
- Handoff authority, filtering, and provenance.
- Prompt-injection, toxicity, rate/cost, timeout/fallback, observability, and eval metadata.

This is a source-visible remediation pattern, not a claim of production readiness. Verify that each control is bound to the execution point it protects.
