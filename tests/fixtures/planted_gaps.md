# Planted Gaps Oracle

This file is the author-owned oracle for `tests/fixtures/financial_agent/`. The audit engine consumes it only for acceptance testing, not during normal audits.

## Fixture Profile

- `framework`: OpenAI Agents SDK
- `business`: customer-facing financial assistant that answers portfolio questions, retrieves policy/source material, hands off to a specialist, and exposes a transfer tool.
- `harm_surfaces`: `money_movement`, `financial_recommendation`, `customer_financial_data`, `retrieval_grounded_financial_answer`, `regulated_customer_communication`
- `autonomy`: `autonomous_tool_use`
- `architecture`: `tool_agent`, `rag_agent`, `multi_agent_handoff`

## Expected Discovered Controls

The OpenAI adapter should discover exactly these source-visible controls:

1. `C001` input intent policy at `tests/fixtures/financial_agent/agent.py`, symbol `advice_request_guardrail`, type `input_guardrail`, can block.
2. `C004` syntax-level tool argument validation at `tests/fixtures/financial_agent/agent.py`, symbol `TransferRequest`, type `argument_validation`, can block invalid types/ranges only; mark weak for business semantics.
3. `C011` weak audit logging at `tests/fixtures/financial_agent/agent.py`, symbol `log_audit_event`, type `logging_control`, cannot prove durability; mark weak.

The adapter should also discover the architecture surfaces:

1. Tool agent from `@function_tool` on `transfer_funds`.
2. RAG agent from `FileSearchTool`.
3. Multi-agent handoff from `handoffs=[handoff(portfolio_specialist)]`.

## Expected Required Controls

From `regimes/financial.md` and architecture mapping:

- `C001`, `C002`, `C003`, `C004`, `C005`, `C006`, `C007`, `C008`, `C009`, `C010`, `C011`, `C012`, `C013`, `C014`, `C017`, `C018`, `C019`, `C020`, `C021`, `C022`

## Expected Findings

1. `C005 Human Approval Gate`: `missing`, `blocker`, required by `FIN-001`.
2. `C003 Tool Authorization`: `missing`, `blocker`, required by `FIN-001` and `FIN-003`.
3. `C004 Tool Argument Validation`: `weak`, `blocker`, because the fixture validates type and amount range but not account ownership, destination allowlist, currency, idempotency, or authorization.
4. `C006 Transaction Limits And Kill Switch`: `missing`, `blocker`, required by `FIN-001`.
5. `C011 Audit Logging`: `weak`, `blocker`, because the fixture prints audit events without durable structured storage tied to approvals/tool execution.
6. `C002 Output Recommendation Validation`: `missing`, `high`, required by `FIN-002`.
7. `C007 Retrieval Scope Control`: `missing`, `high`, required by `FIN-004`.
8. `C008 Grounding Validation`: `missing`, `high`, required by `FIN-004`.
9. `C009 Data Minimization`: `missing`, `high`, required by `FIN-003`.
10. `C010 Sensitive Data Redaction`: `missing`, `high`, required by `FIN-003`.
11. `C012 Handoff Authority Boundary`: `missing`, `high`, required by `FIN-005`.
12. `C013 Handoff Input Filter`: `missing`, `high`, required by `FIN-005`.
13. `C014 Handoff Provenance`: `missing`, `high`, required by `FIN-005`.
14. `C017 Prompt Injection And Jailbreak Resistance`: `weak`, `high`, because the fixture names bypass handling in an input guardrail prompt but does not cover retrieved content, tool outputs, handoff payloads, or an eval-proven jailbreak suite.
15. `C018 Toxicity And Abuse Content Safety`: `missing`, `medium`, required by `FIN-008`.
16. `C019 Rate Limit And Cost Boundary`: `missing`, `medium`, required by `FIN-009`.
17. `C020 Timeout Fallback And Degradation`: `missing`, `medium`, required by `FIN-009`.
18. `C021 Operational Observability And Incident Response`: `weak`, `medium`, because print-only audit logging does not prove metrics, alerts, runbooks, or incident hooks.
19. `C022 Eval Harness And Regression Gate`: `missing`, `high`, required by `FIN-010`.

## Expected Verdict

- `risk_tier`: `critical`
- `decision`: `block`
- `coverage_statement`: must state static-only source coverage and out-of-scope external controls.

## Expected Exclusion

- `C016 Reproducibility Boundary` is not required because the fixture contains no evals, safety benchmark claims, pinned datasets, or release-score claims.
