"""Typed tool request schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AMLToolRequest(BaseModel):
    case_id: str = Field(min_length=6, max_length=64)
    source_system: Literal["case_management", "kyc", "transactions", "sanctions", "adverse_media", "policy"]
    evidence_version: str = Field(min_length=2)

    @field_validator("case_id")
    @classmethod
    def semantic_argument_validation(cls, value: str) -> str:
        if not value.startswith("CASE-"):
            raise ValueError("case_id must be a governed case identifier")
        return value


class RegulatedActionRequest(BaseModel):
    case_id: str = Field(min_length=6, max_length=64)
    action: Literal["draft_sar", "rfi", "client_exit", "close_alert", "contact_customer"]
    analyst_id: str = Field(min_length=3)
    evidence_ids: list[str] = Field(min_length=1)
