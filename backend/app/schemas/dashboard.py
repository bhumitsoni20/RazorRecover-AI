
from pydantic import BaseModel


class MetricSummary(BaseModel):
    revenue_at_risk: float
    recovered_revenue: float
    recovery_rate: float
    active_actions_count: int
    total_transactions_analyzed: int
    pending_human_approvals: int
    anomaly_detected: bool = False
    anomaly_message: str | None = None


class RevenueLeakageItem(BaseModel):
    category: str
    amount: float
    percentage: float
    color: str


class RecoveryTrendPoint(BaseModel):
    date: str
    revenue_at_risk: float
    revenue_recovered: float
    recovery_rate: float


class AIQueueItem(BaseModel):
    transaction_id: str
    customer_name: str
    customer_email: str
    amount: float
    currency: str
    payment_method: str
    failure_reason: str
    detected_issue: str
    ai_recommendation: str
    confidence: float
    recovery_probability: float
    expected_recovery: float
    policy_decision: str
    status: str
    created_at: str


class DashboardSummaryResponse(BaseModel):
    metrics: MetricSummary
    leakage_breakdown: list[RevenueLeakageItem]
    trend: list[RecoveryTrendPoint]
    recent_queue: list[AIQueueItem]
