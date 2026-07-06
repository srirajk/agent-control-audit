"""FastAPI wrapper exposing the normalized assurance contract."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ..assurance.eval_adapter import run_case


class AssuranceCase(BaseModel):
    id: str
    suite: str
    input: str
    expected: str | None = None
    must_not: list[str] = Field(default_factory=list)
    severity: str = "medium"
    source: str = "http"
    retrieved_doc: str | None = None
    user_context: dict[str, Any] | None = None


app = FastAPI(title="ADK AML OpenAI Assurance Example")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/invoke")
def invoke(case: AssuranceCase) -> dict[str, Any]:
    return run_case(case.model_dump())
