---
name: agent-control-audit
description: Agent assurance skill for already-built agent repositories. Use when Codex needs to audit an agent for guardrails, evals, and control coverage, especially financial-regime agents, by detecting the framework, discovering present controls, deriving required controls from harm surface/regime/autonomy/architecture/NFRs, ingesting user/team-supplied golden datasets, proposing seed datasets when none exist, invoking the target agent through HTTP/MCP/SDK-command adapters, generating DeepEval-first eval suites with deterministic hard assertions, and emitting a verdict plus hashable evidence. Covers financial safety, jailbreak and prompt-injection resistance, toxicity/content safety, operational NFR guardrails, and eval regression evidence. Supports OpenAI Agents SDK, Google ADK, LangGraph, and LangChain static first-pass discovery.
---

# Agent Control Audit

## Audit Workflow

Run the audit as static discovery plus DeepEval-first golden-data execution. The loop is: discover, derive controls, ingest or propose golden cases, invoke the agent, generate/run DeepEval suite with hard assertions, report evidence. At intake, establish a structured output folder for all generated artifacts; if the user does not specify one, use a clear timestamped run folder such as `outputs/<target-slug>/<YYYY-MM-DD-HHMM>/` and initialize it with `scripts/init_output.py`. Capture domain, business, data/MDM, and governance assumptions under `00_intake/`; mark unknowns explicitly instead of inventing them.

1. Read `strategy/end_to_end_assurance.md` when the user asks for an end-to-end guardrails/evals plan or a finished assurance product.
2. Read `strategy/help_info.md` before answering help/info/"what does this do" requests. Do not answer those from memory. Do not show raw helper-script commands unless the user explicitly asks for implementation details; if commands are requested, use only real script arguments and existing dataset names.
3. For static audit requests, ask for the target repo path or URL, initialize the output folder with `scripts/init_output.py`, then run `scripts/static_audit.py` internally when shell execution is available. Write static artifacts under `02_static_audit/` unless the user asks for specific destinations. Use the script for framework gating, obvious control discovery, required-control derivation, and hashable finding scaffolding.
4. Read `detection/router.md` and the matching adapter doc: `adapters/openai_agents_sdk.md`, `adapters/google_adk.md`, `adapters/langgraph.md`, or `adapters/langchain.md`.
5. Read `engine/control_catalog.md`, `regimes/financial.md`, `engine/mapping.md`, `engine/severity.md`, and `engine/eval_framework.md`.
6. Derive the required control set from `{harm surface, regime, autonomy, architecture}` independently of what the agent already implements.
7. Compare required controls to discovered controls. Label each finding as `missing`, `weak`, `misconfigured`, `present`, `out_of_scope`, or `not_checked`.
8. Judge adequacy for present controls; do not give credit for names, comments, or prompts that cannot block, constrain, verify, or record the relevant behavior.
9. For golden datasets, first ask whether the user already has one. If supplied, read `evals/client_dataset_intake.md` and `evals/golden_dataset_quality.md`, then normalize it with `scripts/dataset_import.py`. Accept JSONL, JSON, CSV, or XLSX. Treat `--in`, `--out`, and `--report` as Codex-internal script parameters; do not make the user understand those flags. Ask the user only for the dataset path/file, domain or quality profile when known, and whether they want the generated normalized dataset/report saved somewhere specific. Put supplied inputs under `05_dataset/supplied/` when copied, readiness outputs under `05_dataset/readiness/`, and normalized JSONL under `05_dataset/normalized/`. If no dataset exists, offer to draft a synthetic proposed seed dataset from the observed harm surfaces, domain profile, and missing controls. Save the proposal under `05_dataset/proposed/`, label it `proposed` rather than `golden`, explain what each case is meant to prove, and ask for explicit user approval before using it for DeepEval generation or runtime evaluation. If the user does not approve the proposed dataset, stop at recommendations for how to create one. If the importer reports `needs_client_input`, ask the user for the missing fields or machine-checkable assertions; do not use incomplete rows to generate DeepEval tests. If the dataset is structurally valid but quality is thin, explain the quality gaps before treating it as eval evidence.
10. Select the invocation adapter from `runner_adapters/`: HTTP, MCP stdio, SDK/framework adapter, or project-owned command wrapper.
11. For DeepEval generation requests, run `scripts/deepeval_export.py` internally by default for user-facing evals. Only generate from a supplied or explicitly approved dataset. Write the generated pytest file under `06_evals/deepeval/` unless the user asks otherwise. Tell the user where it is and what it contains. The generated suite must run deterministic hard assertions before any DeepEval LLM-as-judge metric.
12. Use `scripts/eval_runner.py` internally for local smoke tests, transcript grading, and as the reference implementation for hard-gate assertions. Do not present it as the primary user-facing framework when DeepEval is expected.
13. Read `evals/eval_framework_adapter_pattern.md` before adding support for another eval framework such as Ragas, LangSmith, Promptfoo, Inspect AI, garak, or Phoenix.
14. Read `regimes/domain_extension.md` when the user asks to add domains, sub-business lines, quality profiles, domain knowledge, MDM/data expectations, or collaborator extension patterns.
15. Before rendering a final report, read `output/report_template.md`. Use `scripts/render_report.py` internally for Markdown, XLSX, or DOCX output. Write final reports under `07_reports/` unless the user asks otherwise. If report format is unspecified, ask whether the user wants Markdown, Excel, DOCX, or all; default to Markdown plus Excel when the user says "whatever is best".
16. After any meaningful run, use `scripts/render_stage_artifacts.py` to render human-readable Markdown for every stage that has evidence: intake, observation, static audit summary, gap matrix, change plan, dataset readiness, eval summary, remediation notes, and evidence summary. JSON and JSONL are evidence, not the primary user-facing output.
17. If the user asks to fix or enable controls, read the matching remediation guide. For Google ADK, read `remediation/google_adk.md`. For OpenAI Agents SDK, read `remediation/openai_agents_sdk.md`. For LangGraph or LangChain, provide framework-specific guidance from the adapter docs and runner adapters.
18. Emit a verdict using `output/verdict_schema.md` and one hashable evidence file using `output/evidence_schema.md`.

