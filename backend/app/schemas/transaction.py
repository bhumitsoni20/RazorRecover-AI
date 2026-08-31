from typing import List, Optional
from datetime import datetime
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
    evidence: List[str]
    recovery_probability: float
    recommended_action: str
    expected_recovery: float
    policy_decision: str
    policy_checks: List[PolicyCheckItem]
    rag_policy_reference: Optional[str] = None


class RecoveryActionBrief(BaseModel):
    id: str
    action_type: str
    reason: str
    confidence: float
    policy_decision: str
    status: str
    amount_recovered: float
    external_reference: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class TransactionListItem(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    customer_email: str
    amount: float
    currency: str
    payment_method: str
    bank: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    attempt_number: int
    risk_score: Optional[float] = None
    recovery_probability: Optional[float] = None
    loss_probability: Optional[float] = None
    revenue_at_risk: Optional[float] = None
    risk_level: Optional[str] = None  # LOW, MEDIUM, HIGH, CRITICAL
    explanation: Optional[str] = None
    ai_recommendation: Optional[str] = None
    policy_decision: Optional[str] = None
    created_at: str


class TransactionDetailResponse(BaseModel):
    id: str
    merchant_id: str
    amount: float
    currency: str
    payment_method: str
    payment_gateway: str
    bank: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    attempt_number: int
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    loss_probability: Optional[float] = None
    revenue_at_risk: Optional[float] = None
    risk_level: Optional[str] = None
    created_at: str
    updated_at: str
    customer: CustomerBrief
    investigation: Optional[AIInvestigation] = None
    recovery_actions: List[RecoveryActionBrief] = []
