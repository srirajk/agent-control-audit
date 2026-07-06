# Agent Control Audit

Agent Control Audit is a Codex skill for answering one hard question:

> Given an agent someone already built, what guardrails, evals, governance evidence, and operational controls are missing before anyone should trust it?

It is designed for high-risk agent systems, starting with financial services and AML-style workflows, but the architecture is domain-extensible. The core idea is simple: do not ask an LLM to vaguely "review safety." Instead, derive the required control set from the agent's harm surface, autonomy, architecture, domain, and non-functional risk, then compare that required set against source-visible evidence and live eval results.

## Why This Matters

Most agent demos show a happy path. Real governance teams ask different questions:

- Can this agent move money, close cases, file reports, notify customers, or influence eligibility?
- Can prompt injection, retrieved content, tool output, or a specialist handoff bypass policy?
- Are toxic, abusive, or brand-damaging interactions handled safely?
- Are rate limits, timeouts, fallback behavior, observability, and incident response real?
- Are there golden datasets, eval thresholds, and release gates?
- Is there model inventory, intended use, validation, data lineage, monitoring, fairness, explainability, retention, rollback, and governance reporting?

Agent Control Audit turns those questions into a repeatable workflow and evidence bundle.

## Repository Layout

- `agent-control-audit/`: the installable Codex skill package. Keep this lean and focused on skill instructions, deterministic scripts, adapters, eval seeds, and report templates.
- `domain_extensions/`: optional domain/sub-business-line extension packs. Use this for business, data/MDM, governance, quality-profile, and golden-case expectations that should guide a run without being packaged into the skill zip.
- `examples/`: runnable demo agents and mock targets. These prove the story but should not be bundled into the skill zip.
- `tests/`: development-only scanner fixtures and self-tests. These prove the skill but should not be bundled into the skill zip.
- `docs/testing/`: local smoke tests, ADK proof path, runner-adapter guide, and dynamic validation notes.
- `docs/architecture/`: skill/product architecture decisions, including when to keep capabilities inside the orchestrator skill versus promoting them to sibling skills.
- `docs/research/`: researched external repositories and supporting analysis.
- `external_repos/`: optional local clones for validation. This folder is ignored by git so downloaded repos and their secrets do not get packaged accidentally.

See `docs/testing/packaging_boundary.md` for the exact include/exclude rule when creating the skill zip.
See `docs/user_guide.md` for the client-facing assurance journey, stage outcomes, and artifact expectations.
See `docs/architecture/skill_product_model.md` for the current one-skill orchestrator model and the planned sibling skills: `golden-dataset-normalizer`, `deepeval-suite-builder`, and `domain-pack-author`.
See `AGENT_CONTROL_AUDIT_RUNBOOK.md` for the hands-on runbook to test the skill against reference or client-style agents.

## What It Does

The skill performs an end-to-end assurance loop:

1. Detects the agent framework and architecture.
2. Infers harm surfaces such as money movement, customer financial data, RAG, regulated communication, tool use, and multi-agent delegation.
3. Derives required controls independently of what the repo already has.
4. Discovers source-visible guardrails, evals, NFR controls, and governance evidence.
5. Produces missing/weak/misconfigured findings with file-line evidence and hashable records.
6. Reviews whether client golden datasets are actually usable, machine-checkable, owned, versioned, and risk-covering.
7. Normalizes acceptable client datasets from JSONL, JSON, CSV, or XLSX.
8. Generates DeepEval-first test suites with deterministic gates for observable fields, plus explicit fallback notes where text matching is used.
9. Invokes the real agent through HTTP, MCP stdio, SDK/framework adapters, or a project-owned command wrapper.
10. Renders Markdown, Excel, or DOCX reports from a fixed template.

Static audit does not require API keys. Dynamic evals use the target agent's normal local credentials through environment variables or an approved `.env` file.

## What Makes It Different

This is not just a prompt checklist.

