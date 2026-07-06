# Golden Dataset Quality Review

Use this before generating DeepEval tests or claiming eval coverage.

Golden data is not automatically good because a client supplied it. Treat it as governed evidence that must be checked for usability, traceability, and machine-checkability.

## Skill Concept

The skill should help the client answer:

- Is this dataset structurally usable?
- Is each case precise enough to grade?
- Does it cover the risks the agent actually has?
- Does it include benign false positives as well as adversarial cases?
- Is it owned, versioned, reviewed, and safe to run?
- What exact information does the client need to add before this becomes eval evidence?

The LLM should do the reasoning and critique. Python should do deterministic mechanics: parsing, schema validation, duplicate detection, profile-based quality scoring, report generation, hashing, format conversion, and DeepEval file generation.

Quality expectations are configurable. Use `evals/quality_profiles.json` for built-in profiles such as `default`, `financial`, `financial_aml`, `financial_payments`, and `financial_lending`. A client or domain owner can supply a custom profile file when their domain has different suites, metadata expectations, weights, or readiness thresholds.

## Quality Dimensions

Review datasets across these dimensions:

- `schema_validity`: required fields are present and parseable.
- `machine_checkability`: cases contain observable assertions such as forbidden tools, required phrases, citations, max tool calls, or precise `must_not` outcomes.
- `high_risk_machine_checkability`: every blocker/high case has deterministic assertions.
- `risk_coverage`: suites cover the agent's required control set, not only generic prompts.
- `benign_balance`: benign/allowed cases exist so guardrails are tested for overblocking.
- `domain_specificity`: cases reflect the actual business line, tools, data, and decisions.
- `traceability`: owner, reviewer/approver, source, version, and reviewed date are captured.
- `secret_safety`: cases use synthetic or redacted identifiers and no production secrets.
- `runner_readiness`: cases contain enough context for HTTP, MCP, SDK, or command invocation.

## Configurable Quality Profiles

Each profile may define:

- `recommended_suites`: suites expected for that domain or sub-business line.
- `owner_metadata_keys`: metadata keys that count as ownership traceability.
- `version_metadata_keys`: metadata keys that count as version/review traceability.
- `score_weights`: weights for quality dimensions.
- `readiness_thresholds`: thresholds for `eval_ready` and `governance_grade_candidate`.

User-facing prompt:

```text
Use agent-control-audit to review this dataset with the financial_aml quality profile: /path/to/client_cases.xlsx.
```

Codex should run the deterministic importer internally and explain the readiness result. If a custom profile is needed, ask for the profile name and profile JSON file path in plain language.

Implementation detail: `scripts/dataset_import.py` accepts `--quality-profile` and `--quality-profile-file`, but users should not need to know those flags unless they ask how the skill works.

## Readiness Levels

- `needs_client_input`: required fields or high-risk assertions are missing. Do not generate DeepEval tests.
- `structurally_valid_but_coverage_thin`: rows parse, but coverage or governance quality is too weak for serious claims.
- `eval_ready`: good enough to run against the agent and produce meaningful pass/fail results.
- `governance_grade_candidate`: broad risk coverage, deterministic assertions, owner/version metadata, benign coverage, and traceability are present. Human governance approval may still be needed.

The validation report should expose `deepeval_generation_allowed=true` only for `eval_ready` or `governance_grade_candidate`. A structurally valid but thin dataset may still be normalized for inspection, but it should not be treated as assurance evidence.

## Required Client Questions

When quality is weak, ask concrete questions instead of giving a generic complaint:

- Which tool call must never happen in this case?
- Should the expected behavior be `block`, `request_approval`, `answer_with_citations`, `safe_fallback`, or `allow`?
- What exact phrase, citation, reason code, or structured field must appear?
- What exact outcome is forbidden?
- Which suite/risk does this row test?
- Who owns or approved this case?
- What version/date should be attached to this dataset?
- Is this identifier synthetic or redacted?

## DeepEval Generation Rule

Generate DeepEval files only after the dataset is at least structurally valid. For high-risk financial cases, prefer `eval_ready` or better.

Ask the user whether they want a DeepEval suite generated after the dataset is at least structurally valid. Codex should run `scripts/deepeval_export.py` internally. That script does not call an LLM and does not run the target agent. It only renders a deterministic pytest file from normalized cases. The generated file invokes the real agent later through `AGENT_ASSURANCE_COMMAND`; optional DeepEval LLM-as-judge scoring happens only when that generated test is run with judge mode enabled.

## What Not To Do

- Do not use an LLM to invent missing expected behavior or forbidden outcomes.
- Do not treat client prose notes as machine-checkable assertions.
- Do not generate release evidence from transcript-only data.
- Do not include API keys, production account numbers, private keys, raw customer identifiers, or secrets.
- Do not claim coverage for suites that are absent from the dataset.
