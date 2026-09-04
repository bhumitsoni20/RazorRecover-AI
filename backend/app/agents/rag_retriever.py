from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.rag.vector_store import policy_vector_store
from app.schemas.rag import PolicyContextResponse, RetrievedPolicyChunk


class RAGRetrieverAgent:
    """
    Phase 6 — RAG Merchant Policy Retrieval Agent.
    Retrieves relevant sections from merchant_policy.md and uses Google Gemini
    to provide policy-grounded AI interpretations.
    """

    def __init__(self):
        self.gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models"

    async def retrieve_policy_context(
        self,
        transaction_id: str,
        root_cause: str,
        failure_reason: str | None = None,
        payment_method: str = "UPI",
        amount: float = 4999.0,
        attempt_count: int = 1,
        anomaly_info: dict[str, Any] | None = None,
    ) -> PolicyContextResponse:
        """
        Retrieves matching policy chunks and generates an explainable policy summary.
        """
        # 1. Formulate targeted search query
        query_terms = [payment_method, root_cause]
        if failure_reason:
            query_terms.append(failure_reason)
        if attempt_count > 1:
            query_terms.append("retry policy maximum attempts")
        if amount > 25000:
            query_terms.append("high value human approval threshold")
        if anomaly_info and anomaly_info.get("anomaly_detected"):
            query_terms.append("gateway degradation psp outage")

        query = " ".join(query_terms)

        # 2. Retrieve top-k chunks from vector store
        raw_results = policy_vector_store.search(query, top_k=2)

        retrieved_chunks: list[RetrievedPolicyChunk] = []
        for r in raw_results:
            retrieved_chunks.append(
                RetrievedPolicyChunk(
                    chunk_id=r.get("chunk_id"),
                    source=r.get("source", "merchant_policy.md"),
                    section=r.get("section", "General Policy"),
                    content=r.get("content", ""),
                    relevance_score=r.get("relevance_score", 0.90),
                )
            )

        # 3. Generate Policy-Grounded Interpretation via Gemini LLM
        policy_text = "\n\n".join([f"[{c.section}] {c.content}" for c in retrieved_chunks])
        ai_interpretation = await self._generate_interpretation(
            transaction_id=transaction_id,
            root_cause=root_cause,
            payment_method=payment_method,
            amount=amount,
            attempt_count=attempt_count,
            policy_context=policy_text,
        )

        if not ai_interpretation:
            # Deterministic policy summary fallback
            ai_interpretation = self._deterministic_summary(
                root_cause=root_cause,
                amount=amount,
                attempt_count=attempt_count,
                chunks=retrieved_chunks,
            )

        match_confidence = retrieved_chunks[0].relevance_score if retrieved_chunks else 0.85

        return PolicyContextResponse(
            transaction_id=transaction_id,
            query=query,
            retrieved_policies=retrieved_chunks,
            ai_interpretation=ai_interpretation,
            policy_match_confidence=match_confidence,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )

    async def _generate_interpretation(
        self,
        transaction_id: str,
        root_cause: str,
        payment_method: str,
        amount: float,
        attempt_count: int,
        policy_context: str,
    ) -> str | None:
        api_key = settings.GEMINI_API_KEY or getattr(settings, "LLM_API_KEY", "")
        if not api_key or api_key.startswith("your-") or "gemini-api-key" in api_key:
            return None

        prompt = f"""
You are the Policy RAG Agent in RazorRecover AI.
Interpret how the merchant's policy applies to this specific transaction.

Transaction Details:
- Transaction ID: {transaction_id}
- Root Cause: {root_cause}
- Payment Method: {payment_method}
- Amount: INR {amount:,.2f}
- Attempt Number: {attempt_count}

Retrieved Merchant Policy:
{policy_context}

Task:
Summarize concisely (2-3 sentences) how the merchant policy applies to this transaction.
Distinguish clearly between FACTS from the transaction and RULES from the merchant policy.
Do NOT invent rules that are not in the policy.
"""

        candidate_models = [settings.GEMINI_MODEL, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                for model_name in candidate_models:
                    url = f"{self.gemini_endpoint}/{model_name}:generateContent?key={api_key}"
                    try:
                        res = await client.post(url, json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                            if text:
                                return text
                        elif res.status_code == 404:
                            continue
                    except Exception:
                        continue
        except Exception as e:
            logger.info(f"[RAGRetrieverAgent] Gemini interpretation fallback ({e})")

        return None

    def _deterministic_summary(
        self,
        root_cause: str,
        amount: float,
        attempt_count: int,
        chunks: list[RetrievedPolicyChunk],
    ) -> str:
        if amount > 25000:
            return (
                f"According to Merchant Policy (§ High Value Transactions), this transaction amount of "
                f"INR {amount:,.2f} exceeds the INR 25,000 threshold and strictly requires human administrator approval before action dispatch."
            )
        if attempt_count >= 3:
            return (
                "According to Merchant Policy (§ Retry Policy), automated retries are capped at 2 attempts per transaction. "
                "Since this transaction is on attempt #3, further automated retries are blocked."
            )
        if "degradation" in root_cause.lower() or "timeout" in root_cause.lower():
            return (
                "According to Merchant Policy (§ UPI Failures & Gateway Degradation), technical failures during degradation "
                "permit autonomous payment link recovery with 24-hour expiry for amounts <= INR 25,000."
            )
        top_section = chunks[0].section if chunks else "General Policy"
        return f"According to Merchant Policy (§ {top_section}), recovery actions must adhere strictly to verified customer eligibility and threshold limits."


# Global singleton instance
rag_retriever_agent = RAGRetrieverAgent()
