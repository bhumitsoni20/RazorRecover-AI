from typing import Dict, List
from pydantic import BaseModel


class FailureCategoryMetric(BaseModel):
    category: str
    total_failures: int
    predicted_correctly: int
    accuracy: float
    recovered_amount: float


class EvaluationMetricsResponse(BaseModel):
    total_transactions_analyzed: int
    total_revenue_at_risk: float
    total_revenue_recovered: float
    overall_recovery_rate: float
    root_cause_accuracy: float
    strategy_recommendation_accuracy: float
    actions_approved_by_policy: int
    actions_blocked_by_guardrails: int
    actions_requiring_human_approval: int
    avg_agent_latency_ms: int
    category_breakdown: List[FailureCategoryMetric]
    ml_roc_auc_score: float
    ml_precision: float
    ml_recall: float
    ml_f1_score: float
