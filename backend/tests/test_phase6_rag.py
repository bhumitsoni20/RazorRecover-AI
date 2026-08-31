import pytest
from app.rag.vector_store import policy_vector_store, PolicyVectorStore
from app.agents.rag_retriever import rag_retriever_agent
from app.agents.workflow import MultiAgentWorkflow
from app.schemas.rag import PolicyContextResponse


def test_policy_document_loaded_and_chunked():
    """
    Test Phase 6: merchant_policy.md exists, is parsed into structured chunks with metadata.
    """
    assert len(policy_vector_store.chunks) >= 4
    sections = [c.section for c in policy_vector_store.chunks]
    assert any("UPI" in s for s in sections)
    assert any("Retry" in s for s in sections)
    assert any("High Value" in s for s in sections)

    for chunk in policy_vector_store.chunks:
        assert chunk.source.endswith(".md")
        assert len(chunk.content) > 20
        assert chunk.chunk_id.startswith("chunk_")


def test_upi_failure_retrieval():
    """
    Test Phase 6: Query for UPI degradation retrieves UPI Failures as top section.
    """
    results = policy_vector_store.search("UPI temporary degradation timeout retry policy", top_k=2)
    assert len(results) >= 1
    top_result = results[0]
    assert "UPI" in top_result["section"] or "Gateway" in top_result["section"]
    assert 0.0 <= top_result["relevance_score"] <= 1.0
    assert top_result["source"] == "merchant_policy.md"


def test_high_value_retrieval():
    """
    Test Phase 6: Query for high amount > 25,000 retrieves High Value Transactions section.
    """
    results = policy_vector_store.search("transaction amount 50000 high value human review approval threshold", top_k=2)
    assert len(results) >= 1
    sections = [r["section"] for r in results]
    assert any("High Value" in s or "Escalation" in s for s in sections)


def test_retry_policy_retrieval():
    """
    Test Phase 6: Query for maximum retry attempts retrieves Retry Policy section.
    """
    results = policy_vector_store.search("maximum retry attempts backoff stopping rule", top_k=2)
    assert len(results) >= 1
    sections = [r["section"] for r in results]
    assert any("Retry" in s for s in sections)


@pytest.mark.asyncio
async def test_rag_retriever_agent_context_generation():
    """
    Test Phase 6: RAGRetrieverAgent generates policy-grounded interpretation.
    """
    res = await rag_retriever_agent.retrieve_policy_context(
        transaction_id="txn_4999_upi",
        root_cause="payment_method_degradation",
        failure_reason="upi_timeout",
        payment_method="UPI",
        amount=4999.0,
        attempt_count=1,
    )

    assert isinstance(res, PolicyContextResponse)
    assert res.transaction_id == "txn_4999_upi"
    assert len(res.retrieved_policies) >= 1
    assert res.ai_interpretation is not None
    assert "Merchant Policy" in res.ai_interpretation or "policy" in res.ai_interpretation.lower()


@pytest.mark.asyncio
async def test_policy_context_api_endpoint(async_client):
    """
    Test Phase 6: GET /api/revenue-risk/transactions/{id}/policy-context returns 200 OK.
    """
    response = await async_client.get("/api/revenue-risk/transactions/txn_4999_upi/policy-context")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["transaction_id"] == "txn_4999_upi"
    assert len(data["data"]["retrieved_policies"]) >= 1
    assert "source" in data["data"]["retrieved_policies"][0]
    assert "section" in data["data"]["retrieved_policies"][0]


@pytest.mark.asyncio
async def test_multi_agent_workflow_phase5_and_6_integration():
    """
    Test Phase 5 + 6: MultiAgentWorkflow coordinates Root Cause and RAG Policy Retrieval.
    """
    wf_result = await MultiAgentWorkflow.run(
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

    assert wf_result["transaction_id"] == "txn_4999_upi"
    assert wf_result["root_cause"] == "payment_method_degradation"
    assert len(wf_result["evidence"]) >= 1
    assert len(wf_result["policy_references"]) >= 1
    assert any("Merchant Policy" in p for p in wf_result["policy_references"])