- **Required controls are derived before discovery.** The scanner cannot hide missing controls just because it did not find them.
- **DeepEval is the client-facing eval framework by default.** The generated suite includes deterministic gates for structured facts such as blocked status, approval requests, tool calls, citations, and max tool calls. Text checks are treated as fallback heuristics and should be paired with DeepEval/LLM-as-judge or structured result fields for semantic claims.
- **Golden datasets are treated as governed assets.** Client files can arrive as JSONL, JSON, CSV, or Excel, but the skill first checks whether they are complete, machine-checkable, traceable, and risk-covering enough to deserve the word "golden."
- **Dataset quality is domain-configurable.** AML, payments, lending, healthcare, insurance, and other domains can define their own expected suites, metadata keys, scoring weights, and readiness thresholds.
- **Python is used for deterministic mechanics.** The skill uses scripts for parsing, validation, scoring, hashing, DeepEval file generation, and report rendering so the LLM does not waste tokens reformatting Excel, JSONL, or DOCX by hand.
- **NFRs are first-class controls.** Cost, rate limits, retries, fallbacks, observability, incident hooks, retention, rollback, and continuity are not afterthoughts.
- **Model governance is included.** Inventory, ownership, intended use, validation, data lineage, monitoring, benchmarking, fairness, explainability, change approval, vendor risk, access segregation, legal hold, decommissioning, and governance reporting are explicit controls.
- **It supports real invocation.** The runner contract can wrap HTTP endpoints, MCP tools, OpenAI Agents SDK, LangChain, LangGraph, Google ADK, or a client-owned command.

## Current Framework Coverage

Static first-pass discovery supports:

- OpenAI Agents SDK
- Google ADK
- LangChain
- LangGraph

For OpenAI Agents SDK, the scanner detects native guardrails, tools, approvals, handoffs, retrieval, eval signals, and governance artifacts. For Google ADK, LangChain, and LangGraph, it performs generic source-control discovery and then requires reviewer judgment for framework-specific runtime semantics.

## Financial Control Surface

The first domain pack is financial services because it stresses the hard parts:

- AML and financial-crime investigation
- Sanctions and adverse media
- Payments, refunds, ACH, wires, and merchant operations
- Lending, credit, eligibility, and adverse action
- Wealth, investment research, and portfolio assistance
- Capital markets, trading support, and research workflows
- Treasury, finance operations, reconciliations, and reporting
- Customer support over regulated financial products

The financial regime currently covers:

- Financial side effects
- Financial recommendations and regulated output
- Customer financial data
- Retrieval-grounded financial answers
- Multi-agent delegation
- Reproducible audit claims
- Jailbreak and prompt-injection resistance
- Toxicity and abuse safety
- Operational NFR guardrails
- Eval regression gates
- Model inventory, intended use, validation, data governance, monitoring, benchmarking, fairness, explainability, change management, vendor risk, access control, retention, continuity, and governance reporting

## How To Run The Local Smoke Test

From this workspace:

```bash
python3 -B tests/self_test.py
```

Run the unsafe fixture:

```bash
python3 -B agent-control-audit/scripts/static_audit.py \
  tests/fixtures/financial_agent \
  --out /tmp/agent_audit.json \
  --jsonl /tmp/agent_findings.jsonl
```

Run the guarded fixture:

```bash
python3 -B agent-control-audit/scripts/static_audit.py \
  tests/fixtures/financial_agent_guarded \
  --out /tmp/guarded_audit.json
```

Expected result:

- Unsafe fixture: `decision=block`
- Guarded fixture: `decision=ship`

## Client Golden Dataset Flow

Clients can supply test cases as JSONL, JSON, CSV, or XLSX. The skill does not assume the dataset is good. It first reviews whether the cases are complete, machine-checkable, traceable, and aligned to the risks of the agent.

User prompt:

```text
Use agent-control-audit to review this golden dataset for AML readiness: /path/to/client_cases.xlsx.
Tell me if it is good enough for DeepEval and what the client needs to fix.
```

Codex runs the deterministic importer internally. The user does not need to know `--in`, `--out`, or `--report`.

The report includes:

