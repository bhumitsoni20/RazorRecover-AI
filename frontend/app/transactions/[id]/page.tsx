"use client";

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
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AgentExecutionTimeline, TimelineStep } from "@/components/recovery/agent-execution-timeline";
import { LiveExecutionModal } from "@/components/recovery/live-execution-modal";
import { WebhookPlaygroundModal } from "@/components/recovery/webhook-playground-modal";
import { apiClient } from "@/lib/api-client";
import { TransactionDetailResponse } from "@/types/api";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { PageTransition, itemFadeUp, staggerContainer } from "@/components/animations/page-transition";

export default function TransactionDetailPage() {
  const params = useParams();
  const id = (params?.id as string) || "txn_4999_upi";

  const [transaction, setTransaction] = useState<TransactionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
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
      const res = await apiClient.getTransaction(id);
      setTransaction(res);
      const isRecov = res.status === "recovered";
      setIsRecovered(isRecov);

      const decision = res.investigation?.policy_decision || (res.amount > 25000 ? "HUMAN_APPROVAL_REQUIRED" : res.attempt_number > 2 ? "BLOCKED" : "APPROVED");
      setIsHumanReview(decision === "HUMAN_APPROVAL_REQUIRED");
      setIsBlocked(decision === "BLOCKED");

      const hasAction = res.recovery_actions && res.recovery_actions.length > 0;
      const latestAction = hasAction ? res.recovery_actions[0] : null;

      if (latestAction && latestAction.external_reference) {
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
          description: res.investigation?.root_cause || "Payment Method Degradation (UPI spike detected)",
          status: "completed",
          agent: "RootCauseAgent",
        },
        {
          id: "step_3",
          title: "Policy RAG Retrieval",
          description: res.investigation?.rag_policy_reference || "Policy §2.1: Payment link generation approved for degradation <= ₹25k",
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
        const statusRes = await fetch(`http://localhost:8000/api/recovery/${id}/status`);
        if (statusRes.ok) {
          const json = await statusRes.json();
          if (json.data && json.data.is_recovered) {
            setIsRecovered(true);
            setTimelineSteps((prev) =>
              prev.map((step) =>
                step.id === "step_6"
                  ? {
                      ...step,
                      status: "completed",
                      description: "Inbound payment_link.paid webhook verified via raw HMAC-SHA256. Transaction marked recovered.",
                    }
                  : step
              )
            );
          }
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
          : step
      )
    );
  };

  const handleHumanApproval = async (approved: boolean) => {
    setIsApproving(true);
    try {
      const res = await fetch(`http://localhost:8000/api/recovery/${id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transaction_id: id,
          approved: approved,
          approver_note: approved ? "Approved by Merchant Admin" : "Rejected by Merchant Admin",
        }),
      });

      if (res.ok) {
        const json = await res.json();
        if (approved) {
          setIsHumanReview(false);
          setExecutionResult({
            status: "executed",
            razorpay_payment_link: json.data?.razorpay_payment_link || "https://rzp.io/i/test_approved",
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
      }
    } catch (e) {
      console.error("Failed to approve action:", e);
    } finally {
      setIsApproving(false);
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
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 font-mono">
                {transaction.id}
              </h1>
              <Badge
                variant={isRecovered ? "success" : isBlocked ? "danger" : isHumanReview ? "warning" : executionResult ? "warning" : "danger"}
                size="sm"
              >
                {isRecovered ? `RECOVERED (${formatCurrency(transaction.amount)})` : isBlocked ? "BLOCKED" : isHumanReview ? "HUMAN REVIEW REQUIRED" : executionResult ? "Payment Link Sent" : transaction.status}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Initiated on {transaction.created_at} • Gateway: {transaction.payment_gateway.toUpperCase()} • Razorpay Test Mode
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {executionResult && !isRecovered && (
            <Button
              onClick={() => setShowWebhookModal(true)}
              variant="outline"
              size="sm"
              className="gap-1.5 border-emerald-300 text-emerald-700 hover:bg-emerald-50"
            >
              <Zap className="h-3.5 w-3.5" />
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
        {/* Left Column */}
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

        {/* Right Column: Why this action? + Agent Timeline */}
        <motion.div variants={itemFadeUp} className="lg:col-span-2 space-y-6">
          {/* Why This Action Card */}
          <Card className="border-blue-200 bg-gradient-to-br from-white to-blue-50/40 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-white shadow-xs">
                    <Brain className="h-4 w-4" />
                  </div>
                  <div>
                    <CardTitle className="text-base text-slate-900">Why this action?</CardTitle>
                    <p className="text-xs text-slate-500">Autonomous reasoning, RAG merchant policy context & ML risk prediction</p>
                  </div>
                </div>
                <Badge variant="default" size="md" className="font-semibold">
                  91% Model Confidence
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Root Cause & ML Probability */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <motion.div whileHover={{ scale: 1.02 }} className="rounded-lg border border-slate-200 bg-white p-3 shadow-xs transition-transform">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Root Cause</span>
                  <div className="text-sm font-bold text-slate-900 mt-1">
                    {investigation?.root_cause || "Payment Method Degradation"}
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">UPI PSP Latency Spike (+4.8x)</span>
                </motion.div>

                <motion.div whileHover={{ scale: 1.02 }} className="rounded-lg border border-slate-200 bg-white p-3 shadow-xs transition-transform">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Recovery Probability</span>
                  <div className="text-sm font-bold text-emerald-600 mt-1">
                    {investigation ? formatPercentage(investigation.recovery_probability * 100) : "87.0%"}
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">
                    Expected Yield: {investigation ? formatCurrency(investigation.expected_recovery) : "₹4,349"}
                  </span>
                </motion.div>

                <motion.div whileHover={{ scale: 1.02 }} className="rounded-lg border border-slate-200 bg-white p-3 shadow-xs transition-transform">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Selected Strategy</span>
                  <div className="text-sm font-bold text-[#0052cc] mt-1 capitalize">
                    {investigation?.recommended_action.replace("_", " ") || "Generate Payment Link"}
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Via Razorpay Test Mode API</span>
                </motion.div>
              </div>

              {/* Evidence Checklist */}
              <div>
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Investigative Evidence & Anomaly Telemetry
                </span>
                <div className="mt-2 space-y-1.5">
                  {investigation?.evidence.map((item, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.2, delay: idx * 0.06 }}
                      className="flex items-start gap-2 text-xs text-slate-700 bg-white/80 p-2 rounded-lg border border-slate-200/60"
                    >
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Policy RAG Section Citation */}
              <div className="pt-2 border-t border-blue-100 space-y-2">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  <span>Deterministic Guardrails & Policy Citations</span>
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

                {investigation?.rag_policy_reference && (
                  <div className="flex items-start gap-2 text-[11px] text-slate-600 bg-blue-50/70 p-2.5 rounded-lg border border-blue-200">
                    <BookOpen className="h-4 w-4 text-blue-600 shrink-0 mt-0.5" />
                    <span><strong>Retrieved Policy Citation:</strong> {investigation.rag_policy_reference}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Agent Execution Timeline */}
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
                isExecuting={isExecuting}
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </PageTransition>
  );
}
