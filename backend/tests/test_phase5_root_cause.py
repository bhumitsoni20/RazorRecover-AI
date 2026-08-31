import pytest
from app.agents.root_cause_agent import root_cause_agent, RootCauseAgent
from app.schemas.root_cause import RootCauseAnalysis, RootCauseCategory


@pytest.mark.asyncio
async def test_valid_transaction_root_cause_analysis():
    """
    Test Phase 5: Valid transaction signals produce structured root cause output.
    """
    result = await root_cause_agent.analyze(
        transaction_id="txn_4999_upi",
        amount=4999.0,
        currency="INR",
        payment_method="upi",
        failure_reason="upi_timeout",
        failure_code="PSP_TIMEOUT",
        attempt_count=1,
        bank="HDFC",
        customer_name="Aditya Verma",
        customer_success_rate=0.867,
        anomaly_info={"anomaly_detected": True, "anomaly_message": "UPI failure spike +4.8x"},
    )

    assert isinstance(result, RootCauseAnalysis)
    assert result.transaction_id == "txn_4999_upi"
    assert result.root_cause in [c.value for c in RootCauseCategory]
    assert result.root_cause == RootCauseCategory.PAYMENT_METHOD_DEGRADATION.value
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.evidence) >= 1
    assert result.explanation is not None
    assert len(result.explanation) > 10


@pytest.mark.asyncio
async def test_missing_fields_marked_unavailable():
    """
    Test Phase 5: Missing optional signals are marked UNAVAILABLE rather than hallucinated.
    """
    result = await root_cause_agent.analyze(
        transaction_id="txn_sparse_data",
        amount=1200.0,
        currency="INR",
        payment_method="card",
        failure_reason=None,
        failure_code=None,
        attempt_count=1,
        bank=None,
        customer_name=None,
        customer_success_rate=None,
        anomaly_info=None,
    )

    assert result.signals_analyzed is not None
    assert result.signals_analyzed["bank_network"] == "UNAVAILABLE"
    assert result.signals_analyzed["customer_name"] == "UNAVAILABLE"
    assert result.signals_analyzed["customer_historical_success_rate"] == "UNAVAILABLE"
    assert result.root_cause in [c.value for c in RootCauseCategory]
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_repeated_failure_category():
    """
    Test Phase 5: High attempt count triggers repeated_payment_failure category.
    """
    result = await root_cause_agent.analyze(
        transaction_id="txn_3_attempts",
        amount=1999.0,
        currency="INR",
        payment_method="card",
        failure_reason="declined_by_issuer",
        attempt_count=3,
        bank="ICICI",
    )

    assert result.root_cause == RootCauseCategory.REPEATED_PAYMENT_FAILURE.value
    assert result.confidence >= 0.80
    assert any("attempt count #3" in e for e in result.evidence)


@pytest.mark.asyncio
async def test_insufficient_funds_category():
    """
    Test Phase 5: Insufficient funds failure reason triggers insufficient_funds.
    """
    result = await root_cause_agent.analyze(
        transaction_id="txn_low_balance",
        amount=8500.0,
        currency="INR",
        payment_method="netbanking",
        failure_reason="insufficient_funds",
        attempt_count=1,
        bank="SBI",
    )

    assert result.root_cause == RootCauseCategory.INSUFFICIENT_FUNDS.value
    assert result.confidence >= 0.85
    assert "insufficient" in result.explanation.lower()


@pytest.mark.asyncio
async def test_confidence_validation_bounds():
    """
    Test Phase 5: Schema validates confidence strictly in [0.0, 1.0].
    """
    valid = RootCauseAnalysis(
        transaction_id="txn_123",
        root_cause=RootCauseCategory.GATEWAY_FAILURE.value,
        confidence=0.95,
        evidence=["Gateway 504 error"],
        explanation="Temporary gateway error.",
    )
    assert valid.confidence == 0.95

    # Out of bounds clamping
    clamped_high = RootCauseAnalysis(
        transaction_id="txn_123",
        root_cause=RootCauseCategory.GATEWAY_FAILURE.value,
        confidence=1.5,
        evidence=["Gateway 504 error"],
        explanation="Temporary gateway error.",
    )
    assert clamped_high.confidence == 1.0


@pytest.mark.asyncio
async def test_root_cause_api_endpoint(async_client):
    """
    Test Phase 5: GET /api/revenue-risk/transactions/{id}/root-cause returns 200 OK with valid schema.
    """
    response = await async_client.get("/api/revenue-risk/transactions/txn_4999_upi/root-cause")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["transaction_id"] == "txn_4999_upi"
    assert data["data"]["root_cause"] == "payment_method_degradation"
    assert 0.0 <= data["data"]["confidence"] <= 1.0
    assert len(data["data"]["evidence"]) >= 1


@pytest.mark.asyncio
async def test_root_cause_api_not_found(async_client):
    """
    Test Phase 5: GET with non-existent transaction returns 404.
    """
    response = await async_client.get("/api/revenue-risk/transactions/txn_non_existent_9999/root-cause")
    assert response.status_code == 404
