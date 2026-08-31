import os
import re
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.logging import logger


class PolicyChunk:
    def __init__(
        self,
        chunk_id: str,
        source: str,
        section: str,
        content: str,
        keywords: Optional[List[str]] = None,
    ):
        self.chunk_id = chunk_id
        self.source = source
        self.section = section
        self.content = content
        self.keywords = keywords or []

    def to_dict(self, relevance_score: float = 0.0) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "section": self.section,
            "content": self.content,
            "relevance_score": round(float(relevance_score), 3),
        }


class PolicyVectorStore:
    """
    Hybrid Vector & Keyword Policy Retrieval Engine.
    Combines TF-IDF semantic embeddings with keyword matching for exact merchant recovery policies.
    """

    def __init__(self, policy_dir: Optional[str] = None):
        if policy_dir:
            self.policy_dir = policy_dir
        else:
            # Look in standard project data/policies/ directories
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/policies"))
            if not os.path.exists(base_dir):
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/policies"))
            self.policy_dir = base_dir

        self.chunks: List[PolicyChunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.load_and_index()

    def load_and_index(self):
        """Loads policy markdown files, chunks by header, and indexes for hybrid search."""
        self.chunks = []
        target_files = []

        if os.path.exists(self.policy_dir):
            for fname in os.listdir(self.policy_dir):
                if fname.endswith(".md"):
                    target_files.append(os.path.join(self.policy_dir, fname))

        # Always index merchant_policy.md if available
        merchant_policy_file = [f for f in target_files if "merchant_policy.md" in f]
        if merchant_policy_file:
            for filepath in merchant_policy_file:
                self._index_file(filepath)
        elif target_files:
            for filepath in target_files:
                self._index_file(filepath)

        if not self.chunks:
            logger.warning(f"No policy markdown files found in {self.policy_dir}. Using embedded defaults.")
            self._load_default_chunks()

        # Build TF-IDF semantic matrix
        corpus = [c.content for c in self.chunks]
        if corpus:
            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                lowercase=True,
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            logger.info(f"[PolicyVectorStore] Indexed {len(self.chunks)} policy chunks from merchant_policy.md.")

    def _index_file(self, filepath: str):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_text = f.read()

            source_name = "merchant_policy.md" if "merchant_policy" in filepath else os.path.basename(filepath)
            # Split markdown by H2 or H3 headers
            raw_sections = re.split(r"(?=\n## |\n### )", raw_text)

            for idx, sec in enumerate(raw_sections):
                text = sec.strip()
                if not text or len(text) < 20:
                    continue

                lines = text.split("\n")
                header_line = lines[0].replace("#", "").strip()
                # Clean section title
                section_title = re.sub(r"^\d+[\.\)]?\s*", "", header_line).strip()

                chunk_id = f"chunk_{idx + 1:02d}_{re.sub(r'[^a-zA-Z0-9_]', '_', section_title.lower())}"
                keywords = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower())

                self.chunks.append(
                    PolicyChunk(
                        chunk_id=chunk_id,
                        source=source_name,
                        section=section_title or "General Policy",
                        content=text,
                        keywords=keywords,
                    )
                )
        except Exception as e:
            logger.error(f"Error indexing policy file {filepath}: {e}")

    def _load_default_chunks(self):
        defaults = [
            ("Scope & Purpose", "This policy document establishes standard operating rules for autonomous revenue recovery in merchant checkout operations."),
            ("UPI Failures", "When UPI payment failures occur during an active PSP degradation window, automated direct retries are suspended. For orders <= INR 25,000, autonomous generation of a secure payment link with 24hr expiry is permitted for customers with >= 60% historical success rate."),
            ("Gateway Degradation", "If payment failures occur due to gateway timeouts or bank downtime, record as technical degradation. If failure rate exceeds 25% over 15 minutes, pause direct API retries immediately."),
            ("Retry Policy", "A maximum of 2 automated retries is permitted per transaction. Minimum backoff for Retry #1 is 15 minutes, and Retry #2 is 60 minutes. Transactions on attempt #3 or greater are strictly BLOCKED. Halt retries upon payment capture webhook."),
            ("Alternative Payment Methods", "If Card fails due to OTP timeout, recommend UPI Deep-Link. If UPI fails due to bank degradation, recommend NetBanking or Card checkout options."),
            ("High Value Transactions", "Any transaction with gross amount > INR 25,000 is classified as High Value. Autonomous execution is prohibited and requires HUMAN_APPROVAL_REQUIRED by Merchant Admin."),
            ("Customer History", "Customers with historical success rate >= 80% and lifetime value >= INR 20,000 are eligible for accelerated autonomous recovery."),
            ("Escalation & Audit", "Transactions exceeding INR 25,000 or with low AI confidence (< 0.70) must be routed to human review. All AI diagnoses and policy matches must be logged immutably."),
        ]
        for idx, (sec, content) in enumerate(defaults):
            self.chunks.append(
                PolicyChunk(
                    chunk_id=f"default_chunk_{idx+1:02d}",
                    source="merchant_policy.md",
                    section=sec,
                    content=f"## {sec}\n{content}",
                    keywords=re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", content.lower()),
                )
            )

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs hybrid semantic similarity + keyword boosted retrieval.
        Returns top-k chunks with relevance scores between 0.0 and 1.0.
        """
        if not self.chunks or not query:
            return []

        query_lower = query.lower()
        query_words = set(re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query_lower))

        # 1. Semantic TF-IDF Cosine Similarity
        semantic_scores = np.zeros(len(self.chunks))
        if self.vectorizer and self.tfidf_matrix is not None:
            try:
                query_vec = self.vectorizer.transform([query])
                cosine_sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                semantic_scores = np.nan_to_num(cosine_sims)
            except Exception as e:
                logger.warning(f"TF-IDF similarity error: {e}")

        # 2. Keyword & Rule-Based Domain Boosting
        results = []
        for idx, chunk in enumerate(self.chunks):
            content_lower = chunk.content.lower()
            section_lower = chunk.section.lower()

            # Overlap score
            overlap_count = sum(1 for w in query_words if w in content_lower)
            keyword_score = min(overlap_count / max(len(query_words), 1), 1.0)

            # Specific domain keyword bonuses
            bonus = 0.0
            if "upi" in query_lower and "upi" in section_lower:
                bonus += 0.35
            if ("retry" in query_lower or "attempt" in query_lower) and "retry" in section_lower:
                bonus += 0.35
            if ("high_value" in query_lower or "high value" in query_lower or "25000" in query_lower or "25,000" in query_lower or "human" in query_lower) and ("high value" in section_lower or "escalation" in section_lower):
                bonus += 0.40
            if "degradation" in query_lower and ("degradation" in section_lower or "upi" in section_lower):
                bonus += 0.35
            if any(w in section_lower for w in query_words if len(w) > 3):
                bonus += 0.15

            # Hybrid blend: 40% Semantic + 30% Keyword + 30% Domain Boost
            combined = (0.40 * semantic_scores[idx]) + (0.30 * keyword_score) + bonus
            # Scale to 0.0 - 0.99 range
            final_score = min(max(round(float(combined), 3), 0.10), 0.98)
            results.append((final_score, chunk))

        # Sort descending by score
        results.sort(key=lambda x: x[0], reverse=True)
        top_results = results[:top_k]

        return [chunk.to_dict(relevance_score=score) for score, chunk in top_results]


# Global singleton instance
policy_vector_store = PolicyVectorStore()
