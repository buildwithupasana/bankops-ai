"""HTTP routing; banking lookups remain in service.py."""

from fastapi import APIRouter, HTTPException

from backend.banking import service
from backend.banking.models import Account, Customer, ErrorResponse, HealthResponse, Transaction

router = APIRouter()
ERRORS = {
    404: {"model": ErrorResponse, "description": "Requested resource does not exist."},
    500: {"model": ErrorResponse, "description": "Backing banking data could not be loaded or validated."},
}


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    """Application liveness only; does not check backing files."""
    return {"status": "ok"}


@router.get("/customers/{customer_id}", response_model=Customer, responses=ERRORS, tags=["Customers"])
def read_customer(customer_id: str):
    customer = service.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")
    return customer


@router.get("/customers/{customer_id}/accounts", response_model=list[Account], responses=ERRORS, tags=["Customers"])
def read_customer_accounts(customer_id: str):
    if service.get_customer(customer_id) is None:
        raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")
    return service.get_customer_accounts(customer_id)


@router.get("/accounts/{account_id}", response_model=Account, responses=ERRORS, tags=["Accounts"])
def read_account(account_id: str):
    account = service.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account not found: {account_id}")
    return account


@router.get("/accounts/{account_id}/transactions", response_model=list[Transaction], responses=ERRORS, tags=["Accounts"])
def read_account_transactions(account_id: str):
    if service.get_account(account_id) is None:
        raise HTTPException(status_code=404, detail=f"Account not found: {account_id}")
    return service.get_account_transactions(account_id)


@router.get("/transactions/{transaction_id}", response_model=Transaction, responses=ERRORS, tags=["Transactions"])
def read_transaction(transaction_id: str):
    transaction = service.get_transaction(transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail=f"Transaction not found: {transaction_id}")
    return transaction
