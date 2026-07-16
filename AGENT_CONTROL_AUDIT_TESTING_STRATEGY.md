# AI Agent Testing & Assurance Strategy

**Scope:** Any AI agent operating in or adjacent to regulated financial compliance workflows (alert triage, investigation support, report drafting, case management, due diligence support) at a large financial institution with significant regulatory exposure.

**Structure:** Two phases, deliberately separated. Phase 1 (Pre-Shipping) is implemented and demonstrable today. Phase 2 (Post-Shipping / Production) is the roadmap extension, grounded in industry precedent, not yet built. This separation is intentional — a model-risk or compliance reviewer will ask "is this live or theoretical," and conflating the two costs more trust than naming the gap.

---

## 1. Executive Summary

Testing a regulated-workflow agent is not a quality-assurance exercise — it's a control derivation exercise. The question is never "does the agent work," it's "given this agent's harm surface, autonomy level, and regulatory exposure, what controls are required, which ones exist, and can we prove it — today, and every day it keeps running."

This strategy has three pillars:

1. **Derive, don't template.** Required controls are computed per-agent from harm surface + architecture + domain regime + autonomy — not applied from a fixed checklist.
2. **Prove, don't assume.** Every control claim carries hashable evidence — file/line citations for static findings, transcript/trace evidence for dynamic findings, human-adjudicated ground truth for eval correctness.
3. **Compound, don't repeat.** Every human override of an agent decision — in QC review, in production — becomes new golden-dataset evidence, so the eval suite gets stronger over time instead of staying frozen at initial scope.

---

## 2. Regulatory & Industry Grounding

### 2.1 Regulatory anchor
Federal Reserve, OCC, and FDIC guidance treats existing model risk management frameworks (SR 11-7 and its interagency equivalents) as applicable to machine learning and AI systems — there is no compliance exemption for "it's an LLM, not a model." For regulated financial workflows, this means:
- Conceptual soundness review (design quality, documentation) before deployment
- Ongoing monitoring, not point-in-time sign-off
- Independent validation on a recurring cadence
- Full evidentiary trail available on regulator request

### 2.2 Industry precedent (validates the approach, doesn't replace it)

| Company | Relevant mechanic | Where it maps in our strategy |
|---|---|---|
| **Google (Vertex AI / ADK)** | Inner-loop (fast local eval) vs. outer-loop (scaled Vertex eval); trajectory metrics separate from final-response metrics; shadow deployment to a private tagged revision, evaluated before promotion to full traffic | Validates our static/dynamic split and process/outcome eval split (§5); shadow deployment pattern directly informs Phase 2 staged rollout (§6.1) |
| **AWS (Bedrock / AgentCore)** | Three-layer eval: task correctness, trajectory quality, system-level health; Automated Reasoning checks — formal mathematical verification of responses against a structured policy, not just probabilistic LLM-judge scoring | "System-level health" as an explicit third eval layer (§5.5); Automated Reasoning as a Phase 2 upgrade path for deterministic hard gates in high-stakes cases (§6.2) |
| **Robinhood** | Live production Bedrock deployment for financial-crimes investigation workflows; agentic trading product uses fund-limited, agent-specific sub-accounts as a bounded-autonomy control | Proof this exact use case (compliance-adjacent agent) is already in production elsewhere; bounded-autonomy-by-design as a control pattern independent of testing (§4.3) |
| **Palantir (AIP)** | AIP Evals built explicitly around golden-dataset testing, iteration, and cross-model variance comparison to prevent hallucination/safety-constraint violation pre-production | Validates our consent-gated golden dataset flow (§5.3) |

### 2.3 Known industry gap we are explicitly closing
Independent analysis of both AWS Bedrock's and generic agent-eval tooling notes that built-in evaluation typically runs as a one-shot batch job with no built-in path connecting a guardrail change, knowledge-base re-index, or model-version refresh back into a regression suite gating the next deploy. This is precisely the gap Phase 2's CI/CD regression gate (§6.2) is designed to close — and is a differentiator to state explicitly to the client, since it's a documented blind spot across the industry, not a gap unique to their environment.

### 2.4 Framework Crosswalk (NIST AI RMF / Treasury AI RMF)

Everything in this strategy already exists as engineering and process substance in §3–§9. This table doesn't add new controls — it relabels that same substance against the two taxonomies a bank's model-risk and compliance reviewers are most likely to grade against internally: NIST AI RMF's four functions (Govern / Map / Measure / Manage) and the Treasury Financial Services AI Risk Management Framework's risk-management components. It's usually the first page a compliance reviewer flips to.

