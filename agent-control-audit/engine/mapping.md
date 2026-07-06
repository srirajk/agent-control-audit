# Required-Control Mapping

The derive step maps `{harm surface, regime, autonomy, architecture}` to the minimum ranked required control set. It must run independently of discovered controls. Do not add a control because it is easy to detect, and do not omit a control because it is missing.

## Inputs

Build a target profile from repository evidence:

- `business`: what the agent does for users or operators.
- `harm_surfaces`: one or more of `money_movement`, `financial_recommendation`, `credit_or_eligibility`, `customer_financial_data`, `regulated_customer_communication`, `retrieval_grounded_financial_answer`, `jailbreak_or_prompt_injection`, `toxicity_or_abuse`, `operational_failure`, `cost_or_resource_exhaustion`, `internal_financial_ops`.
- `regime`: `financial`, loaded from `regimes/financial.md`.
- `autonomy`: `answer_only`, `draft_only`, `tool_with_confirmation`, `autonomous_tool_use`, or `delegated_multi_agent`.
- `architecture`: `single_agent`, `tool_agent`, `rag_agent`, `multi_agent_handoff`, `agent_as_tool`, `stateful_memory`, or combinations.

If the profile cannot be determined from static evidence, record the uncertainty and choose the more conservative applicable category only when the evidence shows the capability exists. Example: a transfer tool proves `money_movement`; a vague "financial assistant" prompt alone does not.

## Regime Consumption

Load `regimes/financial.md` as author-supplied ground truth. Each requirement must provide:

- `requirement_id`
- `requirement_text`
- `applies_when`
- `requires_controls`
- `severity_floor`
- `source`

If the regime file is absent, empty, or marked `author_approved: false`, stop. If a requirement is ambiguous, flag it as `not_checked` and ask for author clarification; do not invent a replacement.

## Derivation Algorithm

1. Initialize `required_controls` as an empty set.
2. For each financial requirement, evaluate `applies_when` against the target profile using only repository evidence and explicit author text.
3. Add each listed `requires_controls` item with provenance `{requirement_id, requirement_text, source}` and severity at least `severity_floor`.
4. Add architecture controls below when the architecture is present. These are engineering controls, not regulatory claims, and must still trace to the architecture evidence.
5. Add NFR controls below when the agent is customer-facing, production-facing, retrieval-connected, tool-connected, or high-risk.
6. Add model-governance controls below when the agent is high-risk, production-facing, or decision-supporting.
7. Add autonomy controls below when the autonomy level is present.
8. Merge duplicates by `control_id`. Preserve all requirement provenance and keep the highest severity floor.
9. Remove controls that are explicitly inapplicable only when both conditions hold: the architecture/harm surface is absent, and no regime requirement independently demands the control.
10. Produce at least one justified exclusion. If every catalog control is required, justify why no exclusion is available instead of fabricating one.
11. Rank with `engine/severity.md`.

## Architecture Additions

### Tool Agent

When the agent can call custom, hosted, local, MCP, shell, computer, code, payment, account, CRM, ticketing, or data tools:

- Require `C003 Tool Authorization` for tools that read sensitive data or perform side effects.
- Require `C004 Tool Argument Validation` for all tools with user/model-controlled arguments.
- Require `C005 Human Approval Gate` for high-impact, irreversible, external, money-moving, account-changing, or policy-sensitive tools.
- Require `C011 Audit Logging` for side-effecting tools and sensitive-data access.

### RAG Agent

When the agent uses retrieval, file search, vector stores, web search, MCP retrieval, document stores, or knowledge-base tools:

- Require `C007 Retrieval Scope Control`.
- Require `C008 Grounding Validation` for user-facing financial claims.
- Require `C009 Data Minimization` when retrieved content may include customer or account data.
- Require `C017 Prompt Injection And Jailbreak Resistance` for indirect prompt-injection through retrieved documents, webpages, files, or tool results.

### Multi-Agent Handoff

When the agent transfers control through handoffs or exposes agents as tools:

- Require `C012 Handoff Authority Boundary`.
- Require `C013 Handoff Input Filter` when conversation history, tool results, files, or customer data can cross the boundary.
- Require `C014 Handoff Provenance` for financial workflows.
- Require tool-agent controls from the Tool Agent section when an agent is exposed with `Agent.as_tool(...)`.

### Stateful Memory

When the agent persists conversation state, user profile data, account facts, embeddings, or long-term memory:

- Require `C009 Data Minimization`.
- Require `C010 Sensitive Data Redaction` for memory writes or memory-fed prompts.
- Require `C011 Audit Logging` when memory changes affect decisions or entitlements.

## NFR Additions

NFR controls are not optional polish for financial agents. They prevent non-functional failures from becoming safety failures.

### Customer-Facing Agent

When a user, customer, merchant, advisor, analyst, or external API can interact with the agent:

- Require `C017 Prompt Injection And Jailbreak Resistance`.
- Require `C018 Toxicity And Abuse Content Safety`.
- Require `C019 Rate Limit And Cost Boundary`.
- Require `C020 Timeout Fallback And Degradation`.
- Require `C021 Operational Observability And Incident Response`.
- Require `C022 Eval Harness And Regression Gate` when the agent influences financial decisions, customer communications, tools, retrieval, or reports.

### Production-Facing Or Tool-Connected Agent

When the agent calls external APIs, payment/refund tools, market data APIs, document stores, MCP servers, web search, message systems, databases, or ticketing systems:

- Require `C019 Rate Limit And Cost Boundary`.
- Require `C020 Timeout Fallback And Degradation`.
- Require `C021 Operational Observability And Incident Response`.
- Require `C022 Eval Harness And Regression Gate` for unauthorized tool-call and failure-mode scenarios.

