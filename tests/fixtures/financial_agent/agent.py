from typing import Literal

from pydantic import BaseModel, Field

from agents import (
    Agent,
    FileSearchTool,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    function_tool,
    handoff,
    input_guardrail,
)


class AdviceGuardrailOutput(BaseModel):
    should_block: bool
    reason: str


class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount_usd: float = Field(gt=0, le=10_000)
    memo: str | None = Field(default=None, max_length=120)
    transfer_type: Literal["ach", "wire"]


guardrail_agent = Agent(
    name="Advice request classifier",
    instructions="Block requests for guaranteed returns or instructions to bypass financial controls.",
    output_type=AdviceGuardrailOutput,
)


@input_guardrail
async def advice_request_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str,
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.should_block,
    )


def log_audit_event(event_type: str, payload: dict) -> None:
    print({"event_type": event_type, "payload": payload})


@function_tool
async def transfer_funds(request: TransferRequest) -> str:
    log_audit_event(
        "transfer_requested",
        {
            "from_account_id": request.from_account_id,
            "to_account_id": request.to_account_id,
            "amount_usd": request.amount_usd,
        },
    )
    return f"Submitted {request.transfer_type} transfer for ${request.amount_usd:.2f}"


portfolio_specialist = Agent(
    name="Portfolio specialist",
    instructions="Answer detailed questions about customer holdings and market exposure.",
)


financial_agent = Agent(
    name="Customer financial assistant",
    instructions=(
        "Help customers understand their portfolio, answer questions from available files, "
        "and transfer funds when requested."
    ),
    input_guardrails=[advice_request_guardrail],
    tools=[
        FileSearchTool(vector_store_ids=["vs_financial_policy"]),
        transfer_funds,
    ],
    handoffs=[handoff(portfolio_specialist)],
)