| Our Section | NIST AI RMF Function | Treasury AI RMF Component | What It Demonstrates |
|---|---|---|---|
| §2.1 (Regulatory anchor), §8 (Governance & Ownership) | **Govern** | Governance & Risk Culture | Accountable ownership per agent, SR 11-7-aligned oversight, named RACI |
| §3 (Agent Inventory & Materiality Tiering) | **Map** | Risk Identification & Assessment | Authoritative inventory, harm-surface classification, tiered depth of scrutiny |
| §4 (Domain Risk Model) | **Map** | Risk Identification & Assessment | Named harm surfaces, control-requirement mapping, bounded-autonomy design |
| §5 (Phase 1 — Pre-Shipping Assurance) | **Measure** | Model Testing & Validation | Static + dynamic testing, golden-dataset eval, hard-gate + judge scoring, hashable evidence |
| §6 (Phase 2 — Post-Shipping Production Assurance) | **Manage** | Ongoing Monitoring & Risk Response | Staged rollout, CI/CD regression gate, drift monitoring, kill switch, periodic re-certification |
| §7 (Vendor & Third-Party Agent Pathway) | **Govern** + **Map** | Third-Party Risk Management | C032 vendor control, evidence-quality labeling for dynamic-only assessments |
| §9 (Success Metrics) | **Measure** + **Manage** | Ongoing Monitoring & Reporting | Metrics tied to a recurring governance-committee cadence, not point-in-time sign-off |

This table can be pulled forward as a standalone one-pager for a compliance-stakeholder audience without altering the underlying strategy.

---

## 3. Agent Inventory & Materiality Tiering

Before any per-agent testing happens, the institution needs an authoritative answer to: how many agents exist, who owns each, and what's each one's harm surface. Without this, testing is only ever applied to whatever agent someone happened to point at — a documented model-risk exam failure pattern (undocumented/"shadow" AI usage).

### 3.1 Required inventory fields per agent
- Owning business unit and named accountable owner
- Framework/architecture (OpenAI Agents SDK, Google ADK, LangChain, LangGraph, vendor/closed-source)
- Autonomy level: recommend-only / request-approval / auto-execute
- Harm surface: can it move money, file a regulatory report, close a case, contact a customer, mutate a system of record
- Data sources touched: customer due diligence records, watchlists, transaction monitoring, case management
- Build provenance: in-house, open-source-derived, or third-party/vendor

### 3.2 Materiality tiers (drives testing depth, not a uniform bar)

| Tier | Example | Required depth |
|---|---|---|
| **Tier 1 — Blocker-eligible** | Compliance investigation assistant, regulatory report support, case-closure/client-exit recommendation | Full pipeline: static + dynamic + golden dataset + judge scoring + Phase 2 continuous monitoring, mandatory |
| **Tier 2 — Elevated** | Alert summarizer (no recommendation authority), document extraction | Static + dynamic required; judge scoring recommended; Phase 2 sampling at reduced frequency |
| **Tier 3 — Low materiality** | Internal knowledge-base Q&A, meeting-note summarization with no case data | Static audit only, periodic re-check, no mandatory golden dataset |

Applying Tier 1 depth uniformly to Tier 3 agents is wasteful and creates a bad signal to regulators (undifferentiated over-testing reads as not actually understanding the risk gradient). Applying Tier 3 depth to Tier 1 agents is the actual exam-failure scenario.

---

## 4. Domain Risk Model

### 4.1 Harm surfaces
- Regulatory report finalization
- Alert/case closure
- Client-exit recommendation
- Unauthorized disclosure of investigation or flagged status
- Sensitive customer/account/transaction data exposure
- Watchlist and due diligence grounding accuracy
- Wrong entity/counterparty resolution
- Prompt injection via external documents, retrieved content, or tool output
- Overblocking benign analyst workflows (a real cost — an unusable agent gets bypassed, which is its own risk)
- Missing or stale source evidence

### 4.2 Required control mapping (domain regime overlay)

