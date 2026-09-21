"""Input validation and the structured extraction contract."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TriageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be blank")
        return value.strip()


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    issue_type: Literal["payment_not_received", "other", "unclear"]
    transaction_id: str | None
    amount: float | None = Field(description="Stated amount in whole currency units, not minor units; null if unknown.")
    currency: Literal["AED", "USD", "EUR", "GBP"] | None

    @field_validator("amount")
    @classmethod
    def check_amount(cls, value: float | None) -> float | None:
        import math
        if value is not None and (not math.isfinite(value) or value < 0):
            raise ValueError("Amount must be finite and nonnegative")
        return value
