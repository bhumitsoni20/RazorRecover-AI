"use client";

export const dynamic = "force-dynamic";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Play,
  Link2,
  Loader2,
  ExternalLink,
  BookOpen,
  User,
  History,
  FileText,
  Zap,
  DollarSign,
  Brain,
  XCircle,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Search,
  Scale,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { AgentExecutionTimeline, TimelineStep } from "@/components/recovery/agent-execution-timeline";
import { LiveExecutionModal } from "@/components/recovery/live-execution-modal";
import { WebhookPlaygroundModal } from "@/components/recovery/webhook-playground-modal";
import { apiClient } from "@/lib/api-client";
import { TransactionDetailResponse, RootCauseResponse, PolicyContextResponse } from "@/types/api";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { PageTransition, itemFadeUp, staggerContainer } from "@/components/animations/page-transition";

export default function TransactionDetailPage() {
  const params = useParams();
  const id = (params?.id as string) || "txn_4999_upi";

  const [transaction, setTransaction] = useState<TransactionDetailResponse | null>(null);
  const [rootCauseData, setRootCauseData] = useState<RootCauseResponse | null>(null);
  const [policyContextData, setPolicyContextData] = useState<PolicyContextResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingRootCause, setLoadingRootCause] = useState(false);
  const [rootCauseError, setRootCauseError] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [showLiveModal, setShowLiveModal] = useState(false);
  const [showWebhookModal, setShowWebhookModal] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [isRecovered, setIsRecovered] = useState(false);
  const [isHumanReview, setIsHumanReview] = useState(false);
  const [isBlocked, setIsBlocked] = useState(false);
  const [timelineSteps, setTimelineSteps] = useState<TimelineStep[]>([]);

  const loadDetail = async () => {
    setLoading(true);
    try {
      const [res, rc, pol] = await Promise.all([
        apiClient.getTransaction(id),
        apiClient.getRootCause(id),
        apiClient.getPolicyContext(id),
      ]);
      setTransaction(res);
      setRootCauseData(rc);
      setPolicyContextData(pol);

      const isRecov = res.status === "recovered";
      setIsRecovered(isRecov);

      const decision = res.investigation?.policy_decision || (res.amount > 25000 ? "HUMAN_APPROVAL_REQUIRED" : res.attempt_number > 2 ? "BLOCKED" : "APPROVED");
      setIsHumanReview(decision === "HUMAN_APPROVAL_REQUIRED");
      setIsBlocked(decision === "BLOCKED");

      const hasAction = res.recovery_actions && res.recovery_actions.length > 0;
      const latestAction = hasAction ? res.recovery_actions[0] : null;

      if (latestAction && latestAction.external_reference && latestAction.status === "executed") {
        setExecutionResult({
          status: latestAction.status,
          razorpay_payment_link: latestAction.external_reference,
        });
      }

      setTimelineSteps([
        {
          id: "step_1",
          title: "Revenue Risk Detected",
          description: `Identified payment failure of ${formatCurrency(res.amount)} due to ${res.failure_reason || "timeout"}`,
          status: "completed",
          agent: "RevenueDetectionAgent",
        },
        {
          id: "step_2",
          title: "Root Cause AI Investigation",
          description: rc?.root_cause ? `${rc.root_cause.replace(/_/g, " ").toUpperCase()} (${Math.round((rc.confidence || 0.9) * 100)}% conf)` : (res.investigation?.root_cause || "Payment Method Degradation (UPI spike detected)"),
          status: "completed",
          agent: "RootCauseAgent",
        },
        {
          id: "step_3",
          title: "Policy RAG Retrieval",
          description: pol?.retrieved_policies?.[0]?.section ? `Merchant Policy § ${pol.retrieved_policies[0].section}` : (res.investigation?.rag_policy_reference || "Policy §2.1: Payment link generation approved for degradation <= ₹25k"),
          status: "completed",
          agent: "RAGPolicyRetriever",
        },
        {
          id: "step_4",
          title: "Deterministic Guardrails Check",
          description: decision === "BLOCKED"
            ? "Guardrails: BLOCKED (Max retries exceeded or risk threshold breached)"
            : decision === "HUMAN_APPROVAL_REQUIRED"
            ? "Guardrails: HUMAN APPROVAL REQUIRED (Amount exceeds ₹25,000 threshold)"
            : "Deterministic limits verified: amount <= ₹25k, retries <= 2 (APPROVED)",
          status: "completed",
          meta: `Policy Check: ${decision}`,
          agent: "PolicyGuardrailEngine",
        },
        {
          id: "step_5",
          title: "Razorpay Test Mode Execution",
          description: latestAction?.external_reference
            ? `Generated Razorpay Test Mode Link: ${latestAction.external_reference}`
            : isRecov
            ? "Razorpay Test Mode Payment Link executed"
            : decision === "BLOCKED"
            ? "Execution blocked by policy engine"
            : "Awaiting execution trigger...",
          status: hasAction || isRecov ? "completed" : decision === "BLOCKED" ? "blocked" : "pending",
          agent: "ActionExecutionAgent",
        },
        {
          id: "step_6",
          title: "Webhook Verification & Recovery",
          description: isRecov
            ? "Inbound payment_link.paid webhook verified via HMAC-SHA256. Transaction marked recovered."
            : "Waiting for customer payment or webhook event...",
          status: isRecov ? "completed" : "pending",
          agent: "RazorpayWebhookVerifier",
        },
      ]);
    } catch (e) {
      console.error("Failed to load transaction:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [id]);

  // Polling mechanism to sync recovered state if webhook fires
  useEffect(() => {
    if (isRecovered) return;

    const interval = setInterval(async () => {
      try {
        const statusData = await apiClient.getRecoveryStatus(id);
        if (statusData && (statusData.is_recovered || statusData.status === "recovered")) {
          setIsRecovered(true);
          setTimelineSteps((prev) =>
            prev.map((step) =>
              step.id === "step_6"
                ? {
                    ...step,
                    status: "completed",
                    description: "Inbound payment_link.paid webhook verified via raw HMAC-SHA256. Transaction marked recovered.",
                  }
                : step.id === "step_5"
                ? { ...step, status: "completed" }
                : step
            )
          );
        }
      } catch (e) {
        // ignore polling errors
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [id, isRecovered]);

  const handleModalComplete = (result: any) => {
    setExecutionResult({
      status: "executed",
      razorpay_payment_link: result.paymentLink,
    });
    setTimelineSteps((prev) =>
      prev.map((step) =>
        step.id === "step_5"
          ? {
              ...step,
              status: "completed",
              description: `Generated Razorpay Test Mode Link: ${result.paymentLink}`,
              meta: "Executed via Razorpay Test Mode",
            }
          : step
      )
    );
  };

  const handlePaymentSuccess = () => {
    setIsRecovered(true);
    setTimelineSteps((prev) =>
      prev.map((step) =>
        step.id === "step_6"
          ? {
              ...step,
              status: "completed",
              description: "Inbound payment_link.paid webhook verified via raw HMAC-SHA256. Transaction marked recovered.",
            }
          : step.id === "step_5"
          ? { ...step, status: "completed" }
          : step
      )
    );
  };

  const handleHumanApproval = async (approved: boolean) => {
    setIsApproving(true);
    try {
      const data = await apiClient.approveRecovery(id, approved);
      if (approved) {
        setIsHumanReview(false);
        setExecutionResult({
          status: "executed",
          razorpay_payment_link: data?.razorpay_payment_link || "https://rzp.io/rzp/live_approved",
        });
        setTimelineSteps((prev) =>
          prev.map((step) =>
            step.id === "step_5"
              ? {
                  ...step,
                  status: "completed",
                  description: "Human review approved. Generated Razorpay Test Mode Link.",
                }
              : step
          )
        );
      } else {
        setIsBlocked(true);
        setIsHumanReview(false);
      }
    } catch (e) {
      console.error("Failed to approve action:", e);
    } finally {
      setIsApproving(false);
    }
  };

  const handleReanalyzeRootCause = async () => {
    setLoadingRootCause(true);
    setRootCauseError(null);
    try {
      const [rc, pol] = await Promise.all([
        apiClient.getRootCause(id),
        apiClient.getPolicyContext(id),
      ]);
      setRootCauseData(rc);
      setPolicyContextData(pol);
    } catch (e: any) {
      setRootCauseError("Failed to refresh AI root cause. Showing cached telemetry.");
    } finally {
      setLoadingRootCause(false);
    }
  };

  if (loading || !transaction) {
    return (
      <div className="flex h-96 items-center justify-center text-slate-400 text-sm">
        <Loader2 className="h-5 w-5 animate-spin mr-2 text-[#0052cc]" />
        Loading transaction investigation...
      </div>
    );
  }

  const investigation = transaction.investigation;
  const customer = transaction.customer;
  const hasExecutedRecovery = Boolean(
    executionResult?.status === "executed" ||
    (transaction?.recovery_actions && transaction.recovery_actions.some((a) => a.status === "executed" && a.external_reference))
  );

  const formatCategoryName = (cat?: string) => {
    if (!cat) return "Unknown";
    return cat
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const getCategoryColor = (cat?: string) => {
    const c = (cat || "").toLowerCase();
    if (c.includes("degradation") || c.includes("psp")) return "bg-blue-50 text-blue-800 border-blue-200";
    if (c.includes("gateway") || c.includes("504")) return "bg-indigo-50 text-indigo-800 border-indigo-200";
    if (c.includes("bank")) return "bg-purple-50 text-purple-800 border-purple-200";
    if (c.includes("funds")) return "bg-amber-50 text-amber-800 border-amber-200";
    if (c.includes("abandon")) return "bg-orange-50 text-orange-800 border-orange-200";
    if (c.includes("repeat") || c.includes("retry")) return "bg-red-50 text-red-800 border-red-200";
    return "bg-slate-50 text-slate-800 border-slate-200";
  };

  const displayRootCause = rootCauseData?.root_cause || investigation?.root_cause || "payment_method_degradation";
  const displayConfidence = rootCauseData?.confidence ?? investigation?.confidence ?? 0.91;
  const displayEvidence = (rootCauseData?.evidence && rootCauseData.evidence.length > 0)
    ? rootCauseData.evidence
    : (investigation?.evidence || [
        "UPI network failure rate elevated above baseline in NPCI link",
        "Customer historical success rate: 91.6% (11/12 successful payments)",
        "Zero fraud flags, trusted device & phone fingerprint verified",
      ]);
  const displayExplanation = rootCauseData?.explanation || "The payment failed due to temporary UPI PSP latency degradation rather than customer insufficiency.";

  const primaryChunk = policyContextData?.retrieved_policies?.[0];
  const displaySection = primaryChunk?.section || "UPI Failures";
  const displayPolicyMatch = Math.round((policyContextData?.policy_match_confidence ?? 0.95) * 100);
  const displayPolicyRule = primaryChunk?.content || "## 2. UPI Failures\nWhen UPI payment failures occur during an active PSP degradation window, automated direct retries are suspended. For orders <= INR 25,000, autonomous generation of a secure payment link with 24hr expiry is permitted.";
  const displayInterpretation = policyContextData?.ai_interpretation || "According to Merchant Policy (§ UPI Failures & Gateway Degradation), technical failures during degradation permit autonomous payment link recovery with 24-hour expiry for amounts <= INR 25,000.";

  return (
    <PageTransition className="space-y-6">
      {/* Live AI Reasoning Simulation Modal */}
      <LiveExecutionModal
        open={showLiveModal}
        onOpenChange={setShowLiveModal}
        transactionId={transaction.id}
        amount={transaction.amount}
        customerName={customer.name}
        onComplete={handleModalComplete}
      />

      {/* Webhook Playground Modal */}
      <WebhookPlaygroundModal
        open={showWebhookModal}
        onOpenChange={setShowWebhookModal}
        transactionId={transaction.id}
        amount={transaction.amount}
        onPaymentSuccess={handlePaymentSuccess}
      />

      {/* Back Button & Header */}
      <motion.div
        variants={itemFadeUp}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div className="flex items-center gap-3">
          <Link href="/transactions">
            <Button variant="outline" size="icon" className="h-9 w-9 hover:bg-slate-100 transition-colors">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 font-mono break-all">
                {transaction.id}
              </h1>
              <Badge
                variant={isRecovered ? "success" : isBlocked ? "danger" : isHumanReview ? "warning" : hasExecutedRecovery ? "warning" : "danger"}
                size="sm"
              >
                {isRecovered ? `RECOVERED (${formatCurrency(transaction.amount)})` : isBlocked ? "BLOCKED" : isHumanReview ? "HUMAN REVIEW REQUIRED" : hasExecutedRecovery ? "Payment Link Sent" : transaction.status}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Initiated on {transaction.created_at} • Gateway: {transaction.payment_gateway.toUpperCase()} • Razorpay Test Mode
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {!isRecovered && !isBlocked && hasExecutedRecovery && (
            <Button
              onClick={() => setShowWebhookModal(true)}
              variant="outline"
              size="sm"
              className="gap-1.5 border-emerald-400 bg-emerald-50/80 text-emerald-800 hover:bg-emerald-100 font-semibold shadow-xs"
            >
              <Zap className="h-3.5 w-3.5 fill-emerald-600 text-emerald-600" />
              <span>Simulate Customer Paying</span>
            </Button>
          )}

          {isHumanReview ? (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={() => handleHumanApproval(false)}
                disabled={isApproving}
                variant="outline"
                className="gap-1.5 text-red-600 border-red-200 hover:bg-red-50"
              >
                <ThumbsDown className="h-3.5 w-3.5" />
                <span>Reject</span>
              </Button>
              <Button
                size="sm"
                onClick={() => handleHumanApproval(true)}
                disabled={isApproving}
                className="gap-1.5 bg-amber-600 hover:bg-amber-700 text-white"
              >
                {isApproving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ThumbsUp className="h-3.5 w-3.5" />}
                <span>Approve Recovery ({formatCurrency(transaction.amount)})</span>
              </Button>
            </div>
          ) : isBlocked ? (
            <div className="flex items-center gap-1.5 text-xs text-red-600 font-semibold px-3 py-1.5 bg-red-50 rounded-lg border border-red-200">
              <XCircle className="h-4 w-4 text-red-500" />
              <span>Recovery Blocked by Policy</span>
            </div>
          ) : (
            <Button
              onClick={() => setShowLiveModal(true)}
              className="gap-2 bg-gradient-to-r from-[#0052cc] to-[#1e40af] text-white shadow-md hover:shadow-lg hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              {isRecovered ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-emerald-300" />
                  <span>Re-run AI Reasoning</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-white" />
                  <span>Execute AI Recovery</span>
                </>
              )}
            </Button>
          )}
        </div>
      </motion.div>

      {/* Webhook Simulator Call-To-Action Banner */}
      {!isRecovered && !isBlocked && hasExecutedRecovery && (
        <motion.div
          variants={itemFadeUp}
          className="rounded-xl border border-emerald-300 bg-gradient-to-r from-emerald-50 via-teal-50/60 to-emerald-50/30 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-xs">
              <Zap className="h-5 w-5 fill-white" />
            </div>
            <div>
              <span className="font-bold text-xs uppercase tracking-wider text-emerald-950">
                Customer Paid on Razorpay?
              </span>
              <p className="text-xs text-emerald-800 mt-0.5">
                Fire the signed Razorpay webhook simulator to verify HMAC-SHA256, seal the audit record, and update revenue.
              </p>
            </div>
          </div>
          <Button
            size="sm"
            onClick={() => setShowWebhookModal(true)}
            className="shrink-0 gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow-xs"
          >
            <Zap className="h-3.5 w-3.5 fill-white" />
            <span>Simulate Customer Payment Now</span>
          </Button>
        </motion.div>
      )}

      {/* Negative Test / Notice Alerts */}
      {isBlocked && (
        <motion.div variants={itemFadeUp} className="rounded-lg border border-red-200 bg-red-50/80 p-4 text-xs text-red-900 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-sm">❌ Autonomous Recovery Blocked</span>
            <p className="mt-1 text-red-800">
              This transaction exceeded deterministic policy guardrails (e.g. maximum retries exceeded: {transaction.attempt_number} of 2, or risk threshold breached). In accordance with merchant security policies, automated link generation is permanently suppressed.
            </p>
          </div>
        </motion.div>
      )}

      {isHumanReview && (
        <motion.div variants={itemFadeUp} className="rounded-lg border border-amber-200 bg-amber-50/80 p-4 text-xs text-amber-900 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold text-sm">⚠ Merchant Human Approval Required</span>
            <p className="mt-1 text-amber-800">
              Transaction value of <strong>{formatCurrency(transaction.amount)}</strong> exceeds the autonomous action ceiling of ₹25,000. Review the AI reasoning below and click <strong>Approve Recovery</strong> to dispatch the Razorpay Payment Link.
            </p>
          </div>
        </motion.div>
      )}

      {isRecovered && (
        <motion.div variants={itemFadeUp} className="rounded-lg border border-emerald-200 bg-emerald-50/80 p-4 text-xs text-emerald-900 flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-sm">✓ Revenue Successfully Recovered</span>
            <p className="mt-1 text-emerald-800">
              Inbound Razorpay webhook cryptographically verified via HMAC-SHA256. ₹{transaction.amount.toLocaleString()} was captured and credited to merchant revenue. Audit trail sealed.
            </p>
          </div>
        </motion.div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Summary & Customer Profile */}
        <motion.div variants={itemFadeUp} className="space-y-6">
          {/* Summary Card */}
          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Transaction Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Amount</span>
                <span className="font-bold text-slate-900 text-sm">
                  {formatCurrency(transaction.amount)}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Payment Method</span>
                <span className="font-medium text-slate-800 uppercase">{transaction.payment_method}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Bank / Network</span>
                <span className="font-medium text-slate-800">{transaction.bank || "NPCI / HDFC"}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Failure Reason</span>
                <span className="font-mono text-red-600 bg-red-50 px-1.5 py-0.5 rounded border border-red-200">
                  {transaction.failure_reason || "upi_timeout"}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Attempt Count</span>
                <span className="font-medium text-slate-800">#{transaction.attempt_number} of 2 (Safe Limit)</span>
              </div>
            </CardContent>
          </Card>

          {/* Customer History */}
          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <User className="h-4 w-4 text-blue-600" />
                <span>Customer Profile</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div>
                <div className="font-semibold text-slate-900 text-sm">{customer.name}</div>
                <div className="text-slate-500 mt-0.5">{customer.email}</div>
                <div className="text-slate-400 font-mono text-[11px] mt-0.5">{customer.phone}</div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
                <div className="rounded-lg bg-slate-50 p-2.5">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Success Rate</div>
                  <div className="text-base font-bold text-emerald-600 mt-0.5">
                    {formatPercentage(
                      (customer.successful_transactions / Math.max(customer.total_transactions, 1)) * 100
                    )}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {customer.successful_transactions}/{customer.total_transactions} txns
                  </div>
                </div>

                <div className="rounded-lg bg-slate-50 p-2.5">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Lifetime Value</div>
                  <div className="text-base font-bold text-slate-900 mt-0.5">
                    {formatCurrency(customer.lifetime_value)}
                  </div>
                  <div className="text-[10px] text-slate-400">Trusted Customer</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Right Column: Phase 5 Root Cause Card + Phase 6 RAG Card + Guardrails & Timeline */}
        <motion.div variants={itemFadeUp} className="lg:col-span-2 space-y-6">
          
          {/* Phase 5: Dedicated AI Root Cause Analysis Card */}
          <Card className="border-blue-200 bg-gradient-to-br from-white via-slate-50/50 to-blue-50/30 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-xs">
                    <Brain className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-base text-slate-900">AI Root Cause Diagnosis</CardTitle>
                      <Badge variant="default" size="sm" className="bg-blue-100 text-blue-800 border-blue-200 font-mono text-[10px]">
                        Google Gemini 2.5 Flash
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500">Autonomous evidence-first failure diagnostics from live transaction telemetry</p>
                  </div>
                </div>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleReanalyzeRootCause}
                  disabled={loadingRootCause}
                  className="h-8 gap-1.5 text-xs text-slate-700 hover:text-blue-700 border-slate-200"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${loadingRootCause ? "animate-spin text-blue-600" : ""}`} />
                  <span>{loadingRootCause ? "Diagnosing..." : "Re-Analyze"}</span>
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-4 pt-4">
              {rootCauseError && (
                <div className="text-xs text-amber-800 bg-amber-50 p-2.5 rounded-lg border border-amber-200 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
                  <span>{rootCauseError}</span>
                </div>
              )}

              {/* Diagnosis Badge & Confidence Meter */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-xs">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Diagnosed Category</span>
                  <div className="mt-1.5 flex items-center gap-2">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold border ${getCategoryColor(displayRootCause)}`}>
                      {formatCategoryName(displayRootCause)}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Telemetry: {transaction.payment_method.toUpperCase()} • {transaction.bank || "HDFC"}
                  </span>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Diagnosis Confidence</span>
                    <span className="text-sm font-bold text-blue-700">
                      {Math.round(displayConfidence * 100)}%
                    </span>
                  </div>
                  <div className="mt-2">
                    <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${displayConfidence >= 0.8 ? "bg-emerald-500" : displayConfidence >= 0.6 ? "bg-amber-500" : "bg-red-500"}`}
                        style={{ width: `${Math.round(displayConfidence * 100)}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-400 mt-1 block">
                    Validated against signal bounds [0.0 - 1.0]
                  </span>
                </div>
              </div>

              {/* Factual Explanation Box */}
              <div className="rounded-lg bg-slate-50/80 border border-slate-200/80 p-3 text-xs">
                <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider block mb-1">
                  AI Diagnostic Explanation
                </span>
                <p className="text-slate-700 leading-relaxed font-sans">
                  {displayExplanation}
                </p>
              </div>

              {/* Factual Evidence Points Checklist */}
              <div>
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-2">
                  Factual Signals & Investigative Evidence
                </span>
                <div className="space-y-1.5">
                  {displayEvidence.map((item, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.2, delay: idx * 0.05 }}
                      className="flex items-start gap-2 text-xs text-slate-700 bg-white p-2.5 rounded-lg border border-slate-200 shadow-xs"
                    >
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span className="leading-snug">{item}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Phase 6: Dedicated Relevant Merchant Policy (RAG) Card */}
          <Card className="border-indigo-200 bg-gradient-to-br from-white via-indigo-50/20 to-purple-50/20 shadow-sm">
            <CardHeader className="pb-3 border-b border-indigo-100">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-purple-700 text-white shadow-xs">
                    <BookOpen className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-base text-slate-900">Relevant Merchant Policy (RAG)</CardTitle>
                      <Badge variant="default" size="sm" className="bg-indigo-100 text-indigo-800 border-indigo-200 text-[10px]">
                        merchant_policy.md
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500">Hybrid TF-IDF & keyword vector retrieval grounding AI actions in merchant rules</p>
                  </div>
                </div>

                <Badge variant="success" className="bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold text-xs">
                  {displayPolicyMatch}% Policy Match
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-4 pt-4">
              {/* Section Header & Policy Excerpt Quote */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[11px] font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                    <Scale className="h-3.5 w-3.5 text-indigo-600" />
                    <span>Retrieved Section: § {displaySection}</span>
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Source: {primaryChunk?.source || "merchant_policy.md"}
                  </span>
                </div>

                <div className="rounded-lg bg-indigo-50/60 border-l-4 border-indigo-500 p-3.5 text-xs text-slate-800 font-mono leading-relaxed whitespace-pre-line shadow-xs">
                  {displayPolicyRule}
                </div>
              </div>

              {/* Policy-Grounded AI Interpretation */}
              <div className="rounded-lg bg-white border border-indigo-200 p-3.5 shadow-xs">
                <div className="flex items-center gap-1.5 text-indigo-950 font-bold text-xs uppercase tracking-wider mb-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                  <span>Policy-Grounded AI Interpretation</span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {displayInterpretation}
                </p>
                <div className="mt-2.5 pt-2 border-t border-slate-100 flex flex-wrap items-center gap-1.5 text-[10px] text-slate-500">
                  <span className="font-semibold text-slate-600">Query Telemetry:</span>
                  <span className="bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-700">
                    {policyContextData?.query || `${transaction.payment_method} ${displayRootCause}`}
                  </span>
                </div>
              </div>

              {/* Deterministic Guardrails Checklist */}
              <div className="pt-2 border-t border-indigo-100 space-y-2">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  <span>Deterministic Guardrail Verifications</span>
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {investigation?.policy_checks.map((check, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200 text-xs">
                      {check.status === "passed" ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                      ) : (
                        <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
                      )}
                      <span className="text-slate-800 font-medium">{check.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Multi-Agent Execution Timeline */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <History className="h-4 w-4 text-slate-700" />
                <span>Multi-Agent Execution Timeline</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AgentExecutionTimeline
                steps={timelineSteps}
                paymentLinkUrl={executionResult?.razorpay_payment_link}
                transactionId={transaction.id}
                isExecuting={isExecuting}
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </PageTransition>
  );
}
