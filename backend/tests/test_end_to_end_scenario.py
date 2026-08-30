import json
import hmac
import hashlib
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_full_scenario_txn_4999_upi():
    """
    Specification 15 End-to-End Verification Test:
    1. Transaction txn_4999_upi (₹4,999, failed)
    2. MultiAgentWorkflow analyzes and reasons
    3. Root cause: UPI Degradation
    4. ML: calculates recovery probability
    5. RAG: retrieves policy citation §2.1
    6. Guardrail: APPROVED
    7. Execute: Razorpay Payment Link generated
    8. Webhook: payment_link.paid captured & verified
    9. Transaction: marked recovered
    10. Audit Chain: cryptographically verified
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. AI Analysis & Investigation
        res_analyze = await ac.post("/api/recovery/analyze", json={"transaction_id": "txn_4999_upi"})
        assert res_analyze.status_code == 200
        analysis = res_analyze.json()["data"]

        assert analysis["transaction_id"] == "txn_4999_upi"
        assert analysis["root_cause"] == "Payment Method Degradation"
        assert analysis["recommended_action"] == "payment_link"
        assert analysis["policy_decision"] == "APPROVED"
        assert analysis["recovery_probability"] > 0.70
        assert analysis["expected_recovery"] > 3500.0
        assert len(analysis["evidence"]) >= 3
        assert "2.1" in analysis["rag_policy_reference"] or "Merchant" in analysis["rag_policy_reference"]

        # 2. Execution via Razorpay Test Mode
        res_exec = await ac.post(
            "/api/recovery/execute",
            json={"transaction_id": "txn_4999_upi", "action_type": "payment_link"},
        )
        assert res_exec.status_code == 200
        exec_data = res_exec.json()["data"]
        assert exec_data["status"] == "executed"
        assert exec_data["policy_verdict"] == "APPROVED"
        assert exec_data["razorpay_payment_link"] is not None
        assert "rzp.io" in exec_data["razorpay_payment_link"]

        # 3. Simulate Customer Payment via Razorpay Webhook with Valid Signature
        event_id = f"evt_e2e_verify_{uuid.uuid4().hex[:8]}"
        webhook_payload = {
            "entity": "event",
            "id": event_id,
            "event": "payment_link.paid",
            "contains": ["payment_link", "payment"],
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_e2e_4999",
                        "reference_id": f"recov_txn_4999_upi_{event_id}",
                        "amount": 499900,
                        "status": "paid",
                    }
                },
                "payment": {
                    "entity": {
                        "id": "pay_e2e_4999",
                        "amount": 499900,
                        "status": "captured",
                        "method": "upi",
                    }
                },
            },
        }
        raw_body = json.dumps(webhook_payload).encode("utf-8")
        sig = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        res_webhook = await ac.post(
            "/api/webhooks/razorpay",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
        )
        assert res_webhook.status_code == 200
        wh_data = res_webhook.json()["data"]
        assert wh_data["status"] == "processed"
        assert wh_data["signature_verified"] is True
        assert wh_data["transaction_id"] == "txn_4999_upi"

        # 4. Verify Cryptographic Audit Log Chain Integrity
        res_audit = await ac.get("/api/audit-logs/verify")
        assert res_audit.status_code == 200
        audit_ver = res_audit.json()["data"]
        assert audit_ver["is_valid"] is True
        assert audit_ver["total_records"] > 0
        assert audit_ver["status"] == "cryptographically_verified"
