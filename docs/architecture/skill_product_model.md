# Skill Product Model

This repository uses one installable orchestrator skill today:

```text
agent-control-audit
```

That is intentional. The current product is an end-to-end assurance workflow: intake, observation, static audit, gap matrix, golden dataset readiness, DeepEval generation, dynamic invocation, remediation planning, and reporting. Those stages share one control vocabulary, one output folder contract, one evidence model, and one user journey.

Splitting every stage into its own top-level skill would look modular, but it would create routing risk and inconsistent evidence. Codex or ChatGPT selects skills from their top-level metadata. It does not guarantee that `intake`, `observe`, `static-audit`, `dataset`, `evals`, and `report` skills will be loaded in the right order with the same assumptions.

## Current Structure

Keep the active product as:

```text
agent-control-audit/
├── SKILL.md
├── adapters/
├── detection/
├── engine/
├── evals/
├── output/
├── regimes/
├── remediation/
├── runner_adapters/
├── scripts/
└── strategy/
```

Use internal stage files, references, scripts, and adapters to keep the skill maintainable. The stage logic can be cleanly separated inside the package, while the user still invokes one stable assurance capability.

Recommended internal stage model:

```text
agent-control-audit/
├── SKILL.md
├── stages/
│   ├── intake.md
│   ├── observe.md
│   ├── static_audit.md
│   ├── gap_matrix.md
│   ├── dataset_readiness.md
│   ├── deepeval_generation.md
│   ├── dynamic_invocation.md
│   ├── remediation_plan.md
│   └── report.md
└── scripts/
```

This is a future cleanup path, not a requirement to demo the product. Today, equivalent guidance already lives in `strategy/`, `evals/`, `engine/`, `runner_adapters/`, `output/`, and `scripts/`.

## Why Not One Skill Per Stage

Avoid this as the default:

```text
agent-control-audit-intake/
agent-control-audit-observe/
agent-control-audit-static-audit/
agent-control-audit-dataset/
agent-control-audit-evals/
agent-control-audit-report/
```

Reasons:

- The user does not think in stage packages; they think "audit this agent and tell me what is missing."
- Each stage depends on the same domain assumptions, control catalog, quality profile, and run manifest.
- Multiple top-level skills can drift in terminology, severity rules, dataset schema, and report language.
- Skill routing would become fragile because the model must choose the right stage skill at the right time.
- Packaging would become harder: each skill would need its own `SKILL.md`, metadata, references, scripts, tests, and versioning.

Use one orchestrator skill until a sub-capability proves it has an independent audience outside agent assurance.

## Future Sibling Skills

The following should be documented as future sibling skills or plugin capabilities, not immediate replacements for `agent-control-audit`.

| Future Skill | Purpose | When It Becomes Its Own Skill | Relationship To `agent-control-audit` |
|---|---|---|---|
| `golden-dataset-normalizer` | Normalize JSONL, JSON, CSV, or XLSX datasets into governed eval-case JSONL and readiness reports. | When teams want dataset readiness checks for any AI system, not only agents. | `agent-control-audit` can call or embed its scripts for golden dataset intake. |
| `deepeval-suite-builder` | Generate DeepEval-first pytest suites from approved normalized datasets with deterministic gates and documented text-fallback limitations. | When teams want reusable DeepEval generation for RAG apps, copilots, classifiers, and agents. | `agent-control-audit` uses it after dataset approval. |
| `domain-pack-author` | Help domain/business/MDM/MRM teams create domain extension packs and quality profiles. | When many teams need to author reusable domain packs without editing the audit skill. | Produces `domain_extensions/<domain>/` packs consumed by `agent-control-audit`. |
| `agent-control-audit` | Main end-to-end assurance workflow for already-built agents. | Already active. | Orchestrates the full journey and owns final evidence/report semantics. |

The first three are reusable products. They are worth splitting only when they can be used directly in another workflow without running a full agent audit.

## Plugin Direction

A plugin can package several sibling skills together:

```text
agent-assurance-plugin/
├── agent-control-audit/
├── golden-dataset-normalizer/
├── deepeval-suite-builder/
└── domain-pack-author/
```

That plugin model is attractive when the product matures because it gives users a coherent toolkit:

- Use `agent-control-audit` for the complete assurance run.
- Use `golden-dataset-normalizer` when the immediate problem is bad client datasets.
- Use `deepeval-suite-builder` when the dataset is ready and the team only needs tests.
- Use `domain-pack-author` when governance or business teams need to define reusable domain expectations.

Until then, keep the current repo simple: one installable skill plus external docs, examples, tests, domain extensions, and outputs.

## Graduation Criteria

Create a sibling skill only when at least three of these are true:

- It solves a user request that does not require a full agent audit.
- Its inputs and outputs are stable enough to document independently.
- It has scripts or templates that are reused across more than one workflow.
- It has its own likely user persona, such as data governance, model validation, or domain SMEs.
- It can be tested with fixtures that do not need the full `agent-control-audit` context.
- It has enough surface area that keeping it inside the orchestrator skill makes `SKILL.md` or the package confusing.

## Decision

For now:

- Keep `agent-control-audit` as the main installable skill.
- Keep stage logic inside that skill using references, scripts, adapters, and optional future `stages/` files.
- Keep `domain_extensions/`, `examples/`, `tests/`, and `docs/` outside the skill zip.
- Document `golden-dataset-normalizer`, `deepeval-suite-builder`, and `domain-pack-author` as the next productized sibling skills.
