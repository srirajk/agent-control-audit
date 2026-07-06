# Skill Packaging Boundary

Use this repository layout when creating a Codex/ChatGPT skill zip.

## Include In The Skill Zip

- `agent-control-audit/SKILL.md`
- `agent-control-audit/agents/`
- `agent-control-audit/adapters/`
- `agent-control-audit/detection/`
- `agent-control-audit/engine/`
- `agent-control-audit/evals/`
- `agent-control-audit/output/`
- `agent-control-audit/regimes/`
- `agent-control-audit/remediation/`
- `agent-control-audit/runner_adapters/`
- `agent-control-audit/scripts/`
- `agent-control-audit/strategy/`

These files directly help Codex perform the audit: they provide trigger instructions, framework routing, control derivation, domain rules, dataset normalization, DeepEval generation, live invocation adapters, report templates, and remediation guidance.

## Product Boundary

`agent-control-audit` is currently the single installable orchestrator skill. Intake, observation, static audit, dataset readiness, DeepEval generation, dynamic invocation, remediation planning, and reporting should stay inside this skill as internal stages because they share one run manifest, output folder contract, control catalog, and evidence model.

Do not create one top-level skill per stage by default. Future reusable sibling skills should be split only when they are useful outside the end-to-end audit workflow:

- `golden-dataset-normalizer`
- `deepeval-suite-builder`
- `domain-pack-author`

See `docs/architecture/skill_product_model.md` for the decision record and graduation criteria.

## Keep Outside The Skill Zip

- `docs/`: user guides, prototype journeys, research notes, and local test walkthroughs.
- `domain_extensions/`: optional domain/sub-business-line packs used by teams to configure business, data/MDM, governance, quality-profile, and golden-case expectations.
- `examples/`: runnable demo agents and mock targets.
- `tests/`: scanner fixtures, expected-output oracles, and development self-tests.
- `external_repos/`: cloned public or client repositories.
- `.env`, virtual environments, pycache, generated reports, and any downloaded dependencies.

These files are valuable for proving and demonstrating the skill, but they are not needed by an installed skill and can confuse the packaged experience.

## What Fixtures Are

Fixtures are small fake repositories or files with known expected outcomes. They prove that the scanner can block an unsafe agent and pass a guarded one. They are development tests and few-shot examples for maintainers, not client deliverables.

Keep fixtures outside the zip unless a future skill workflow must copy a fixture into a generated output. If that happens, move only the smallest required fixture into an `assets/` folder and document why it is packaged.
