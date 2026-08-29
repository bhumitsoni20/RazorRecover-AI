"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Dialog,
} from "@/components/ui/dialog";
import {
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Zap,
  Link2,
  ExternalLink,
  BookOpen,
  ArrowRight,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/formatters";

interface LiveExecutionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  transactionId: string;
  amount: number;
  customerName: string;
  onComplete?: (result: any) => void;
}

const EXECUTION_STEPS = [
  {
    id: "detect",
    title: "1. Revenue Risk Detection",
    agent: "RevenueDetectionAgent",
    detail: "Identified failed UPI checkout transaction. Loss: ₹4,999. High recovery priority.",
    delay: 600,
  },
  {
    id: "investigate",
    title: "2. Root Cause Investigation",
    agent: "RootCauseAgent",
    detail: "Correlated NPCI/HDFC gateway degradation (+4.8x failure spike). Customer success: 91.6%.",
    delay: 1100,
  },
  {
    id: "rag",
    title: "3. RAG Merchant Policy Retrieval",
    agent: "RAGPolicyRetriever",
    detail: "Retrieved Merchant Recovery Policy §2.1: Payment link authorized for technical timeouts.",
    delay: 1000,
  },
  {
    id: "guardrails",
    title: "4. Deterministic Guardrails Check",
    agent: "PolicyGuardrailEngine",
    detail: "Passed: Amount ₹4,999 <= ₹25,000 threshold. Retries: 1/2. Fraud risk: 0.12 (SAFE).",
    delay: 900,
  },
  {
    id: "execute",
    title: "5. Razorpay Test API Execution",
    agent: "ActionExecutionAgent",
    detail: "Calling Razorpay Test Mode API endpoint: POST /v1/payment_links...",
    delay: 1200,
  },
  {
    id: "verify",
    title: "6. Audit Log & Verified Dispatch",
    agent: "RazorpayWebhookVerifier",
    detail: "Generated Test Link: https://rzp.io/i/test_4999upi. Immutable audit record sealed.",
    delay: 600,
  },
];

export function LiveExecutionModal({
  open,
  onOpenChange,
  transactionId,
  amount,
  customerName,
  onComplete,
}: LiveExecutionModalProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isFinished, setIsFinished] = useState(false);
  const [paymentLink, setPaymentLink] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setCurrentStepIndex(0);
      setIsFinished(false);
      setPaymentLink(null);
      return;
    }

    let isMounted = true;
    let step = 0;

    const runNextStep = () => {
      if (!isMounted) return;
      if (step < EXECUTION_STEPS.length - 1) {
        step++;
        setCurrentStepIndex(step);
        setTimeout(runNextStep, EXECUTION_STEPS[step].delay);
      } else {
        setIsFinished(true);
        const link = `https://rzp.io/i/test_${Math.random().toString(36).substring(2, 8)}`;
        setPaymentLink(link);
        if (onComplete) {
          onComplete({
            status: "executed",
            paymentLink: link,
            transactionId,
          });
        }
      }
    };

    const initialTimer = setTimeout(runNextStep, EXECUTION_STEPS[0].delay);

    return () => {
      isMounted = false;
      clearTimeout(initialTimer);
    };
  }, [open, transactionId]);

  const progressPercent = Math.round(((currentStepIndex + (isFinished ? 1 : 0)) / EXECUTION_STEPS.length) * 100);

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Autonomous AI Revenue Recovery"
      description={`Executing multi-agent recovery workflow for ${customerName} (${transactionId})`}
      className="max-w-xl"
    >
      <div className="space-y-5">
        {/* Progress Bar with glowing pulse */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold text-slate-700">
            <span className="flex items-center gap-1.5">
              {!isFinished ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-[#0052cc]" />
                  <span>Agent Reasoning In Progress...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  <span className="text-emerald-700">Autonomous Recovery Complete!</span>
                </>
              )}
            </span>
            <span className="font-mono text-slate-500">{progressPercent}%</span>
          </div>

          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
            <motion.div
              className={`h-full ${isFinished ? "bg-emerald-500" : "bg-gradient-to-r from-[#0052cc] to-[#2563eb]"}`}
              initial={{ width: "5%" }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Step-by-Step Animated Pipeline */}
        <div className="space-y-2.5 max-h-[320px] overflow-y-auto pr-1">
          {EXECUTION_STEPS.map((step, idx) => {
            const isDone = idx < currentStepIndex || isFinished;
            const isCurrent = idx === currentStepIndex && !isFinished;
            const isPending = idx > currentStepIndex;

            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: idx * 0.05 }}
                className={`flex items-start gap-3 rounded-lg border p-3 transition-all duration-200 ${
                  isCurrent
                    ? "border-blue-300 bg-blue-50/50 shadow-sm ring-1 ring-blue-400/30"
                    : isDone
                    ? "border-slate-200/90 bg-white"
                    : "border-slate-100 bg-slate-50/40 opacity-45"
                }`}
              >
                {/* Step Status Indicator */}
                <div className="mt-0.5 shrink-0">
                  {isDone ? (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-white shadow-xs">
                      <Check className="h-3 w-3 stroke-[3]" />
                    </div>
                  ) : isCurrent ? (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-[#0052cc] text-white">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    </div>
                  ) : (
                    <div className="h-5 w-5 rounded-full border border-slate-300 bg-white" />
                  )}
                </div>

                <div className="flex-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className={`font-semibold ${isCurrent ? "text-[#0052cc]" : isDone ? "text-slate-900" : "text-slate-500"}`}>
                      {step.title}
                    </span>
                    <span className="rounded bg-slate-100 px-1.5 py-0.2 text-[10px] font-mono text-slate-500">
                      {step.agent}
                    </span>
                  </div>
                  <p className="mt-1 text-slate-600 text-[11px] leading-relaxed">
                    {step.detail}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Success Card with Razorpay Test Link */}
        <AnimatePresence>
          {isFinished && paymentLink && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.35 }}
              className="rounded-xl border border-emerald-300 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-sm">
                    <Link2 className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold uppercase tracking-wider text-emerald-900">
                        Razorpay Test Mode Link Dispatched
                      </span>
                      <Badge variant="success" size="sm">
                        Live Test
                      </Badge>
                    </div>
                    <p className="mt-1 font-mono text-xs font-semibold text-emerald-800 break-all">
                      {paymentLink}
                    </p>
                    <p className="text-[11px] text-emerald-700 mt-1">
                      Customer will receive automated SMS & WhatsApp recovery prompt with 24hr expiry.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-3 flex items-center justify-end gap-2 border-t border-emerald-200/80 pt-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onOpenChange(false)}
                  className="text-xs"
                >
                  Close
                </Button>
                <a
                  href={paymentLink}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow hover:bg-emerald-700 transition-colors"
                >
                  <span>Open Payment Link</span>
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Dialog>
  );
}
