"""Read-only banking lookups backed by local synthetic JSON files."""

import json
from pathlib import Path

# Resolve from this file, so loading does not depend on the terminal directory.
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class BankingDataError(Exception):
    """The backing data file could not be read or has an invalid basic shape."""


def _load_records(filename: str, id_field: str) -> list[dict]:
    path = DATA_DIR / filename
    try:
        with path.open(encoding="utf-8") as file:
            records = json.load(file)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BankingDataError(f"Cannot load {path.name}: {error}") from error

    if not isinstance(records, list):
        raise BankingDataError(f"{filename} must contain a JSON list.")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise BankingDataError(f"{filename} must contain only objects.")
        record_id = record.get(id_field)
        if not isinstance(record_id, str) or not record_id.strip():
            raise BankingDataError(f"Every record in {filename} needs a nonempty {id_field}.")
        if record_id in seen:
            raise BankingDataError(f"Duplicate {id_field} in {filename}: {record_id}")
        seen.add(record_id)
    return records


def _find_record(filename: str, id_field: str, record_id: str) -> dict | None:
    for record in _load_records(filename, id_field):
        if record[id_field] == record_id:
            return record
    return None


def get_customer(customer_id: str) -> dict | None:
    """Return a customer, or None if the exact ID is unknown."""
    return _find_record("customers.json", "customer_id", customer_id)


def get_account(account_id: str) -> dict | None:
    """Return an account, or None if the exact ID is unknown."""
    return _find_record("accounts.json", "account_id", account_id)


def get_transaction(transaction_id: str) -> dict | None:
    """Return a transaction, or None if the exact ID is unknown."""
    return _find_record("transactions.json", "transaction_id", transaction_id)


def get_customer_accounts(customer_id: str) -> list[dict]:
    """Return matching accounts; an unknown customer has no matches ([])."""
    return [account for account in _load_records("accounts.json", "account_id")
            if account["customer_id"] == customer_id]


def get_account_transactions(account_id: str) -> list[dict]:
    """Return matching transactions in file order, or [] if there are none."""
    return [transaction for transaction in _load_records("transactions.json", "transaction_id")
            if transaction["account_id"] == account_id]
