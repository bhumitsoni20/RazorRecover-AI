
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    transaction_id: str | None = None
    include_rag_evidence: bool = True


class AnalyzeResponse(BaseModel):
    transaction_id: str
    root_cause: str
    confidence: float
    evidence: list[str]
    recovery_probability: float
    recommended_action: str
    expected_recovery: float
    policy_decision: str
    guardrails_passed: bool
    policy_details: list[str]
    rag_policy_reference: str | None = None
    rag_retrieval_excerpt: str | None = None


class ExecuteRequest(BaseModel):
    transaction_id: str | None = None
    action_type: str | None = None
    override_reason: str | None = None


class ExecuteResponse(BaseModel):
    transaction_id: str
    action_id: str
    action_type: str
    status: str
    razorpay_payment_link: str | None = None
    razorpay_reference_id: str | None = None
    policy_verdict: str
    message: str
    timeline_steps: list[dict] = []


class ApproveRequest(BaseModel):
    transaction_id: str | None = None
    approved: bool = True
    approver_note: str | None = None


class ApproveResponse(BaseModel):
    transaction_id: str
    action_id: str
    status: str
    razorpay_payment_link: str | None = None
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
    external_reference: str | None = None
    created_at: str
    completed_at: str | None = None
