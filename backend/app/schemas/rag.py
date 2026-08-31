from typing import List, Optional
from pydantic import BaseModel, Field


class RetrievedPolicyChunk(BaseModel):
    chunk_id: Optional[str] = None
    source: str = Field(default="merchant_policy.md", description="Originating policy document")
    section: str = Field(..., description="Policy section title")
    content: str = Field(..., description="Full text or excerpt of retrieved policy section")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Normalized relevance score between 0.0 and 1.0")


class PolicyContextResponse(BaseModel):
    transaction_id: str
    query: str
    retrieved_policies: List[RetrievedPolicyChunk]
    ai_interpretation: str
    policy_match_confidence: float = Field(default=0.91, ge=0.0, le=1.0)
    retrieved_at: Optional[str] = None
