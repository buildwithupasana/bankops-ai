"""Explicit opt-in only: this test sends synthetic text to OpenRouter and costs money."""
import os
import pytest
from backend.ai.service import triage_message


@pytest.mark.live
@pytest.mark.skipif(os.getenv("RUN_LIVE_LLM_TESTS") != "1", reason="Set RUN_LIVE_LLM_TESTS=1 to enable a paid live call")
def test_live_example():
    result = triage_message("Customer reports that transaction TXN001 for AED 2,500 was debited but the beneficiary has not received the payment.")
    assert result.model_dump() == {"issue_type":"payment_not_received", "transaction_id":"TXN001", "amount":2500, "currency":"AED"}