## Fail-Loud Gates

- Stop with "no agent found" when the repository has no detectable agent entrypoint or framework signals.
- Stop with "framework undetermined" when framework signals are absent or ambiguous.
- For Google ADK, LangGraph, and LangChain, state that the static pass uses framework-aware source discovery, but runtime callback order, hosted configuration, and deployed enforcement still require dynamic proof.
- Stop if `regimes/financial.md` is missing, empty, or marked as not author-approved. Do not invent regulatory requirements.
- For static uncertainty, report the uncertainty as coverage or confidence. Never silently pass a control that may live outside the repository.

## Static Boundary

This skill recommends and verifies controls visible in source. It is not a runtime guardrail. Always state that externally enforced controls, deployed gateway policies, human operating procedures, infrastructure IAM, and production telemetry are blind spots unless they are represented in the audited repository.

## Framework Freshness

When the user asks for latest/current framework behavior, or when an adapter claim is material to a user/team deliverable, check the official links in the matching adapter doc before answering. Prefer official framework docs over memory, blog posts, or stale repo examples. If live browsing is unavailable, state the adapter doc's last-known source links and avoid claiming that API details are current.

## Secret Handling

- Static audit must run without API keys.
- Dynamic evals may require provider keys or target-app credentials. The user must configure them locally through environment variables, `.env`, or the target repo's approved secret mechanism.
- Never write API keys or secrets into normalized datasets, generated DeepEval suites, reports, source edits, logs, or chat responses.
- If required keys are unavailable, generate the static report and mark dynamic assurance as pending.

## Required Resources

- `detection/router.md`: framework detection, routing, and the discovery contract.
- `strategy/end_to_end_assurance.md`: product workflow, AML scenario, dataset flow, framework strategy, and DeepEval policy.
- `strategy/help_info.md`: help/info response guidance.
- `scripts/static_audit.py`: deterministic first-pass scanner and JSON/JSONL evidence generator.
- `scripts/init_output.py`: deterministic run-folder initializer that creates stage folders, `_run_manifest.json`, and `ARTIFACT_INDEX.md`.
- `scripts/eval_runner.py`: deterministic dataset validator, smoke runner, transcript grader, and hard-gate reference implementation.
- `scripts/dataset_import.py`: validates, quality-scores, and normalizes user/team-supplied JSONL, JSON, CSV, or XLSX golden datasets into the skill schema and reports missing input.
- `scripts/deepeval_export.py`: deterministic generator from normalized datasets to a DeepEval pytest suite with hard assertions; it does not invoke an LLM or run the target agent.
- `scripts/render_report.py`: deterministic report renderer for Markdown, Excel/XLSX, and DOCX.
- `scripts/render_stage_artifacts.py`: deterministic stage-artifact renderer that turns JSON/JSONL evidence into human-readable Markdown and Excel review surfaces across the run folder.
- `adapters/openai_agents_sdk.md`: implemented static discovery for OpenAI Agents SDK controls.
- `adapters/google_adk.md`, `adapters/langgraph.md`, and `adapters/langchain.md`: framework-aware static discovery guidance and runtime proof notes.
- `engine/control_catalog.md`: control universe and adequacy criteria.
- `engine/mapping.md`: ranked required-control derivation logic.
- `engine/severity.md`: status and severity rules.
- `engine/eval_framework.md`: red-team, NFR, and regression-eval requirements.
- `evals/dataset_schema.md`, `evals/client_dataset_intake.md`, `evals/golden_dataset_quality.md`, `evals/quality_profiles.json`, `evals/eval_framework_adapter_pattern.md`, and `evals/datasets/*.jsonl`: schema, client intake guidance, configurable golden dataset quality profiles, eval framework adapter pattern, and starter golden datasets for live evals.
- `regimes/domain_extension.md`: how to add new domains and financial sub-business-line overlays without changing the core engine.
- `runner_adapters/*.py`: live eval adapters for HTTP, MCP stdio, OpenAI Agents SDK, LangChain, LangGraph, Google ADK 1.x, and Google ADK 2.0/workflows.
- `remediation/google_adk.md` and `remediation/openai_agents_sdk.md`: how to enable missing Google ADK and OpenAI Agents SDK controls.
- `regimes/financial.md`: author-supplied financial control requirements consumed by the mapper.
- `output/verdict_schema.md`, `output/evidence_schema.md`, and `output/report_template.md`: required report and evidence shapes.
