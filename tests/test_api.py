"""HTTP contracts, real JSON integration, error handling, and documentation."""

import json

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.banking import service


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("path,expected", [
    ("/health", {"status": "ok"}),
    ("/customers/CUST001", {"customer_id": "CUST001", "name": "Synthetic Amal Noor"}),
    ("/accounts/ACC001", {"account_id": "ACC001", "customer_id": "CUST001", "currency": "AED"}),
    ("/transactions/TXN001", {"transaction_id": "TXN001", "amount_minor": 250000, "status": "PROCESSING"}),
])
def test_single_responses(client, path, expected):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert expected.items() <= response.json().items()


@pytest.mark.parametrize("path,key,ids", [
    ("/customers/CUST001/accounts", "account_id", ["ACC001", "ACC011"]),
    ("/accounts/ACC001/transactions", "transaction_id", ["TXN001", "TXN016", "TXN031", "TXN046"]),
])
def test_collections(client, path, key, ids):
    response = client.get(path)
    assert response.status_code == 200
    assert [item[key] for item in response.json()] == ids


@pytest.mark.parametrize("path,detail", [
    ("/customers/UNKNOWN", "Customer not found: UNKNOWN"),
    ("/customers/UNKNOWN/accounts", "Customer not found: UNKNOWN"),
    ("/accounts/UNKNOWN", "Account not found: UNKNOWN"),
    ("/accounts/UNKNOWN/transactions", "Account not found: UNKNOWN"),
    ("/transactions/UNKNOWN", "Transaction not found: UNKNOWN"),
])
def test_missing_resources(client, path, detail):
    response = client.get(path)
    assert response.status_code == 404
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize("path,filename,parent_file", [
    ("/customers/CUST001/accounts", "accounts.json", "customers.json"),
    ("/accounts/ACC001/transactions", "transactions.json", "accounts.json"),
])
def test_existing_parent_empty_collection(client, tmp_path, monkeypatch, path, filename, parent_file):
    (tmp_path / parent_file).write_text((service.DATA_DIR / parent_file).read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / filename).write_text("[]", encoding="utf-8")
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("contents", [None, "{broken", '[{"transaction_id":"TXN001"}]'])
def test_storage_or_response_failure_is_500(client, tmp_path, monkeypatch, contents):
    if contents is not None:
        (tmp_path / "transactions.json").write_text(contents, encoding="utf-8")
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    response = client.get("/transactions/TXN001")
    assert response.status_code == 500
    assert response.json() == {"detail": "Banking data could not be loaded or validated."}
    assert str(tmp_path) not in response.text
    assert client.get("/health").status_code == 200


def test_invalid_stored_amount_is_server_error(client, tmp_path, monkeypatch):
    record = service.get_transaction("TXN001")
    record["amount_minor"] = -1
    (tmp_path / "transactions.json").write_text(json.dumps([record]), encoding="utf-8")
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    assert client.get("/transactions/TXN001").status_code == 500


def test_post_not_allowed(client):
    assert client.post("/transactions/TXN001").status_code == 405


def test_swagger_and_openapi(client):
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "swagger-ui" in docs.text
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert set(schema["paths"]) == {"/health", "/customers/{customer_id}", "/customers/{customer_id}/accounts", "/accounts/{account_id}", "/accounts/{account_id}/transactions", "/transactions/{transaction_id}"}
    transaction = schema["paths"]["/transactions/{transaction_id}"]["get"]
    assert {"200", "404", "500"} <= transaction["responses"].keys()
    assert transaction["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/Transaction")
