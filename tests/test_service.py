"""Behavior checks and integrity checks for our synthetic banking fixtures."""

import json

import pytest

from backend.banking import service


@pytest.mark.parametrize("lookup,record_id,key", [
    (service.get_customer, "CUST001", "customer_id"),
    (service.get_account, "ACC001", "account_id"),
    (service.get_transaction, "TXN001", "transaction_id"),
])
def test_single_record_lookup(lookup, record_id, key):
    assert lookup(record_id)[key] == record_id
    assert lookup("UNKNOWN") is None


def test_list_lookups():
    assert [a["account_id"] for a in service.get_customer_accounts("CUST001")] == ["ACC001", "ACC011"]
    assert [t["transaction_id"] for t in service.get_account_transactions("ACC001")] == ["TXN001", "TXN016", "TXN031", "TXN046"]
    assert service.get_customer_accounts("UNKNOWN") == []
    assert service.get_account_transactions("UNKNOWN") == []


def test_fixture_relationships_and_values():
    records = {}
    for name, key, count in [("customers", "customer_id", 10), ("accounts", "account_id", 15), ("transactions", "transaction_id", 50)]:
        rows = json.loads((service.DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))
        assert len(rows) == count
        assert len({r[key] for r in rows}) == count
        assert all(r["is_synthetic"] is True for r in rows)
        records[name] = rows
    customers = {c["customer_id"] for c in records["customers"]}
    accounts = {a["account_id"]: a for a in records["accounts"]}
    assert all(a["customer_id"] in customers for a in accounts.values())
    assert {a["currency"] for a in accounts.values()} == {"AED", "USD", "EUR", "GBP"}
    for transaction in records["transactions"]:
        account = accounts[transaction["account_id"]]
        assert transaction["customer_id"] == account["customer_id"]
        assert transaction["currency"] == account["currency"]
        assert type(transaction["amount_minor"]) is int
        assert transaction["amount_minor"] > 0
    assert {t["status"] for t in records["transactions"]} == {"COMPLETED", "PROCESSING", "FAILED", "REJECTED"}
    assert {t["transaction_type"] for t in records["transactions"]} == {"TRANSFER", "CARD_PAYMENT", "ATM_WITHDRAWAL", "INTERNAL_TRANSFER"}
    example = service.get_transaction("TXN001")
    assert (example["amount_minor"], example["currency"], example["status"]) == (250000, "AED", "PROCESSING")


def test_lookup_result_changes_do_not_modify_file():
    payment = service.get_transaction("TXN001")
    payment["status"] = "FAILED"
    assert service.get_transaction("TXN001")["status"] == "PROCESSING"


@pytest.mark.parametrize("contents", ["{broken", "{}", "[5]", '[{}]', '[{"transaction_id":"TXN001"},{"transaction_id":"TXN001"}]'])
def test_invalid_data_raises_clear_error(tmp_path, monkeypatch, contents):
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    (tmp_path / "transactions.json").write_text(contents, encoding="utf-8")
    with pytest.raises(service.BankingDataError):
        service.get_transaction("TXN001")


def test_missing_file_raises_data_error(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    with pytest.raises(service.BankingDataError, match="transactions.json"):
        service.get_transaction("TXN001")
