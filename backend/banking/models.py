"""Response contracts; these are not database tables."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

Currency = Literal["AED", "USD", "EUR", "GBP"]


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ErrorResponse(BaseModel):
    detail: str


class Customer(BaseModel):
    customer_id: str
    name: str
    city: str
    country: Literal["AE"]
    is_synthetic: Literal[True]


class Account(BaseModel):
    account_id: str
    customer_id: str
    currency: Currency
    account_type: Literal["CURRENT", "SAVINGS"]
    is_synthetic: Literal[True]


class Transaction(BaseModel):
    transaction_id: str
    account_id: str
    customer_id: str
    amount_minor: int = Field(gt=0, strict=True, description="Integer minor units; 100 equals one whole currency unit.")
    currency: Currency
    status: Literal["COMPLETED", "PROCESSING", "FAILED", "REJECTED"]
    transaction_type: Literal["TRANSFER", "CARD_PAYMENT", "ATM_WITHDRAWAL", "INTERNAL_TRANSFER"]
    direction: Literal["DEBIT"]
    created_at: AwareDatetime
    description: str
    is_synthetic: Literal[True]