| Req ID | Requirement | Controls | Severity | Likelihood | Impact |
|---|---|---|---|---|---|
| DOM-001 | Never disclose investigation or flagged status to a customer or counterparty | C001, C002, C010 | Blocker | Medium | Severe |
| DOM-002 | Regulatory report finalization requires logged, explicit analyst approval (actor, timestamp, case ID, evidence hash) | C003, C005, C011 | Blocker | Medium | Severe |
| DOM-003 | Correct customer/account/counterparty entity resolution before acting or reporting | C004, C008 | High | High | High |
| DOM-004 | Retrieval restricted to approved sources; claims grounded in case-linked evidence | C007, C008 | High | High | High |
| DOM-005 | No autonomous case closure or client-exit recommendation as final action | C003, C005, C011 | Blocker | Medium | Severe |

**Reading this table:** Severity is the engineering/audit judgment already used elsewhere in this strategy (drives block/ship decisions in §5.2 and §5.7). Likelihood and Impact are a complementary risk-register view — the likelihood × impact lens a model-risk committee typically expects alongside, not instead of, engineering severity. Likelihood reflects how often the failure mode plausibly arises given typical agent architecture (e.g., entity-resolution errors and ungrounded retrieval are the most common real-world failure modes); Impact reflects the regulatory, financial, and reputational consequence if the failure reaches production unchecked. The two lenses agree on which rows matter most, which is itself evidence the tiering isn't arbitrary.

Three of five requirements are blocker-severity — this is the concrete artifact that tells a client where the regulatory teeth actually are, versus generic "safety" language.

### 4.3 Bounded autonomy as a design control, not just a test target
Following the Robinhood agentic-trading pattern of fund-limited sub-accounts, Tier 1 agents should be architected with hard-bounded action scopes (e.g., can draft a report, cannot submit it; can flag a case, cannot close it) so that even a testing gap doesn't translate directly into unauthorized action. Testing proves the boundary holds; it shouldn't be the only thing enforcing it.

### 4.4 Coverage requirement
Golden dataset case families must span the full range of scenario types relevant to the domain — each with dedicated boundary cases that probe threshold-adjacent behavior and edge conditions.

---

## 5. Phase 1 — Pre-Shipping Assurance (Implemented)

### 5.1 Static Audit
- Regex/signature-based source scanning, framework-aware (OpenAI Agents SDK, Google ADK, LangChain, LangGraph)
- Zero credentials required — runs against source alone
- Each finding: control ID (C001–C036), file/line evidence, `can_block` flag (`true`/`false`/`"unknown"`), adequacy note
- **Fail-loud**: returns `"no agent found"` / `"framework undetermined"` rather than a false pass

**Output artifact — Capability Profile:** agent name, detected framework, autonomy level, registered tools, data sources touched, and detected architecture. This is the "here is what this agent can do" record — it anchors the harm surface derivation and the required control set that follows.

### 5.2 Required-Control Derivation
Computed per agent from: harm surface, detected architecture, domain regime overlay, autonomy level. Diffed against discovered controls — the gap is the finding.

**Output artifact — Control Gap Report:** three columns per control ID: required (yes/no, with rationale), discovered (present / present-but-weak / absent / unknown), gap (none / adequacy gap / missing / unverifiable). Severity is attached per gap item — a blocker-severity missing control is a ship-blocking finding, not a recommendation. This artifact is the "here is the required set, here is what was found, here is what is missing" deliverable.

### 5.3 Golden Dataset Construction (Consent-Gated)
- Schema: `id`, `suite`, `input`, `expected`, `must_not`, `severity`, `source`, plus domain-relevant optional fields (`retrieved_doc`/`tool_result` for injection testing, `forbidden_tools`, `max_tool_calls`, `required_phrases`/`forbidden_phrases`)
- Import pipeline scores client-supplied data against a domain-specific quality profile, yielding one of four readiness states: `needs_client_input` → `structurally_valid_but_coverage_thin` → `eval_ready` → `governance_grade_candidate`
- If no dataset exists, a proposed seed is drafted — **never auto-promoted**; requires explicit client approval before becoming eval ground truth

### 5.4 Dynamic Invocation Testing
- Real invocation via HTTP, MCP, SDK object, or command wrapper
- Confirms runtime behavior, not just source-level presence — anything static-only leaves marked `"unknown"` until dynamically verified

**Output artifact — Runtime Evidence Record:** per-case result (pass/fail/error), observed output, tool calls made, whether an approval gate fired, citations returned. Upgrades `can_block: unknown` static findings to confirmed or unconfirmed at runtime. Controls that pass static audit but fail dynamic invocation are flagged as adequacy gaps, not passes.

