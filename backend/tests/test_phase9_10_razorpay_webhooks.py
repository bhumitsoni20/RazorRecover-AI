import hmac
import hashlib
import json
import uuid
import pytest
from app.integrations.razorpay_service import razorpay_service
from app.core.config import settings


@pytest.mark.asyncio
async def test_razorpay_create_payment_link():
    """
    Test Phase 9: Razorpay service creates a valid Test Mode payment link.
    """
    res = await razorpay_service.create_payment_link(
        amount=4999.0,
        currency="INR",
        customer_name="Aditya Verma",
        customer_email="aditya.verma@example.com",
        customer_phone="+919876543210",
        description="Recovery test link",
        reference_id="ref_test_001",
    )
    assert res is not None
    assert "id" in res
    assert "status" in res
    assert res["status"] in ["created", "issued", "active", "paid", "partially_paid", "expired"]


@pytest.mark.asyncio
async def test_webhook_hmac_signature_verification():
    """
    Test Phase 10: HMAC-SHA256 signature verification over raw request body.
    """
    raw_payload = b'{"event":"payment_link.paid","id":"evt_test_123"}'
    secret = settings.RAZORPAY_WEBHOOK_SECRET or "webhook_secret_for_demo_verification_2026"

    # Compute valid signature
    valid_sig = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    assert razorpay_service.verify_webhook_signature(raw_payload, valid_sig) is True
    assert razorpay_service.verify_webhook_signature(raw_payload, "invalid_signature_hex_123") is False


@pytest.mark.asyncio
async def test_webhook_rejection_on_invalid_signature(async_client):
    """
    Test Phase 10: POST /api/webhooks/razorpay rejects malformed signature with 400 Bad Request.
    """
    raw_body = json.dumps({"event": "payment_link.paid", "id": "evt_invalid_test"}).encode("utf-8")
    headers = {
        "X-Razorpay-Signature": "completely_fake_signature_hash_00000000000",
        "Content-Type": "application/json",
    }
    response = await async_client.post("/api/webhooks/razorpay", content=raw_body, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_payment_recovery_flow(async_client):
    """
    Test Phase 10: Valid signed webhook updates transaction to 'recovered' and logs audit.
    """
    event_id = f"evt_test_recovery_{uuid.uuid4().hex[:8]}"
    payload = {
        "event": "payment_link.paid",
        "id": event_id,
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_test_001",
                    "reference_id": "recov_txn_4999_upi_123",
                    "amount": 499900,
                    "currency": "INR",
                    "status": "paid",
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_test_001",
                    "amount": 499900,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    secret = settings.RAZORPAY_WEBHOOK_SECRET or "webhook_secret_for_demo_verification_2026"
    valid_sig = hmac.new(key=secret.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).hexdigest()

    headers = {
        "X-Razorpay-Signature": valid_sig,
        "Content-Type": "application/json",
    }

    # First delivery -> Processed
    response1 = await async_client.post("/api/webhooks/razorpay", content=raw_body, headers=headers)
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["success"] is True
    assert data1["data"]["status"] == "processed"

    # Idempotent re-delivery -> Ignored duplicate
    response2 = await async_client.post("/api/webhooks/razorpay", content=raw_body, headers=headers)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["success"] is True
    assert data2["data"]["status"] == "ignored_duplicate"


@pytest.mark.asyncio
async def test_webhook_simulation_endpoint(async_client):
    """
    Test Phase 10: Development webhook simulator endpoint triggers signed recovery event.
    """
    sim_payload = {
        "transaction_id": "txn_4999_upi",
        "event_type": "payment_link.paid",
        "amount": 4999.0,
    }
    response = await async_client.post("/api/webhooks/simulate", json=sim_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["event_type"] == "payment_link.paid"
