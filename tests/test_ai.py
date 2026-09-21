"""Offline tests: replace the SDK client, never contact OpenAI."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

from backend.ai import service
from backend.ai.models import TriageResult
from backend.main import app

MESSAGE = "Customer reports that transaction TXN001 for AED 2,500 was debited but the beneficiary has not received the payment."
RESULT = dict(issue_type="payment_not_received", transaction_id="TXN001", amount=2500, currency="AED")


@pytest.fixture
def sdk(monkeypatch):
    monkeypatch.setattr(service, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-test-placeholder")
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o")
    factory = MagicMock()
    client = factory.return_value.__enter__.return_value
    client.chat.completions.parse.return_value = SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(refusal=None, parsed=TriageResult(**RESULT)))])
    monkeypatch.setattr(service, "OpenAI", factory)
    return factory, client


def test_extraction_request_and_response(sdk):
    factory, client = sdk
    with TestClient(app) as api:
        response = api.post("/ai/triage", json={"message": MESSAGE})
    assert response.status_code == 200
    assert response.json() == RESULT
    args = client.chat.completions.parse.call_args.kwargs
    assert args["response_format"] is TriageResult
    assert args["messages"][1] == {"role": "user", "content": MESSAGE}
    assert args["messages"][0]["role"] == "system"
    assert args["extra_body"] == {"provider": {"require_parameters": True}}
    assert factory.call_args.kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert "tools" not in args
    assert factory.call_args.kwargs["max_retries"] == 0


@pytest.mark.parametrize("body", [{}, {"message":""}, {"message":"   "}, {"message":5}, {"message":"x"*4001}, {"message":"hello", "extra":1}])
def test_invalid_input_never_calls_model(sdk, body):
    with TestClient(app) as api:
        assert api.post("/ai/triage", json=body).status_code == 422
    sdk[0].assert_not_called()


def test_missing_key_and_banking_still_work(sdk, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY")
    with TestClient(app) as api:
        assert api.post("/ai/triage", json={"message":MESSAGE}).status_code == 503
        assert api.get("/transactions/TXN001").status_code == 200
    sdk[0].assert_not_called()


@pytest.mark.parametrize("kind,expected", [("timeout",504),("connection",502),("auth",503),("rate",503),("invalid",502)])
def test_safe_provider_errors(sdk, kind, expected, caplog):
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    errors = {
        "timeout": APITimeoutError(request=request),
        "connection": APIConnectionError(request=request),
        "auth": AuthenticationError("unit-test-placeholder", response=httpx.Response(401, request=request), body=None),
        "rate": RateLimitError("unit-test-placeholder", response=httpx.Response(429, request=request), body=None),
        "invalid": ValueError("unit-test-placeholder"),
    }
    sdk[1].chat.completions.parse.side_effect = errors[kind]
    with TestClient(app) as api:
        response = api.post("/ai/triage", json={"message":MESSAGE})
    assert response.status_code == expected
    assert "unit-test-placeholder" not in response.text + caplog.text


@pytest.mark.parametrize("kind,expected", [("incomplete",502),("refusal",422),("missing",502)])
def test_unusable_outputs(sdk, kind, expected):
    response = sdk[1].chat.completions.parse.return_value
    response.choices[0].message.parsed = None
    if kind == "incomplete":
        response.choices[0].finish_reason = "length"
    if kind == "refusal":
        response.choices[0].message.refusal = "Declined"
    with TestClient(app) as api:
        assert api.post("/ai/triage", json={"message":MESSAGE}).status_code == expected


def test_nullable_result(sdk):
    sdk[1].chat.completions.parse.return_value.choices[0].message.parsed = TriageResult(issue_type="unclear", transaction_id=None, amount=None, currency=None)
    with TestClient(app) as api:
        response = api.post("/ai/triage", json={"message":"Please help"})
    assert response.status_code == 200
    assert response.json() == {"issue_type":"unclear", "transaction_id":None, "amount":None, "currency":None}


def test_openapi_triage_contract():
    with TestClient(app) as api:
        schema = api.get("/openapi.json").json()
    operation = schema["paths"]["/ai/triage"]["post"]
    assert operation["requestBody"]["required"] is True
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/TriageResult")


def test_real_sdk_schema_and_parsing_without_network(monkeypatch):
    """Exercise SDK serialization/parsing with a fake HTTP transport, not a real LLM."""
    import json
    from openai import OpenAI

    captured = {}

    def respond(request):
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "chatcmpl_test", "object": "chat.completion", "created": 0,
            "model": "openai/gpt-4o",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": json.dumps(RESULT), "refusal": None}}],
        })

    monkeypatch.setattr(service, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "unit-test-placeholder")
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o")
    monkeypatch.setattr(service, "OpenAI", lambda **kwargs: OpenAI(
        **kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond))))
    assert service.triage_message(MESSAGE).model_dump() == RESULT
    output_format = captured["response_format"]
    assert captured["provider"]["require_parameters"] is True
    assert output_format["type"] == "json_schema"
    assert output_format["json_schema"]["strict"] is True
    assert output_format["json_schema"]["schema"]["additionalProperties"] is False
    assert set(output_format["json_schema"]["schema"]["required"]) == set(RESULT)
