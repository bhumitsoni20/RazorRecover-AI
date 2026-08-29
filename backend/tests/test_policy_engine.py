import pytest
from app.policies.policy_engine import PolicyEngine


def test_autonomous_payment_link_approved():
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=4999.0,
        proposed_action="payment_link",
        failure_reason="upi_timeout",
        attempt_number=1,
        customer_risk_score=0.12,
    )
    assert verdict == "APPROVED"
    assert any(c.name.startswith("Autonomous Amount Limit") and c.status == "passed" for c in checks)


def test_high_value_transaction_requires_human_approval():
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=35000.0,
        proposed_action="payment_link",
        failure_reason="gateway_timeout",
        attempt_number=1,
        customer_risk_score=0.15,
    )
    assert verdict == "HUMAN_APPROVAL_REQUIRED"
    assert any("exceeds autonomous limit" in c.detail for c in checks)


def test_max_retries_exceeded_blocked():
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=1500.0,
        proposed_action="retry",
        failure_reason="gateway_timeout",
        attempt_number=3,
        customer_risk_score=0.10,
    )
    assert verdict == "BLOCKED"
    assert any("exceeds max allowed automated retries" in c.detail for c in checks)


def test_non_retryable_insufficient_funds_blocked():
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=1500.0,
        proposed_action="retry",
        failure_reason="insufficient_funds",
        attempt_number=1,
        customer_risk_score=0.10,
    )
    assert verdict == "BLOCKED"


def test_high_fraud_risk_blocked():
    verdict, checks, reasons = PolicyEngine.evaluate(
        amount=2500.0,
        proposed_action="payment_link",
        failure_reason="auth_failed",
        attempt_number=1,
        customer_risk_score=0.92,
    )
    assert verdict == "BLOCKED"
