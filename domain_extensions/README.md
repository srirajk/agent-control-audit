# Domain Extensions

Use this folder for domain or sub-business-line knowledge that should guide an assurance run without being hard-coded into the installable `agent-control-audit` skill.

The skill can run without a domain extension, but a serious governance run is stronger when the user/team provides one.

## Folder Shape

```text
domain_extensions/
├── _template/
│   ├── domain_profile.md
│   ├── quality_profile.json
│   ├── golden_case_requirements.md
│   ├── business_expectations.md
│   ├── data_mdm_expectations.md
│   └── governance_expectations.md
└── financial_aml/
    ├── domain_profile.md
    ├── quality_profile.json
    ├── golden_case_requirements.md
    ├── business_expectations.md
    ├── data_mdm_expectations.md
    └── governance_expectations.md
```

Each subfolder is a domain pack. It can be owned by a business, data/MDM, model-risk, compliance, platform, or product team.

## How Codex Should Use A Domain Pack

When a user says:

```text
Use the domain extension at domain_extensions/financial_aml.
```

Codex should:

- Read the domain pack before finalizing observations, required controls, golden dataset proposals, or report language.
- Copy or reference the selected pack in the run's `00_intake/domain_extension_reference.md`.
- Use the quality profile expectations when reviewing supplied datasets or proposing seed cases.
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
