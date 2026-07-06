"""ADK root-agent construction."""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

from .callbacks import (
    after_agent_callback,
    after_tool_callback,
    before_agent_callback,
    before_model_callback,
    before_tool_callback,
)
from .config import MODEL_VERSION
from .tools import prepare_regulated_action, retrieve_case_evidence

root_agent = LlmAgent(
    name="adk_aml_openai_reference",
    model=LiteLlm(model=MODEL_VERSION),
    instruction=(
        "You support AML analysts. You may retrieve evidence and draft analyst-facing summaries. "
        "You must not file SARs, close alerts, contact customers, or recommend client exit without "
        "human approval. Cite evidence IDs for material claims, redact sensitive identifiers, and "
        "fall back to manual review when evidence is missing."
    ),
    tools=[
        FunctionTool(retrieve_case_evidence),
        FunctionTool(prepare_regulated_action),
    ],
    before_agent_callback=before_agent_callback,
    before_model_callback=before_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    after_agent_callback=after_agent_callback,
)
