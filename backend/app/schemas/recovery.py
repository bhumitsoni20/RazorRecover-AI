from typing import List, Optional
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    transaction_id: Optional[str] = None
    include_rag_evidence: bool = True


class AnalyzeResponse(BaseModel):
    transaction_id: str
    root_cause: str
    confidence: float
    evidence: List[str]
    recovery_probability: float
    recommended_action: str
    expected_recovery: float
    policy_decision: str
    guardrails_passed: bool
    policy_details: List[str]
    rag_policy_reference: Optional[str] = None
    rag_retrieval_excerpt: Optional[str] = None


class ExecuteRequest(BaseModel):
    transaction_id: Optional[str] = None
    action_type: Optional[str] = None
    override_reason: Optional[str] = None


class ExecuteResponse(BaseModel):
    transaction_id: str
    action_id: str
    action_type: str
    status: str
    razorpay_payment_link: Optional[str] = None
    razorpay_reference_id: Optional[str] = None
    policy_verdict: str
    message: str
    timeline_steps: List[dict] = []


class ApproveRequest(BaseModel):
    transaction_id: Optional[str] = None
    approved: bool = True
    approver_note: Optional[str] = None


class ApproveResponse(BaseModel):
    transaction_id: str
    action_id: str
    status: str
    message: str


class RecoveryActionItem(BaseModel):
    id: str
    transaction_id: str
    customer_name: str
    amount: float
    currency: str
    action_type: str
    reason: str
    confidence: float
    policy_decision: str
    status: str
    amount_recovered: float
    external_reference: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
