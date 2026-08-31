import pytest
from app.policies.policy_engine import PolicyEngine


def test_guardrail_retry_limit_exceeded():
    """
    Test Phase 8: Attempt count 3 exceeds max limit of 2 -> BLOCKED.
    """
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=4999.0,
        proposed_action="payment_link",
        failure_reason="upi_timeout",
        attempt_number=3,
        customer_risk_score=0.10,
    )
    assert verdict == "BLOCKED"
    retry_check = next((c for c in checks if "Retry" in c.name), None)
    assert retry_check is not None
    assert retry_check.status == "failed"


def test_guardrail_high_value_human_approval():
    """
    Test Phase 8: Amount > ₹25,000 strictly requires HUMAN_APPROVAL_REQUIRED.
    """
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=50000.0,
        proposed_action="payment_link",
        failure_reason="gateway_timeout",
        attempt_number=1,
        customer_risk_score=0.10,
    )
    assert verdict == "HUMAN_APPROVAL_REQUIRED"
    amount_check = next((c for c in checks if "Amount" in c.name), None)
    assert amount_check is not None
    assert amount_check.status == "warning"


def test_guardrail_discount_cap_exceeded():
    """
    Test Phase 8: Proposed discount > 10% requires HUMAN_APPROVAL_REQUIRED.
    """
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=5000.0,
        proposed_action="payment_link",
        failure_reason="upi_timeout",
        attempt_number=1,
        proposed_discount_pct=15.0,
    )
    assert verdict == "HUMAN_APPROVAL_REQUIRED"
    discount_check = next((c for c in checks if "Discount" in c.name), None)
    assert discount_check is not None
    assert discount_check.status == "warning"


def test_guardrail_critical_fraud_risk():
    """
    Test Phase 8: Customer risk score > 0.85 -> BLOCKED.
    """
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=3000.0,
        proposed_action="payment_link",
        failure_reason="upi_timeout",
        attempt_number=1,
        customer_risk_score=0.92,
    )
    assert verdict == "BLOCKED"
    fraud_check = next((c for c in checks if "Fraud" in c.name), None)
    assert fraud_check is not None
    assert fraud_check.status == "failed"


def test_guardrail_non_retryable_failure_code():
    """
    Test Phase 8: Non-retryable codes like card_stolen_or_lost -> BLOCKED.
    """
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=2000.0,
        proposed_action="retry",
        failure_reason="card_stolen_or_lost",
        attempt_number=1,
    )
    assert verdict == "BLOCKED"
    code_check = next((c for c in checks if "Non-Retryable" in c.name), None)
    assert code_check is not None
    assert code_check.status == "failed"


def test_guardrail_stopping_rule_already_recovered():
    """
    Test Phase 8: Stopping rule halts recovery on already recovered transaction.
    """
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=4999.0,
        proposed_action="payment_link",
        failure_reason="upi_timeout",
        attempt_number=1,
        transaction_status="recovered",
    )
    assert verdict == "BLOCKED"
    status_check = next((c for c in checks if "Stopping Rule" in c.name), None)
    assert status_check is not None
    assert status_check.status == "failed"


def test_guardrail_duplicate_recovery_prevention():
    """
    Test Phase 8: Duplicate active link creation is blocked.
    """
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=4999.0,
        proposed_action="payment_link",
        failure_reason="upi_timeout",
        attempt_number=1,
        has_active_link=True,
    )
    assert verdict == "BLOCKED"
    dup_check = next((c for c in checks if "Duplicate" in c.name), None)
    assert dup_check is not None
    assert dup_check.status == "failed"


def test_guardrail_valid_approved_transaction():
    """
    Test Phase 8: Normal valid failed transaction passes all guardrails -> APPROVED.
    """
    structured = PolicyEngine.evaluate_structured(
        amount=4999.0,
        proposed_action="payment_link",
        failure_reason="upi_timeout",
        attempt_number=1,
        customer_risk_score=0.15,
        proposed_discount_pct=5.0,
        transaction_status="failed",
        has_active_link=False,
    )
    assert structured["verdict"] == "APPROVED"
    assert structured["is_approved"] is True
    assert len(structured["checks"]) >= 5
