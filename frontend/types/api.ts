export interface APIResponse<T> {
  success: boolean;
  message?: string;
  data: T;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface MetricSummary {
  revenue_at_risk: number;
  recovered_revenue: number;
  recovery_rate: number;
  active_actions_count: number;
  total_transactions_analyzed: number;
  pending_human_approvals: number;
  anomaly_detected: boolean;
  anomaly_message?: string;
}

export interface RevenueLeakageItem {
  category: string;
  amount: number;
  percentage: number;
  color: string;
}

export interface RecoveryTrendPoint {
  date: string;
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
}

export interface AIQueueItem {
  transaction_id: string;
  customer_name: string;
  customer_email: string;
  amount: number;
  currency: string;
  payment_method: string;
  failure_reason: string;
  detected_issue: string;
  ai_recommendation: string;
  confidence: number;
  recovery_probability: number;
  expected_recovery: number;
  policy_decision: string;
  status: string;
  created_at: string;
}

export interface DashboardSummaryResponse {
  metrics: MetricSummary;
  leakage_breakdown: RevenueLeakageItem[];
  trend: RecoveryTrendPoint[];
  recent_queue: AIQueueItem[];
}

export interface CustomerBrief {
  id: string;
  name: string;
  email: string;
  phone: string;
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  lifetime_value: number;
}

export interface PolicyCheckItem {
  name: string;
  status: "passed" | "failed" | "warning";
  detail: string;
}

export interface AIInvestigation {
  root_cause: string;
  confidence: number;
  evidence: string[];
  recovery_probability: number;
  recommended_action: string;
  expected_recovery: number;
  policy_decision: string;
  policy_checks: PolicyCheckItem[];
  rag_policy_reference?: string;
}

export interface RecoveryActionBrief {
  id: string;
  action_type: string;
  reason: string;
  confidence: number;
  policy_decision: string;
  status: string;
  amount_recovered: number;
  external_reference?: string;
  created_at: string;
  completed_at?: string;
}

export interface TransactionListItem {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  amount: number;
  currency: string;
  payment_method: string;
  bank?: string;
  status: string;
  failure_reason?: string;
  attempt_number: number;
  risk_score?: number;
  recovery_probability?: number;
  loss_probability?: number;
  revenue_at_risk?: number;
  risk_level?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  explanation?: string;
  ai_recommendation?: string;
  policy_decision?: string;
  created_at: string;
}

export interface TransactionDetailResponse {
  id: string;
  merchant_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  payment_gateway: string;
  bank?: string;
  status: string;
  failure_reason?: string;
  attempt_number: number;
  razorpay_payment_id?: string;
  razorpay_order_id?: string;
  loss_probability?: number;
  revenue_at_risk?: number;
  risk_level?: string;
  created_at: string;
  updated_at: string;
  customer: CustomerBrief;
  investigation?: AIInvestigation;
  recovery_actions: RecoveryActionBrief[];
}

export interface RecoveryActionItem {
  id: string;
  transaction_id: string;
  customer_name: string;
  amount: number;
  currency: string;
  action_type: string;
  reason: string;
  confidence: number;
  policy_decision: string;
  status: string;
  amount_recovered: number;
  external_reference?: string;
  created_at: string;
  completed_at?: string;
}

export interface AuditLogItem {
  id: string;
  transaction_id?: string;
  agent_name: string;
  action: string;
  reasoning_summary: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  policy_result?: string;
  created_at: string;
}

export interface AgentRunItem {
  id: string;
  agent_name: string;
  transaction_id: string;
  status: "success" | "failed" | "skipped";
  latency_ms: number;
  trigger?: string;
  tokens_used?: number;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
}

export interface AgentStatusCard {
  name: string;
  role: string;
  status: "active" | "idle" | "degraded";
  total_runs: number;
  success_rate: number;
  avg_latency_ms: number;
  last_active?: string;
  last_run_at?: string;
  specialization?: string;
}

export interface AgentsOverviewResponse {
  agents: AgentStatusCard[];
  recent_runs: AgentRunItem[];
  system_health?: {
    status: "HEALTHY" | "DEGRADED" | "CRITICAL";
    active_guardrails: number;
    rag_retrieval_latency_ms: number;
    audit_chain_verified: boolean;
    gemini_connected: boolean;
  };
}

export interface CategoryAccuracyBreakdown {
  category: string;
  total_failures: number;
  predicted_correctly: number;
  accuracy: number;
  recovered_amount: number;
}

export interface EvaluationMetricsResponse {
  total_transactions_analyzed: number;
  total_revenue_at_risk: number;
  total_revenue_recovered: number;
  overall_recovery_rate: number;
  root_cause_accuracy: number;
  strategy_recommendation_accuracy: number;
  actions_approved_by_policy: number;
  actions_blocked_by_guardrails: number;
  actions_requiring_human_approval: number;
  avg_agent_latency_ms: number;
  recovery_attempts?: number;
  successful_recoveries?: number;
  avg_recovery_probability?: number;
  category_breakdown: CategoryAccuracyBreakdown[];
  agent_performance?: AgentPerformanceMetric[];
  ml_roc_auc_score: number;
  ml_precision: number;
  ml_recall: number;
  ml_f1_score: number;
}

export interface AgentPerformanceMetric {
  agent_name: string;
  display_name: string;
  description: string;
  executions: number;
  success_count: number;
  error_count: number;
  avg_confidence: number;
  avg_latency_ms: number;
  status: string;
}

export interface EndToEndStepResult {
  step_number: number;
  step_name: string;
  agent_name: string;
  status: "PASS" | "FAIL" | string;
  latency_ms: number;
  summary: string;
  details: Record<string, any>;
}

export interface EndToEndEvaluationResponse {
  overall_status: "PASS" | "FAIL" | string;
  total_latency_ms: number;
  transaction_id: string;
  amount: number;
  currency: string;
  recovery_link?: string;
  recovered_amount: number;
  steps: EndToEndStepResult[];
  timestamp: string;
}

export interface GuardrailTestCaseResult {
  case_id: string;
  name: string;
  scenario: string;
  expected_verdict: string;
  actual_verdict: string;
  passed: boolean;
  detail: string;
}

export interface GuardrailTestSuiteResponse {
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  all_passed: boolean;
  results: GuardrailTestCaseResult[];
  timestamp: string;
}

export interface AnomalyItem {
  anomaly_type: string;
  payment_method: string;
  baseline_rate: number;
  current_rate: number;
  spike_multiplier: number;
  recent_failed_count?: number;
  recent_total_count?: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  message: string;
}

export interface RiskSourceBreakdown {
  category: string;
  amount: number;
  percentage: number;
  transaction_count: number;
  color: string;
}

export interface RevenueRiskSummaryResponse {
  total_revenue_at_risk: number;
  total_gross_failed_volume: number;
  currency: string;
  transaction_count: number;
  average_loss_probability: number;
  risk_distribution: Record<string, number>;
  top_risk_sources: RiskSourceBreakdown[];
  anomaly_detected: boolean;
  anomaly_message?: string;
  anomalies: AnomalyItem[];
  calculated_at: string;
}

export interface RootCauseResponse {
  transaction_id: string;
  root_cause: string;
  confidence: number;
  evidence: string[];
  explanation: string;
  signals_analyzed?: Record<string, any>;
  analyzed_at?: string;
}

export interface RetrievedPolicyChunk {
  chunk_id?: string;
  source: string;
  section: string;
  content: string;
  relevance_score: number;
}

export interface PolicyContextResponse {
  transaction_id: string;
  query: string;
  retrieved_policies: RetrievedPolicyChunk[];
  ai_interpretation: string;
  policy_match_confidence: number;
  retrieved_at?: string;
}
