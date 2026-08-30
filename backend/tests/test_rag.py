import pytest
from app.rag.policy_rag import policy_rag


def test_rag_chunking():
    assert len(policy_rag.chunks) >= 3
    for c in policy_rag.chunks:
        assert "chunk_id" in c
        assert "citation" in c
        assert "text" in c


def test_rag_retrieval_payment_link():
    results = policy_rag.retrieve("payment_link for upi_timeout amount 4999", top_k=2)
    assert len(results) > 0
    citation_texts = [r["citation"] for r in results]
    assert any("2.1" in cit or "Payment" in cit for cit in citation_texts)


def test_rag_retrieval_retry_limits():
    results = policy_rag.retrieve("maximum retry limit for payment failures", top_k=2)
    assert len(results) > 0
    assert any("retry" in r["text"].lower() or "retries" in r["text"].lower() for r in results)
