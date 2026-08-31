from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class FailureCategoryMetric(BaseModel):
    category: str
    total_failures: int
    predicted_correctly: int
    accuracy: float
    recovered_amount: float


class AgentPerformanceMetric(BaseModel):
    agent_name: str
    display_name: str
    description: str
    executions: int
    success_count: int
    error_count: int
    avg_confidence: float
    avg_latency_ms: int
    status: str


class EndToEndStepResult(BaseModel):
    step_number: int
    step_name: str
    agent_name: str
    status: str  # "PASS" | "FAIL"
    latency_ms: int
    summary: str
    details: Dict[str, Any]


class EndToEndEvaluationResponse(BaseModel):
    overall_status: str  # "PASS" | "FAIL"
    total_latency_ms: int
    transaction_id: str
    amount: float
    currency: str
    recovery_link: Optional[str] = None
    recovered_amount: float = 0.0
    steps: List[EndToEndStepResult]
    timestamp: str


class GuardrailTestCaseResult(BaseModel):
    case_id: str
    name: str
    scenario: str
    expected_verdict: str
    actual_verdict: str
    passed: bool
    detail: str


class GuardrailTestSuiteResponse(BaseModel):
    total_cases: int
    passed_cases: int
    failed_cases: int
    all_passed: bool
    results: List[GuardrailTestCaseResult]
    timestamp: str


class EvaluationMetricsResponse(BaseModel):
    total_transactions_analyzed: int
    total_revenue_at_risk: float
    total_revenue_recovered: float
    overall_recovery_rate: float
    recovery_attempts: int
    successful_recoveries: int
    avg_recovery_probability: float
    root_cause_accuracy: float
    strategy_recommendation_accuracy: float
    actions_approved_by_policy: int
    actions_blocked_by_guardrails: int
    actions_requiring_human_approval: int
    avg_agent_latency_ms: int
    category_breakdown: List[FailureCategoryMetric]
    agent_performance: List[AgentPerformanceMetric]
    ml_roc_auc_score: float
    ml_precision: float
    ml_recall: float
    ml_f1_score: float