- required-field issues
- duplicate IDs
- high-risk cases missing deterministic assertions
- suite, severity, and expected-behavior distributions
- dataset readiness: `needs_client_input`, `structurally_valid_but_coverage_thin`, `eval_ready`, or `governance_grade_candidate`
- concrete improvement actions and client questions

If required fields are missing, do not guess. Ask the client for the missing expected behavior, forbidden outcome, severity, owner, version, or machine-checkable assertion.

Built-in quality profiles include `default`, `financial`, `financial_aml`, `financial_payments`, and `financial_lending`. A domain team can supply a custom profile JSON file when its eval suites or governance metadata differ.

Implementation terms:

- `input`: the client dataset file.
- `normalized_out`: the cleaned canonical JSONL artifact Codex can use for eval generation.
- `report`: the dataset quality/readiness artifact Codex uses to explain gaps and ask client questions.

## DeepEval Flow

Generate the DeepEval suite after the dataset is structurally valid:

```text
Generate a DeepEval suite from the normalized dataset.
```

Codex runs the deterministic exporter internally. It does not invoke an LLM and does not run the target agent. It only renders a pytest/DeepEval file from normalized cases.

To run live evals, the user can say:

```text
Run the DeepEval suite against this agent using the HTTP adapter.
```

Codex can run it when the target repo, invocation path, dependencies, and local API keys are available. Otherwise it generates the suite and marks live execution pending.

The deterministic runner remains the source of truth for hard controls such as forbidden tool calls, missing approval, sensitive-data leakage, missing citations, budget overruns, and timeout/fallback behavior.

Optional LLM-as-judge scoring happens only when the generated DeepEval test is run with judge mode enabled. It is never the only grader for hard financial controls.

## Report Output

Render reports as Markdown, Excel, or DOCX:

```text
Generate the assurance report as Markdown and Excel.
```

Codex uses the renderer internally and tells the user where the generated files are.

Use Excel when the audience wants issue triage and ownership. Use DOCX when the audience wants a governance memo. Use Markdown for engineering handoff and repeatable review.

## Domain Extension Model

The skill is built so contributors can add more domains without rewriting the engine.

A domain pack should define:

- Harm surfaces
- Required controls
- Severity floors
- Domain-specific eval suites
- Dataset quality profile
- Golden dataset examples
- Evidence expectations
- Accepted exclusions
- Report language for that domain

Examples:

- `financial`: AML, payments, lending, investments, treasury, customer support
- `healthcare`: clinical advice boundaries, PHI, escalation, medical safety, HIPAA-oriented evidence
- `insurance`: underwriting, claims, fraud, customer communication, adverse decisions
- `legal`: legal advice boundaries, privilege, citation, jurisdiction, confidentiality
- `enterprise-it`: change control, privileged operations, ticketing, incident response, access governance
- `cybersecurity`: tool abuse, exploit generation, secrets, containment, SOC workflows

The core engine should stay stable. Domains should plug into it through regime files, dataset packs, mapping overlays, and report templates.

## What Is Already Strong

As a critic, this is already strong because it has a real spine:

- Static scanner
- Required-control derivation
- Control catalog
- Financial regime
- DeepEval export
- Dataset normalization
- Runner contract
- Report renderer
- Guarded and unsafe fixtures
- Model governance and NFR controls

That is much more than a checklist.

## What Still Makes It Prototype, Not Final Product

The next leap is validation against real external agents:

- Clone real financial-agent repositories.
- Run static audit against each.
- Build one live invocation adapter per target.
- Run a client-like golden dataset through DeepEval.
- Compare the generated findings against human expert review.
- Add missing framework-specific detectors where the static scanner is too generic.

The product becomes "gold" when it repeatedly finds the same gaps a serious model-risk, security, compliance, and platform team would find.

## North Star

The goal is not to say "this agent is safe."

The goal is to say:

> Here is what this agent can do. Here is what can go wrong. Here is the required control set. Here is the evidence we found. Here is what is missing. Here are the evals that prove the controls work. Here is the residual risk.

That is the language governance teams understand, and it is the difference between an impressive demo and a trusted assurance workflow.
