# Domain Extensions

Use this folder for domain or sub-business-line knowledge that should guide an assurance run without being hard-coded into the installable `agent-control-audit` skill.

The skill can run without a domain extension, but a serious governance run is stronger when the user/team provides one.

## Folder Shape

```text
domain_extensions/
├── _template/
│   ├── domain_profile.md
│   ├── regime_overlay.json
│   ├── quality_profile.json
│   ├── golden_case_requirements.md
│   ├── business_expectations.md
│   ├── data_mdm_expectations.md
│   └── governance_expectations.md
├── financial_aml/
│   ├── domain_profile.md
│   ├── regime_overlay.json
│   ├── quality_profile.json
│   ├── golden_case_requirements.md
│   ├── business_expectations.md
│   ├── data_mdm_expectations.md
│   └── governance_expectations.md
└── financial_lending/
    ├── domain_profile.md
    ├── regime_overlay.json
    ├── quality_profile.json
    ├── golden_case_requirements.md
    ├── business_expectations.md
    ├── data_mdm_expectations.md
    └── governance_expectations.md
```

Each subfolder is a domain pack. It can be owned by a business, data/MDM, model-risk, compliance, platform, or product team. `financial_aml` and `financial_lending` exist as two independent proof points that the same core engine (`agent-control-audit/scripts/static_audit.py`, `engine/schema_validate.py`) plugs into different domains without any core-engine code changes — only the contents of `domain_extensions/<domain>/` differ.

Two of these files are mechanically consumed at runtime, not just read for context:

- `regime_overlay.json` — additional requirements in the same shape as `agent-control-audit/regimes/financial.json` (`requirement_text`, `requires_controls`, `severity_floor`, `source`). When `scripts/static_audit.py` runs with `--domain <name>` and this file exists, its requirements are schema-validated (`engine/schema_validate.py`) and merged into that run's `required_controls` — they show up as real findings, not just narrative.
- `quality_profile.json` — merged into dataset readiness scoring when `scripts/dataset_import.py` runs with `--quality-profile <name> --quality-profile-file domain_extensions/<name>/quality_profile.json` (SKILL.md does this by default whenever a domain is named).

The rest of the pack (`domain_profile.md`, `golden_case_requirements.md`, `business_expectations.md`, `data_mdm_expectations.md`, `governance_expectations.md`) is prose context for Codex/Claude to read and cite — it is not parsed by any script.

## How Codex Should Use A Domain Pack

When a user says:

```text
Use the domain extension at domain_extensions/financial_aml.
```

Codex should:

- Read the domain pack before finalizing observations, required controls, golden dataset proposals, or report language.
- Pass `--domain financial_aml` to `scripts/static_audit.py` so `regime_overlay.json` (if present) actually merges into `required_controls`, and pass `--quality-profile financial_aml --quality-profile-file domain_extensions/financial_aml/quality_profile.json` to `scripts/dataset_import.py` so the domain's dataset expectations actually apply.
- Copy or reference the selected pack in the run's `00_intake/domain_extension_reference.md`, and state plainly whether `regime_overlay.json` was found and merged (`domain_overlay_loaded` in the static audit JSON) — do not say "extension pack not supplied" when one was named and a file exists.
- Treat missing information as an explicit assumption or question, not as a fact.
- Keep user/team approval gates for proposed golden datasets and remediation plans.

## What Belongs Here

- Domain-specific business rules.
- Data/MDM expectations.
- Governance/MRM expectations.
- Golden case requirements.
- Quality profile JSON for dataset readiness.
- Domain vocabulary for reports.

## What Does Not Belong Here

- API keys or secrets.
- Production customer/account identifiers.
- Large copied client repositories.
- Generated reports.
- One-off run artifacts.
- Installed skill internals.

Run artifacts belong under `outputs/<target>/<date>/`. Installed skill files belong under `agent-control-audit/`.
