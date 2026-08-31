import pytest


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint_real_aggregation(async_client):
    """
    Test Phase 11: GET /api/dashboard/summary computes dynamic non-mock aggregations from database.
    """
    response = await async_client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    summary = data["data"]
    metrics = summary["metrics"]
    assert metrics["total_transactions_analyzed"] >= 0
    assert metrics["revenue_at_risk"] >= 0.0
    assert metrics["recovered_revenue"] >= 0.0
    assert 0.0 <= metrics["recovery_rate"] <= 100.0
    assert len(summary["leakage_breakdown"]) >= 1
    assert len(summary["trend"]) >= 1


@pytest.mark.asyncio
async def test_evaluation_metrics_endpoint_real_data(async_client):
    """
    Test Phase 12: GET /api/evaluation/metrics returns real dataset aggregations and 8 agent performance records.
    """
    response = await async_client.get("/api/evaluation/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    metrics = data["data"]
    assert metrics["total_transactions_analyzed"] >= 0
    assert metrics["total_revenue_at_risk"] >= 0.0
    assert metrics["total_revenue_recovered"] >= 0.0
    assert 0.0 <= metrics["overall_recovery_rate"] <= 100.0
    assert len(metrics["category_breakdown"]) >= 4
    assert len(metrics["agent_performance"]) >= 8

    # Verify agent performance structure
    for agent in metrics["agent_performance"]:
        assert "agent_name" in agent
        assert "display_name" in agent
        assert agent["executions"] >= 0
        assert 0.0 <= agent["avg_confidence"] <= 1.0
        assert agent["status"] == "OPERATIONAL"


@pytest.mark.asyncio
async def test_evaluation_run_e2e_endpoint(async_client):
    """
    Test Phase 12: POST /api/evaluation/run-e2e executes real 11-step pipeline.
    """
    payload = {"transaction_id": "txn_4999_upi"}
    response = await async_client.post("/api/evaluation/run-e2e", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    e2e = data["data"]
    assert e2e["overall_status"] == "PASS"
    assert e2e["total_latency_ms"] > 0
    assert e2e["transaction_id"] == "txn_4999_upi"
    assert len(e2e["steps"]) == 11

    # Verify all 11 steps passed
    step_names = [s["step_name"] for s in e2e["steps"]]
    assert "Revenue Risk Detection" in step_names
    assert "Root Cause Analysis" in step_names
    assert "Policy RAG Retrieval" in step_names
    assert "ML Recovery Probability" in step_names
    assert "Strategy Selection" in step_names
    assert "Deterministic Guardrails" in step_names
    assert "Razorpay Test Mode Execution" in step_names
    assert "Webhook Ingestion" in step_names
    assert "HMAC-SHA256 Signature Verification" in step_names
    assert "Transaction Status Update" in step_names
    assert "Audit Trail Sealing" in step_names

    for s in e2e["steps"]:
        assert s["status"] == "PASS"
        assert s["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_evaluation_run_guardrails_endpoint(async_client):
    """
    Test Phase 12: POST /api/evaluation/run-guardrails executes 7 automated boundary test cases.
    """
    response = await async_client.post("/api/evaluation/run-guardrails")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    suite = data["data"]
    assert suite["total_cases"] == 7
    assert suite["passed_cases"] == 7
    assert suite["failed_cases"] == 0
    assert suite["all_passed"] is True

    case_ids = [c["case_id"] for c in suite["results"]]
    assert "CASE_1" in case_ids
    assert "CASE_2" in case_ids
    assert "CASE_3" in case_ids
    assert "CASE_4" in case_ids
    assert "CASE_5" in case_ids
    assert "CASE_6" in case_ids
    assert "CASE_7" in case_ids