### 5.5 DeepEval Suite Generation
- **Deterministic hard gates run first** — forbidden tool calls, skipped approvals, leakage, missing citations, budget overruns — sourced verbatim from the audit engine's assertion logic so there's no drift between audit and test
- **A hard-gate failure fails the case immediately**, before any LLM judge runs — no semantic score can override a deterministic control failure
- **Semantic layer (GEval)** runs only after hard gates pass, scored against a single-source-of-truth rubric, with domain-specific weighting (unauthorized disclosure severity, refusal quality, analyst usefulness, evidence sufficiency, entity/counterparty accuracy)
- Exporter itself never calls an LLM or the target agent — pure deterministic renderer; execution happens via a subprocess contract (`AGENT_ASSURANCE_COMMAND`)

### 5.6 Judge Handoff Pack (Governance-Restricted Path)
For institutions whose policy forbids sending case transcripts to an externally hosted judge model: a rubric + case file + result template scored by hand, using identical criteria to the live path. Recomputes pass/fail from returned scores on import rather than trusting an unattributed number, flagging missing judge-model attribution or inconsistent pass/fail as data-quality issues.

### 5.7 Output Contract
- Hashable evidence (file/line findings)
- Verdict = fix order + residual risk statement, not a single score
- Renderable to Markdown (engineering), Excel (issue triage), or DOCX (governance memo) depending on audience

**Output artifact — Residual Risk Statement:** explicitly names what remains unresolved after all Phase 1 work is complete. Four categories: (1) controls required but not found — ship-blocking until remediated; (2) controls found but adequacy is weak — present in source but prompt-only or no enforceable block path; (3) controls verified dynamically only — no static backing, runtime behavior confirmed but implementation is opaque; (4) open unknowns — `can_block: unknown` findings where neither static nor dynamic testing could confirm blocking behavior. This is the "here is what we still cannot prove" record that governance reviewers act on.

---

## 6. Phase 2 — Post-Shipping Production Assurance (Roadmap)

### 6.1 Staged Rollout
1. **Shadow mode** — agent runs in parallel, output discarded/logged only, compared against actual analyst decisions. No live impact. Modeled on Google's shadow-deployment-to-tagged-revision pattern.
2. **Canary** — small live traffic slice, mandatory human review of every agent decision in the canary window
3. **Full production** — only after canary period demonstrates agent-analyst agreement at an agreed threshold

Shadow mode is not optional overhead — it's the only way to get a production-realistic false-negative estimate before real regulatory exposure exists.

### 6.2 CI/CD Regression Gate
Any change to prompt, tool definitions, model version, or retrieval source automatically re-triggers the Phase 1 static + golden-dataset suite as a CI gate, blocking deploy on regression — not a manual re-review. This directly closes the "no CI/scheduled re-audit story" gap flagged in §2.3 as an industry-wide blind spot. For the highest-severity cases, consider layering formal/deterministic verification (in the spirit of AWS Automated Reasoning checks) on top of LLM-judge scoring for hard gates that carry direct regulatory consequence.

### 6.3 Continuous Sampling & Human QC Feedback Loop
- Statistically meaningful sample of **all** live decisions reviewed on a fixed cadence — explicitly including agent-marked "low risk" cases, since that's where false negatives hide
- Risk-weighted sampling: higher rate on low-confidence or boundary-adjacent cases, not uniform sampling (100% review defeats the purpose of the agent at institution volume)
- **Every QC overturn becomes a new golden case** — this is the single highest-value feedback loop in the strategy; overturned production decisions are stronger ground truth than anything authored synthetically, and it compounds dataset quality over time

### 6.4 Drift Monitoring
- Recommendation rate trend — a sudden drop signals possible silent regression; a sudden spike may signal an early-caught pattern shift; both require investigation
- Analyst override rate — should be low and stable; a rising trend signals eroding trust or an underlying change
- **Unauthorized disclosure incidents — must be zero, always.** Any single occurrence is an automatic circuit-breaker event, not a trend metric
- Approval-gate integrity telemetry — confirms every report filing/case closure actually passed a logged human approval in practice, not just that the code path exists

### 6.5 Kill Switch / Circuit Breaker
Any production trace showing a forbidden action actually executed (autonomous report filing, unauthorized customer contact, case closure without approval) triggers automatic rollback — not a finding queued for next quarter's review. Same deterministic hard-gate assertions from Phase 1 (§5.5), applied to production traces instead of golden cases.

### 6.6 Periodic Re-Certification
Full re-audit on a fixed cadence (semi-annual is typical for high-risk models under SR 11-7-style governance) independent of any code change — because pattern drift alone, with zero code changes, can silently degrade real-world detection performance. Backtest against a refreshed golden set incorporating new intelligence, not the original seed set alone.

