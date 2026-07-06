"""Source-visible model governance evidence for the reference agent."""

from .config import CONTROL_OWNER, MODEL_OWNER, RISK_TIER

model_inventory = {
    "model_owner": MODEL_OWNER,
    "control_owner": CONTROL_OWNER,
    "risk_tier": RISK_TIER,
    "deployment_status": "reference_example",
}
limitations = "Requires analyst approval and validated source evidence before disposition."
independent_validation = "second_line_effective_challenge_required_before_production"
data_lineage = ["case_management", "kyc", "transactions", "sanctions", "adverse_media"]
data_quality = {"freshness_hours": 24, "completeness_threshold": 0.98}
drift_monitoring = {"alert_mix_psi": 0.2, "analyst_override_rate_threshold": 0.15}
benchmark = "historical analyst disposition and rules baseline"
fairness = "segment checks by geography, customer type, PEP status, and risk band"
explainability = "reason_code plus citation evidence required for each recommendation"
change_management = "release_approval_required_for_prompt_tool_policy_dataset_threshold_changes"
vendor_risk = "OpenAI model_provider and ADK/LiteLLM dependency risk tracked"
RBAC = "builder_validator_approver_analyst_roles_segregated"
evidence_retention = "retain prompts, traces, approvals, evals, and evidence bundles per legal_hold policy"
business_continuity = "rollback, fail_closed, RTO, RPO, and decommission criteria documented"
model_governance_report = "monthly governance dashboard for validation, incidents, drift, exceptions, and eval regressions"
