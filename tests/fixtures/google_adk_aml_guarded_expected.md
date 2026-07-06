# Google ADK AML Guarded Fixture Expected Result

`tests/fixtures/google_adk_aml_guarded/agent.py` is expected to route as `google_adk` and demonstrate source-visible coverage for the core AML guardrail pattern:

- Input/output callbacks and safety policy.
- Tool authorization, semantic argument validation, confirmation, limits, and audit logs.
- Retrieval scope, citation/grounding checks, minimization, and redaction.
- Handoff allowlist, payload filtering, and provenance.
- Prompt-injection, toxicity, NFR, eval, and governance evidence.

The fixture should not be treated as a production AML implementation. It is a compact scanner/remediation reference.
