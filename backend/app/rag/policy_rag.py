import os
import re
from typing import Any


class PolicyRAG:
    """
    RAG Policy Retrieval Engine.
    Chunks merchant recovery policy documents and performs semantic & keyword similarity matching.
    """

    def __init__(self, policy_file_path: str = "data/policies/payment_recovery_policy.md"):
        self.policy_file_path = policy_file_path
        self.chunks: list[dict[str, Any]] = []
        self._load_and_chunk_policy()

    def _load_and_chunk_policy(self):
        # Resolve absolute path relative to project root
        possible_paths = [
            self.policy_file_path,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/policies/payment_recovery_policy.md")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/policies/payment_recovery_policy.md")),
        ]

        content = ""
        for p in possible_paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
                break

        if not content:
            content = """# Payment Recovery Policy
## 2.1 Automated Payment Links (payment_link)
Payment failure caused by UPI degradation, gateway timeouts, bank network drops. Amount <= INR 25,000 for autonomous generation. Expiry: 24 hours.
## 2.2 Automated Payment Retries (retry)
Maximum autonomous retry attempts: 2 retries per transaction. Backoff: 15 mins.
## 3. Human Approval Thresholds
Amount > INR 25,000 requires HUMAN_APPROVAL_REQUIRED. Customer Risk > 0.65 requires human review. Discount > 10% requires approval.
## 4. Stopping Rules
Once webhook signals payment.captured or payment_link.paid, immediately halt retries.
"""

        # Chunk by markdown headers
        sections = re.split(r"(?=\n## |\n### )", content)
        for idx, sec in enumerate(sections):
            text = sec.strip()
            if not text:
                continue

            # Extract header citation title
            first_line = text.split("\n")[0].replace("#", "").strip()
            self.chunks.append({
                "chunk_id": f"chunk_{idx + 1:02d}",
                "citation": f"Merchant Policy § {first_line}",
                "text": text,
                "keywords": set(re.findall(r"\w+", text.lower())),
            })

    def retrieve(self, query: str, top_k: int = 2) -> list[dict[str, Any]]:
        """
        Retrieves top-k relevant policy chunks with section citations.
        """
        query_words = set(re.findall(r"\w+", query.lower()))
        scored = []

        for c in self.chunks:
            # Overlap similarity score
            overlap = len(query_words.intersection(c["keywords"]))
            # Bonus for action matches
            bonus = 0
            if "payment_link" in query and "payment link" in c["text"].lower():
                bonus += 3
            if "retry" in query and "retry" in c["text"].lower():
                bonus += 3
            if "amount" in query and ("25,000" in c["text"] or "threshold" in c["text"].lower()):
                bonus += 2

            score = overlap + bonus
            scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]


policy_rag = PolicyRAG()
