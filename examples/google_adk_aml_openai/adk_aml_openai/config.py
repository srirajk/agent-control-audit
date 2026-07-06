"""Runtime and control configuration for the AML ADK reference agent."""

MODEL_VERSION = "openai/gpt-4o-mini"
ADK_VERSION = "adk-1.x"

DATASET_HASH = "sha256:example-adk-openai-aml-golden-dataset"
RANDOM_SEED = 7
EVAL_THRESHOLD = 0.9
TEMPERATURE = 0

MODEL_OWNER = "aml-product-owner"
CONTROL_OWNER = "model-risk-management"
RISK_TIER = "high"
INTENDED_USE = "AML analyst decision support; draft-only recommendations"
PROHIBITED_USE = "No autonomous SAR filing, customer contact, alert closure, or client exit"

MAX_TOOL_CALLS = 12
MAX_TOKENS = 4096
MAX_RUNTIME_SECONDS = 60
RATE_LIMIT_PER_CASE = 25
KILL_SWITCH_ENABLED = False
RETRY_POLICY = {"max_retries": 2, "timeout_seconds": 20, "fallback": "manual_review"}

ALLOWED_RETRIEVAL_SOURCES = {
    "case_management",
    "kyc",
    "transactions",
    "sanctions",
    "adverse_media",
    "policy",
}
SENSITIVE_FIELDS = {"account_number", "ssn", "tax_id", "full_pan", "secret", "token"}
HIGH_IMPACT_ACTIONS = {"draft_sar", "rfi", "client_exit", "close_alert", "contact_customer"}
HANDOFF_ALLOWLIST = {"transaction_selection_agent", "due_diligence_agent", "case_analysis_agent"}
REQUIRED_CITATION_FIELDS = {"source_system", "record_id", "evidence_version"}
