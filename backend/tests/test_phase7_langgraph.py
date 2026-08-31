import pytest
from app.agents.workflow import MultiAgentWorkflow, recovery_langgraph_app, WorkflowState


@pytest.mark.asyncio
async def test_langgraph_full_approved_workflow():
    """
    Test Phase 7: LangGraph full execution for standard approved payment link flow.
    """
    result = await MultiAgentWorkflow.run(
        transaction_id="txn_4999_upi",
        amount=4999.0,
        customer_name="Aditya Verma",
        customer_email="aditya.verma@example.com",
        customer_phone="+919876543210",
        payment_method="upi",
        failure_reason="upi_timeout",
        attempt_number=1,
        bank="HDFC",
        customer_success_rate=0.867,
    )

    assert result["transaction_id"] == "txn_4999_upi"
    assert result["policy_decision"] == "APPROVED"
    assert result["action"] == "payment_link"
    assert result["root_cause"] == "payment_method_degradation"
    assert 0.0 <= result["confidence"] <= 1.0
    assert 0.0 <= result["recovery_probability"] <= 1.0
    assert len(result["evidence"]) >= 1
    assert len(result["policy_references"]) >= 1
    assert result["execution"]["status"] == "executed"
    assert "short_url" in result["execution"]
    assert result["verification"]["verified"] is True
    assert result["verification"]["status"] == "awaiting_payment"
    assert len(result["audit_trail"]) >= 6


@pytest.mark.asyncio
async def test_langgraph_human_review_branch():
    """
    Test Phase 7: LangGraph conditional branch routes high value > ₹25,000 to human review.
    """
    result = await MultiAgentWorkflow.run(
        transaction_id="txn_high_value",
        amount=50000.0,
        customer_name="Priya Sharma",
        customer_email="priya.sharma@example.com",
        customer_phone="+919876543211",
        payment_method="netbanking",
        failure_reason="gateway_timeout",
        attempt_number=1,
        bank="HDFC",
        customer_success_rate=0.90,
    )

    assert result["policy_decision"] == "HUMAN_APPROVAL_REQUIRED"
    assert result["execution"]["status"] == "pending_human_approval"
    assert result["verification"]["verified"] is False
    assert result["verification"]["status"] == "awaiting_human_approval"


@pytest.mark.asyncio
async def test_langgraph_blocked_branch():
    """
    Test Phase 7: LangGraph conditional branch blocks attempt count >= 3.
    """
    result = await MultiAgentWorkflow.run(
        transaction_id="txn_max_retries",
        amount=1987.0,
        customer_name="Rahul Nair",
        customer_email="rahul.nair@example.com",
        customer_phone="+919876543212",
        payment_method="card",
        failure_reason="card_declined",
        attempt_number=3,
        bank="ICICI",
        customer_success_rate=0.60,
    )

    assert result["policy_decision"] == "BLOCKED"
    assert result["execution"]["status"] == "blocked"
    assert result["verification"]["verified"] is False
    assert result["verification"]["status"] == "blocked"


@pytest.mark.asyncio
async def test_langgraph_ainvoke_direct():
    """
    Test Phase 7: Direct invocation of compiled StateGraph app.
    """
    state: WorkflowState = {
        "transaction_id": "txn_direct_test",
        "amount": 2500.0,
        "currency": "INR",
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "customer_phone": "+919876543210",
        "payment_method": "upi",
        "failure_reason": "upi_timeout",
        "attempt_number": 1,
        "bank": "HDFC",
        "customer_success_rate": 0.85,
    }

    final_state = await recovery_langgraph_app.ainvoke(state)
    assert final_state["policy_verdict"] == "APPROVED"
    assert final_state["execution_result"]["status"] == "executed"
    assert "verification_result" in final_state
    assert len(final_state["audit_trail"]) >= 6