### 6.7 Evidence Retention & Exam Readiness
Every artifact above — CI gate results, QC overturn logs, drift metric history, re-certification results — retained and versioned so the institution can answer "prove this was under control on a specific date" on regulator request. This is the layer that turns a testing program into an examinable governance program.

---

## 7. Vendor & Third-Party Agent Pathway

Vendor and third-party agents route through the same assurance pipeline with two structural differences: static audit is skipped (no source access), and C032 (Third-Party And Vendor Model Risk) becomes a required control in the derived set.

### 7.1 What changes in the audit pipeline

**Static audit does not run.** Every control (C001–C036) begins as `can_block: unknown` rather than present or absent. This is an explicit output state, not a silent gap — the verdict labels it `dynamic_only_evidence` and the residual risk statement reflects the missing static coverage. A `dynamic_only` result is never treated as equivalent to a combined static+dynamic result.

**Dynamic testing runs via the available invocation path.** The same golden dataset and the same hard-gate assertions apply — the difference is the adapter:
- HTTP endpoint → `runner_adapters/http_agent_adapter.py`
- MCP server → `runner_adapters/mcp_stdio_adapter.py`
- Neither available → transcript-only mode (historical result JSONL or provided transcripts), which supports initial calibration but does not constitute runtime assurance until the same cases run through a live invocation path

If no invocation path can be arranged, the assessment verdict is `incomplete` — not a pass, not a conditional pass.

### 7.2 C032 as a required control

C032 (Third-Party And Vendor Model Risk) is added to the derived control set for every vendor agent. Adequate evidence requires:
- An entry in the agent inventory (§3.1) identifying the vendor, version, and named internal owner
- A vendor risk assessment or equivalent security review on file
- Contract or onboarding terms that include the right to run the dynamic eval suite against the agent's invocation endpoint — this is a prerequisite for the assessment, not a post-finding recommendation
- Documented SLA and failure-handling behavior relevant to the agent's harm surface

### 7.3 Evidence quality labeling

The final verdict explicitly states the evidence basis. A vendor agent assessed via dynamic-only path carries a `lower_confidence` flag on every control finding that would normally require static verification. Governance reviewers see this in the output — it is never collapsed into the same confidence tier as an in-house agent with full source access.

---

## 8. Governance & Ownership

| Role | Responsibility |
|---|---|
| Model Risk / Governance Committee | Owns materiality tiering policy, reviews re-certification results, approves golden dataset promotions for Tier 1 agents |
| Compliance Lead | Owns domain regime overlay content (scenario coverage, regulatory thresholds), reviews requirement mapping |
| Engineering / Agent Owner | Owns static/dynamic audit remediation, CI gate maintenance, kill-switch response |
| QC Review Team | Owns continuous sampling review, overturn logging, golden dataset feedback submission |
| Independent Validation (2nd/3rd line) | Owns periodic re-certification, evidence retention audit-readiness |

---

## 9. Success Metrics

- % of agent inventory with complete tiering and control-derivation coverage
- Blocker-severity control pass rate at pre-ship gate (target: 100% before Tier 1 ship)
- Time from domain intelligence update to golden dataset refresh
- QC overturn rate trend (declining over time indicates the compounding feedback loop is working)
- Unauthorized disclosure incidents in production (target: zero, always)
- Mean time from CI regression detection to deploy block (target: automatic, sub-minute)
- Evidence retrieval time for a regulator request (target: same-day, from retained artifacts)

---

## 10. Open Questions / Risks to Resolve With Client

1. What's the institution's current agent inventory maturity — does an authoritative registry exist, or does this program need to build one first?
2. What's the acceptable canary-period agreement threshold between agent and analyst decisions before promoting to full production?
3. Does compliance policy permit external LLM-judge scoring, or does every Tier 1 agent require the judge handoff (human-scored) path?
4. What's the re-certification cadence the institution's model risk committee will actually commit to — semi-annual, quarterly?
5. How is the vendor/closed-source agent population currently tracked, if at all?

---

## Appendix: Worked Reference

See companion document **`02_worked_example.md`** for the full concrete walkthrough of one Tier 1 case through the entire Phase 1 pipeline — golden case JSON, static findings, judge rubric overlay, generated test logic, and final report output. See **`01_technical_appendix.md`** for the underlying mechanics of static/dynamic detection, dataset schema, and DeepEval generation referenced throughout §5.
