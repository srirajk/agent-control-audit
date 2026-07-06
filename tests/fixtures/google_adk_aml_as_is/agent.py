"""Intentionally under-controlled Google ADK-style AML agent fixture.

This fixture mimics a real AML investigation agent shape before assurance
controls are added. It is meant to trigger findings in static audit.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool


def select_transactions(case_id: str, lookback_days: int) -> dict:
    return {
        "case_id": case_id,
        "selected_transaction_ids": ["TX-100", "TX-200"],
        "reason": "large reportable transfer pattern",
    }


def draft_case_analysis(case_id: str, party_id: str) -> dict:
    return {
        "case_id": case_id,
        "party_id": party_id,
        "recommendation": "prepare SAR narrative",
        "summary": "Potential suspicious activity based on transaction velocity.",
    }


def create_sar_narrative(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "narrative": "Draft SAR narrative for analyst review.",
    }


root_agent = LlmAgent(
    name="aml_investigation_as_is",
    model="gemini-flash-latest",
    instruction=(
        "Help AML analysts enrich cases, select transactions, summarize due "
        "diligence, and draft case analysis."
    ),
    tools=[
        FunctionTool(select_transactions),
        FunctionTool(draft_case_analysis),
        FunctionTool(create_sar_narrative),
    ],
)

