
from pydantic import BaseModel


class CustomerBrief(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    lifetime_value: float


class PolicyCheckItem(BaseModel):
    name: str
    status: str  # passed, failed, warning
    detail: str


class AIInvestigation(BaseModel):
    root_cause: str
    confidence: float
    evidence: list[str]
    recovery_probability: float
    recommended_action: str
    expected_recovery: float
    policy_decision: str
    policy_checks: list[PolicyCheckItem]
    rag_policy_reference: str | None = None


class RecoveryActionBrief(BaseModel):
    id: str
    action_type: str
    reason: str
    confidence: float
    policy_decision: str
    status: str
    amount_recovered: float
    external_reference: str | None = None
    created_at: str
    completed_at: str | None = None


class TransactionListItem(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    customer_email: str
    amount: float
    currency: str
    payment_method: str
    bank: str | None = None
    status: str
    failure_reason: str | None = None
    attempt_number: int
    risk_score: float | None = None
    recovery_probability: float | None = None
    loss_probability: float | None = None
    revenue_at_risk: float | None = None
    risk_level: str | None = None  # LOW, MEDIUM, HIGH, CRITICAL
    explanation: str | None = None
    ai_recommendation: str | None = None
    policy_decision: str | None = None
    created_at: str


class TransactionDetailResponse(BaseModel):
    id: str
    merchant_id: str
    amount: float
    currency: str
    payment_method: str
    payment_gateway: str
    bank: str | None = None
    status: str
    failure_reason: str | None = None
    attempt_number: int
    razorpay_payment_id: str | None = None
    razorpay_order_id: str | None = None
    loss_probability: float | None = None
    revenue_at_risk: float | None = None
    risk_level: str | None = None
    created_at: str
    updated_at: str
    customer: CustomerBrief
    investigation: AIInvestigation | None = None
    recovery_actions: list[RecoveryActionBrief] = []
