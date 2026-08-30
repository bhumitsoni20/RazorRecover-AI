import json
import hmac
import hashlib
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_webhook_with_valid_signature():
    payload = {
        "entity": "event",
        "account_id": "acc_test_merchant",
        "event": "payment_link.paid",
        "id": "evt_test_valid_101",
        "contains": ["payment_link", "payment"],
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_test_valid_101",
                    "reference_id": "recov_txn_4999_upi_12345",
                    "amount": 499900,
                    "status": "paid",
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_test_valid_101",
                    "amount": 499900,
                    "status": "captured",
                }
            },
        },
        "created_at": 1772345600,
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["signature_verified"] is True
    assert data["data"]["status"] == "processed"


@pytest.mark.asyncio
async def test_webhook_idempotency_duplicate_event():
    event_id = "evt_test_idempotent_duplicate_999"
    payload = {
        "id": event_id,
        "event": "payment_link.paid",
        "contains": ["payment_link"],
        "payload": {
            "payment_link": {"entity": {"reference_id": "recov_txn_4999_upi", "amount": 499900}},
            "payment": {"entity": {"amount": 499900}},
        },
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First call: should process
        res1 = await ac.post(
            "/api/webhooks/razorpay",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
        )
        assert res1.status_code == 200
        assert res1.json()["data"]["status"] == "processed"

        # Second call with same event_id: must be ignored as duplicate
        res2 = await ac.post(
            "/api/webhooks/razorpay",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
        )
        assert res2.status_code == 200
        assert res2.json()["data"]["status"] == "ignored_duplicate"
        assert res2.json()["data"]["action_taken"] == "duplicate_event_already_processed"


@pytest.mark.asyncio
async def test_webhook_reject_invalid_signature():
    raw_body = b'{"event": "payment_link.paid"}'
    invalid_sig = "invalid_fake_signature_hash"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/webhooks/razorpay",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": invalid_sig},
        )
    assert response.status_code == 400
    assert "Invalid Razorpay webhook signature" in response.json()["detail"]
