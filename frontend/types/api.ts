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

export interface AgentStatusCard {
  name: string;
  role: string;
  status: "active" | "idle" | "degraded";
  total_runs: number;
  success_rate: number;
  avg_latency_ms: number;
  last_run_at: string;
}

export interface AgentRunItem {
  id: string;
  transaction_id?: string;
  agent_name: string;
  status: string;
  started_at: string;
  completed_at?: string;
  latency_ms: number;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
}

export interface AgentsOverviewResponse {
  agents: AgentStatusCard[];
  recent_runs: AgentRunItem[];
}

export interface FailureCategoryMetric {
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
  category_breakdown: FailureCategoryMetric[];
  ml_roc_auc_score: number;
  ml_precision: number;
  ml_recall: number;
  ml_f1_score: number;
}
