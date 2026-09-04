import pytest
import json
import hmac
import hashlib
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.integrations.razorpay_service import razorpay_service


@pytest.mark.asyncio
async def test_razorpay_service_methods():
    """
    Test Specification 2: Razorpay service methods.
    """
    # Create Payment Link
    link = await razorpay_service.create_payment_link(
        amount=4999.0,
        currency="INR",
        customer_name="Aditya Verma",
        customer_email="aditya@example.com",
        customer_phone="+919876543210",
        description="Phase 3 Test Link",
        reference_id="recov_test_phase3",
    )
    assert link is not None
    assert "id" in link
    assert "short_url" in link

    # Fetch Payment Link
    fetched_link = await razorpay_service.fetch_payment_link(link["id"])
    assert fetched_link is not None
    assert fetched_link["id"] == link["id"]

    # Fetch Payment
    fetched_pay = await razorpay_service.fetch_payment("pay_test_12345")
    assert fetched_pay is not None
    assert fetched_pay["status"] == "captured"


@pytest.mark.asyncio
async def test_recovery_status_endpoint(async_client):
    """
    Test Specification 5: GET /api/recovery/{transaction_id}/status
    """
    res = await async_client.get("/api/recovery/txn_4999_upi/status")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["transaction_id"] == "txn_4999_upi"
    assert "status" in data
    assert "is_recovered" in data


@pytest.mark.asyncio
async def test_human_approval_lifecycle(async_client):
    """
    Test Specification 20: Human approval branch.
    """
    # High value transaction
    res_exec = await async_client.post("/api/recovery/txn_high_value/execute")
    assert res_exec.status_code == 200
    exec_data = res_exec.json()["data"]
    assert exec_data["policy_verdict"] == "HUMAN_APPROVAL_REQUIRED"
    assert exec_data["status"] == "pending_approval"

    # Approve action
    res_app = await async_client.post(
        "/api/recovery/txn_high_value/approve",
        json={"transaction_id": "txn_high_value", "approved": True, "approver_note": "Approved by Risk Officer"},
    )
    assert res_app.status_code == 200
    app_data = res_app.json()["data"]
    assert app_data["status"] == "executed"


@pytest.mark.asyncio
async def test_blocked_transaction_lifecycle(async_client):
    """
    Test Specification 21 & 22: Blocked retry limit exceeded.
    """
    res = await async_client.post("/api/recovery/txn_retry_exceeded/execute")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == "blocked"
    assert data["policy_verdict"] == "BLOCKED"


@pytest.mark.asyncio
async def test_idempotent_recovery_execution(async_client):
    """
    Test Specification 4: Idempotent execution preventing duplicate actions.
    """
    # Already recovered transaction
    res1 = await async_client.post("/api/recovery/txn_already_recovered/execute")
    assert res1.status_code == 200
    assert res1.json()["data"]["status"] == "recovered"

    # Execute txn_4999_upi once
    res_exec1 = await async_client.post("/api/recovery/txn_4999_upi/execute")
    assert res_exec1.status_code == 200
    link1 = res_exec1.json()["data"]["razorpay_payment_link"]

    # Execute txn_4999_upi second time -> returns existing link without duplication
    res_exec2 = await async_client.post("/api/recovery/txn_4999_upi/execute")
    assert res_exec2.status_code == 200
    link2 = res_exec2.json()["data"]["razorpay_payment_link"]
    assert link1 == link2


@pytest.mark.asyncio
async def test_full_phase3_end_to_end_recovery(async_client):
    """
    Test Specification 1 & 26: Full end-to-end recovery pipeline for txn_4999_upi.
    """
    # 1. Investigate with AI
    res_an = await async_client.post("/api/recovery/txn_4999_upi/analyze")
    assert res_an.status_code == 200
    an_data = res_an.json()["data"]
    assert an_data["policy_decision"] == "APPROVED"
    assert an_data["recommended_action"] == "payment_link"

    # 2. Execute Recovery
    res_ex = await async_client.post("/api/recovery/txn_4999_upi/execute")
    assert res_ex.status_code == 200
    ex_data = res_ex.json()["data"]
    assert ex_data["status"] == "executed"
    assert ex_data["razorpay_payment_link"] is not None

    # 3. Simulate Inbound Webhook with HMAC signature
    event_id = f"evt_p3_{uuid.uuid4().hex[:8]}"
    payload = {
        "entity": "event",
        "id": event_id,
        "event": "payment_link.paid",
        "contains": ["payment_link", "payment"],
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_phase3_demo",
                    "reference_id": f"recov_txn_4999_upi_{event_id}",
                    "amount": 499900,
                    "status": "paid",
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_phase3_demo",
                    "amount": 499900,
                    "status": "captured",
                    "method": "upi",
                }
            },
        },
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    res_wh = await async_client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert res_wh.status_code == 200
    wh_data = res_wh.json()["data"]
    assert wh_data["status"] == "processed"
    assert wh_data["signature_verified"] is True
    assert wh_data["transaction_id"] == "txn_4999_upi"

    # 4. Verify transaction status flipped to recovered
    res_stat = await async_client.get("/api/recovery/txn_4999_upi/status")
    assert res_stat.status_code == 200
    assert res_stat.json()["data"]["is_recovered"] is True

    # 5. Verify cryptographic audit chain validity
    res_aud = await async_client.get("/api/audit-logs/verify")
    assert res_aud.status_code == 200
    aud_data = res_aud.json()["data"]
    assert aud_data["is_valid"] is True

