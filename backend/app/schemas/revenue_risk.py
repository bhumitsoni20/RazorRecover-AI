from pydantic import BaseModel


class AnomalyItem(BaseModel):
    anomaly_type: str
    payment_method: str
    baseline_rate: float
    current_rate: float
    spike_multiplier: float
    recent_failed_count: int | None = None
    recent_total_count: int | None = None
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str


class RiskSourceBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float
    transaction_count: int
    color: str


class RevenueRiskSummaryResponse(BaseModel):
    total_revenue_at_risk: float
    total_gross_failed_volume: float
    currency: str
    transaction_count: int
    average_loss_probability: float
    risk_distribution: dict[str, int]
    top_risk_sources: list[RiskSourceBreakdown]
    anomaly_detected: bool
    anomaly_message: str | None = None
    anomalies: list[AnomalyItem] = []
    calculated_at: str


class TransactionRiskItem(BaseModel):
    transaction_id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    bank: str | None = None
    customer_name: str
    customer_email: str
    failure_reason: str | None = None
    attempt_number: int
    loss_probability: float
    successful_recovery_probability: float
    revenue_at_risk: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    explanation: str
    created_at: str


class PaginatedTransactionRiskResponse(BaseModel):
    items: list[TransactionRiskItem]
    total: int
    page: int
    limit: int
    total_pages: int


class RevenueRiskItem(BaseModel):
    id: str
    transaction_id: str
    amount: float
    currency: str
    customer_name: str
    payment_method: str
    risk_type: str
    risk_score: float
    detected_reason: str
    recovery_probability: float
    expected_recovery: float
    status: str
    created_at: str
