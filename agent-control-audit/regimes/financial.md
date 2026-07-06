# Financial Regime Requirements

author_approved: true

This file is the author-supplied financial control ground truth consumed by the mapper. It is not a summary of external law and should be replaced with organization-approved regulatory text before real legal or compliance use.

## Requirement Format

Each requirement provides `requirement_id`, `requirement_text`, `applies_when`, `requires_controls`, `severity_floor`, and `source`.

## Requirements

### FIN-001 Financial Side Effects

- `requirement_id`: `FIN-001`
- `requirement_text`: Agents that can move money, modify financial accounts, execute trades, submit financial forms, or trigger externally visible financial actions must enforce authorization, semantic argument validation, human approval, transaction limits, and audit logging before the action executes.
- `applies_when`: `harm_surfaces` includes `money_movement` or the agent has side-effecting financial tools.
- `requires_controls`: `C003`, `C004`, `C005`, `C006`, `C011`
- `severity_floor`: `blocker`
- `source`: `author_policy`

### FIN-002 Financial Recommendation Output

- `requirement_id`: `FIN-002`
- `requirement_text`: Agents that provide personalized financial recommendations, investment/trading guidance, credit/eligibility guidance, or customer-facing regulated financial communication must block unsupported requests and validate final output before release.
- `applies_when`: `harm_surfaces` includes `financial_recommendation`, `credit_or_eligibility`, or `regulated_customer_communication`.
- `requires_controls`: `C001`, `C002`
- `severity_floor`: `high`
- `source`: `author_policy`

### FIN-003 Customer Financial Data

- `requirement_id`: `FIN-003`
- `requirement_text`: Agents that process customer financial data must minimize data exposure, redact sensitive data in prompts/tools/logs/output, authorize data access, and preserve audit logs of access and disclosure decisions.
- `applies_when`: `harm_surfaces` includes `customer_financial_data`, or tools/retrieval/memory expose account, transaction, balance, identity, tax, or payment data.
- `requires_controls`: `C003`, `C009`, `C010`, `C011`
- `severity_floor`: `high`
- `source`: `author_policy`

### FIN-004 Retrieval-Grounded Financial Answers

- `requirement_id`: `FIN-004`
- `requirement_text`: Agents that answer financial questions from retrieved sources must restrict retrieval to approved sources and validate that material claims are grounded in current, relevant sources.
- `applies_when`: `architecture` includes `rag_agent` or `harm_surfaces` includes `retrieval_grounded_financial_answer`.
- `requires_controls`: `C007`, `C008`
- `severity_floor`: `high`
- `source`: `author_policy`

### FIN-005 Multi-Agent Financial Delegation

- `requirement_id`: `FIN-005`
- `requirement_text`: Multi-agent financial workflows must constrain handoff destinations and authority, filter transferred context, and preserve handoff provenance.
- `applies_when`: `architecture` includes `multi_agent_handoff` or `agent_as_tool`.
- `requires_controls`: `C012`, `C013`, `C014`
- `severity_floor`: `high`
- `source`: `author_policy`

### FIN-006 Reproducible Audit Claims

- `requirement_id`: `FIN-006`
- `requirement_text`: Safety claims that depend on model behavior, datasets, or evaluation runs must pin versions and report variance or confidence instead of a single unsupported score.
- `applies_when`: the repository contains evals, safety benchmarks, or release claims used as control evidence.
- `requires_controls`: `C016`
- `severity_floor`: `medium`
- `source`: `author_policy`

### FIN-007 Jailbreak And Prompt Injection

- `requirement_id`: `FIN-007`
- `requirement_text`: Financial agents exposed to users, tools, retrieval, webpages, files, MCP servers, or handoffs must prevent jailbreaks and prompt injection from bypassing financial controls, exfiltrating sensitive data, or escalating tool authority.
- `applies_when`: the agent is customer-facing, retrieval-connected, tool-connected, handoff-connected, or processes untrusted text.
- `requires_controls`: `C017`
- `severity_floor`: `high`
- `source`: `author_policy`

### FIN-008 Toxicity And Abuse

