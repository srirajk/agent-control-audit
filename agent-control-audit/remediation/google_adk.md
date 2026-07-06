# Google ADK Remediation

Use this file when an audit finds missing or weak Google ADK controls and the user asks to enable or fix them. Prefer ADK-native controls first, then add domain-specific code for financial/AML controls that ADK does not know about.

Primary docs to re-check for current API details before client delivery:

- `https://adk.dev/callbacks/`
- `https://adk.dev/safety/`
- `https://adk.dev/evaluate/`
- `https://adk.dev/tools-custom/confirmation/`
- `https://adk.dev/agents/models/litellm/`

## Fix Order

1. Add blocking input and model callbacks for intent, jailbreak, prompt injection, and unsupported AML requests: `C001`, `C017`, `C018`.
2. Protect every sensitive tool before execution: authorization, semantic argument validation, confirmation, limits, and audit logging: `C003`, `C004`, `C005`, `C006`, `C011`.
3. Scope retrieval and validate evidence-grounded claims: `C007`, `C008`, `C009`, `C010`.
4. Constrain multi-agent or workflow transitions: `C012`, `C013`, `C014`.
5. Add NFR controls for rate, cost, timeout, retry, fallback, monitoring, and incidents: `C019`, `C020`, `C021`.
6. Add eval and governance evidence: `C016`, `C022`, `C023-C036`.

## ADK-Native Patterns

### Callbacks And Plugins

- Use `before_agent_callback` or `before_model_callback` to block unsupported intents, jailbreaks, prompt injection, or prohibited AML actions before the model runs.
- Use `before_tool_callback` to enforce tool authorization, customer/case ownership, semantic arguments, kill switches, and human approval before side effects.
- Use `after_tool_callback` to redact/minimize tool output before it returns to the model.
- Use `after_agent_callback` or `after_model_callback` to validate final output for grounding, prohibited claims, tipping-off, missing caveats, and sensitive-data leakage.
- Use ADK plugins for reusable security guardrails when the same policy should apply across multiple agents.

### Tool Confirmation

- Use ADK action confirmation for high-impact tools: SAR narrative finalization, RFI generation, client exit recommendation, alert closure, case closure, external notification, or any write-back to a case-management system.
- Confirmation must pause before the tool performs the side effect. A natural-language instruction to "ask the analyst" is weak.
- Store approval/rejection decisions with actor, timestamp, case ID, tool name, reason, and evidence hash.

### Sessions, State, And Evidence

- Use ADK session/state context for correlation IDs, evidence versions, case IDs, and analyst-review state.
- Minimize state passed between agents/tools. Do not store raw account numbers, full identifiers, secrets, or unnecessary customer history in session memory.
- Record durable audit events for allow, deny, redact, approve, reject, execute, retry, fallback, and final-response decisions.

### Retrieval And MCP Tools

- Scope MCP, BigQuery, search, and case-management tools by tenant, business line, case ID, source system, freshness, and approved corpus.
- Treat retrieved documents, adverse-media pages, and tool outputs as untrusted. Strip or quarantine instructions embedded in retrieved content.
- Require citation/evidence IDs for material allegations in case summaries, due-diligence reports, and SAR/RFI narratives.

### Eval And Governance

- Use ADK evals where already present, but generate DeepEval-first suites for client-facing evidence.
- Keep deterministic hard assertions for missing approval, unauthorized tool calls, data leakage, missing citations, forbidden phrases, and max tool-call budgets.
- Capture model version, ADK version, dataset hash, thresholds, owners, intended use, validation date, and residual risk in the report.

## AML Reference Pattern

For an AML investigation assistant, define explicit gates:

- Gate 1 after transaction enrichment/selection: analyst approves selected transactions and derived parties before due diligence.
- Gate 2 after due diligence: analyst reviews party summaries, evidence, and missing-data warnings before case analysis.
- Gate 3 after case analysis: analyst approves recommendation before SAR/RFI/client-exit/post-disposition actions.

Do not let the agent autonomously file a SAR, close an alert, recommend client exit, contact a customer, or mutate case-management records without a source-visible approval path.

## Remediation Shape

For before/after remediation, compare the current agent against this shape: an as-is ADK AML agent usually has tools and analyst-facing prompts but lacks blocking callbacks, confirmation gates, evidence-ledger writes, eval metadata, and governance controls. A guarded ADK AML agent should bind callbacks and confirmations directly to risky tools, require evidence IDs for material claims, redact unnecessary identifiers, log approval decisions, and publish eval/governance metadata.