### High-Risk Financial Agent

When any required control is `blocker` or `high`, require `C022 Eval Harness And Regression Gate`. If the eval harness is used to support a safety or release claim, also require `C016 Reproducibility Boundary`.

## Model Governance Additions

Model governance controls are required when the agent is not merely a throwaway local prototype. They answer the model-risk questions a financial governance team will ask before relying on eval scores.

### High-Risk Financial Or Production-Facing Agent

When the agent is customer-facing, production-facing, tool-connected, retrieval-connected, multi-agent, handles customer financial data, or influences financial recommendations, investigations, eligibility, customer communications, or money movement:

- Require `C023 Model Inventory And Ownership`.
- Require `C024 Intended Use And Limitations`.
- Require `C036 Model Governance Reporting`.

### Eval-Dependent Or Decision-Support Agent

When the repository claims safety, quality, accuracy, compliance, or release readiness using evals, benchmarks, red-team results, or validation reports:

- Require `C025 Independent Validation And Effective Challenge`.
- Require `C027 Drift And Outcome Monitoring`.
- Require `C028 Benchmarking And Backtesting`.

### Data-Driven Financial Agent

When the agent uses customer data, transaction data, retrieval sources, feature stores, analyst labels, case histories, or decision-support inputs:

- Require `C026 Data Lineage And Quality`.
- Require `C030 Explainability And Reason Codes` when outputs affect customer treatment, investigations, recommendations, or regulated communication.
- Require `C029 Fairness And Bias Testing` when the workflow can affect people, entities, eligibility, prioritization, escalation, or customer treatment.

### Operational Governance

When the agent is production-facing, vendor/model-provider dependent, tool-connected, retrieval-connected, externally exposed, or generates auditable decisions:

- Require `C031 Change Management And Release Approval`.
- Require `C032 Third-Party And Vendor Model Risk`.
- Require `C033 Access Control And Segregation Of Duties`.
- Require `C034 Evidence Retention And Legal Hold`.
- Require `C035 Business Continuity Rollback And Decommissioning`.

## Autonomy Additions

- `answer_only`: require output controls only when the regime or harm surface demands them.
- `draft_only`: require output validation for drafts that users may send externally.
- `tool_with_confirmation`: require argument validation and logging; require approval if the confirmation is outside the codebase and cannot be statically verified, with status `out_of_scope` or `weak` depending on evidence.
- `autonomous_tool_use`: require approval, limits, authorization, argument validation, and logging for sensitive or side-effecting tools.
- `delegated_multi_agent`: require all multi-agent handoff controls and provenance.

## Harm Surface Floors

Use these floors unless the regime sets a higher floor:

- `money_movement`: blocker for missing approval, authorization, semantic argument validation, or audit logging.
- `credit_or_eligibility`: blocker for missing input/output policy controls that prevent unsupported eligibility decisions.
- `financial_recommendation`: high for missing input/output policy controls; blocker when the agent can also execute trades or account changes.
- `customer_financial_data`: high for missing data minimization, redaction, or authorization; blocker when leakage is likely through tools or handoffs.
- `retrieval_grounded_financial_answer`: high for missing retrieval scope or grounding; medium when only internal non-customer drafting is affected.
- `jailbreak_or_prompt_injection`: high for missing controls on customer-facing agents; blocker when successful bypass could trigger financial side effects, handoff authority transfer, or sensitive-data exfiltration.
- `toxicity_or_abuse`: medium for missing controls on customer-facing agents; high when the agent produces regulated customer communication or public brand output.
- `operational_failure`: medium for missing timeout/fallback/observability; high when retries can duplicate side effects or failures can silently emit financial advice.
- `cost_or_resource_exhaustion`: medium by default; high when loops, broad retrieval, or tool fanout can cause material spend or service denial.
- `internal_financial_ops`: medium by default; high when tools can change records or notify external parties.

## Compare Logic

For each required control:

- `missing`: no discovered control maps to the required control.
- `weak`: a control exists but lacks coverage, business semantics, durability, or a blocking path required by the risk.
- `misconfigured`: a control exists but is attached to the wrong agent/tool/stage, has disabled settings, cannot run before the risky action, or does not inspect the relevant data.
- `present`: the control is bound to the relevant execution point and meets adequacy criteria in `control_catalog.md`.
- `out_of_scope`: the requirement may be satisfied outside the repository, but static evidence cannot verify it.
- `not_checked`: the adapter or source evidence could not inspect this control class.

## Justified Exclusions

Name controls the agent does not need. Examples:

- Exclude handoff controls for a confirmed single-agent architecture with no `handoffs`, `Agent.as_tool`, graph edges, or delegated specialists.
- Exclude retrieval controls for an agent with no retrieval, file search, web search, knowledge-base, vector-store, or document-access path.
- Exclude money-movement approval controls for an answer-only financial education agent with no tools and no transaction workflow, unless the regime demands approval for the output itself.
- Exclude toxicity controls only for non-interactive internal batch jobs whose outputs never reach users, customers, analysts, or external systems.
- Exclude eval harness controls only for toy fixtures or prototypes with no release, safety, financial, customer-facing, retrieval, or tool-use path.
- Exclude model governance inventory/reporting controls only for confirmed throwaway local prototypes with no production path, customer data, model-risk claim, release decision, or external/user-facing output.
- Exclude fairness controls only when the agent cannot influence eligibility, prioritization, investigation escalation, customer treatment, regulated communication, or other people/entity-impacting outcomes.
- Exclude vendor model-risk controls only when no third-party model, hosted provider, external API/tool, MCP server, dataset, or managed retrieval service is used.

An exclusion must cite the evidence that makes the surface absent.