- `requirement_id`: `FIN-008`
- `requirement_text`: Customer-facing financial agents must block or safely handle toxic, abusive, harassing, hateful, threatening, sexual, self-harm, violent, or brand-damaging content in inputs and outputs without blocking legitimate financial risk discussion.
- `applies_when`: the agent accepts user input or emits customer-facing, analyst-facing, public, or externally delivered communication.
- `requires_controls`: `C018`
- `severity_floor`: `medium`
- `source`: `author_policy`

### FIN-009 Operational NFR Guardrails

- `requirement_id`: `FIN-009`
- `requirement_text`: Production-facing financial agents must bound cost and rate, fail safely under model/tool/data outages, and expose safety-relevant observability for incident response.
- `applies_when`: the agent is deployed behind a UI/API/bot, calls external tools/APIs, performs retrieval, or handles customer financial data.
- `requires_controls`: `C019`, `C020`, `C021`
- `severity_floor`: `medium`
- `source`: `author_policy`

### FIN-010 Eval Regression Gate

- `requirement_id`: `FIN-010`
- `requirement_text`: High-risk financial agents must include regression evals for jailbreak, prompt injection, toxicity, sensitive-data leakage, unauthorized tool calls, grounding failures, financial-advice traps, and benign false positives, with release thresholds and hashable evidence.
- `applies_when`: the agent is customer-facing, tool-connected, retrieval-connected, multi-agent, handles customer financial data, or has any high/blocker required control.
- `requires_controls`: `C022`
- `severity_floor`: `high`
- `source`: `author_policy`

### FIN-011 Model Governance Inventory And Intended Use

- `requirement_id`: `FIN-011`
- `requirement_text`: High-risk financial agents must be registered in a model/agent inventory with named business, technical, and model-risk owners; approved intended use; prohibited use; limitations; and periodic governance reporting.
- `applies_when`: the agent is customer-facing, production-facing, tool-connected, retrieval-connected, multi-agent, handles customer financial data, or influences financial recommendations, eligibility, investigations, customer communications, or money movement.
- `requires_controls`: `C023`, `C024`, `C036`
- `severity_floor`: `high`
- `source`: `author_policy_aligned_to_model_risk_governance`

### FIN-012 Independent Validation Monitoring And Backtesting

- `requirement_id`: `FIN-012`
- `requirement_text`: High-risk financial agents must have independent validation/effective challenge, ongoing drift and outcome monitoring, and benchmark or backtesting evidence for material safety or performance claims.
- `applies_when`: the agent is high-risk, has eval-dependent safety claims, is used in financial decision support, or is released into a production-facing workflow.
- `requires_controls`: `C025`, `C027`, `C028`
- `severity_floor`: `high`
- `source`: `author_policy_aligned_to_model_risk_governance`

### FIN-013 Data Governance Fairness And Explainability

- `requirement_id`: `FIN-013`
- `requirement_text`: Financial agents that use customer, transaction, retrieval, eligibility, prioritization, or decision-support data must document data lineage and quality, test for fairness/bias where outcomes can affect people or entities, and provide reason codes or explanations suitable for review.
- `applies_when`: the agent handles customer financial data, performs retrieval-grounded financial answers, supports credit/eligibility/customer treatment/investigation prioritization, or produces recommendations that may affect financial outcomes.
- `requires_controls`: `C026`, `C029`, `C030`
- `severity_floor`: `high`
- `source`: `author_policy_aligned_to_model_risk_governance`

### FIN-014 Change Vendor Access Retention And Continuity

- `requirement_id`: `FIN-014`
- `requirement_text`: Production-facing financial agents must govern changes, third-party/model-provider dependencies, privileged access and segregation of duties, evidence retention/legal hold, rollback, continuity, and decommissioning.
- `applies_when`: the agent is production-facing, external/customer-facing, tool-connected, retrieval-connected, uses third-party models/services, or produces auditable financial decisions or communications.
- `requires_controls`: `C031`, `C032`, `C033`, `C034`, `C035`
- `severity_floor`: `medium`
- `source`: `author_policy_aligned_to_model_risk_governance`
