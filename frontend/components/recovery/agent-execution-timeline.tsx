"use client";

import React from "react";
import { motion } from "framer-motion";
import { CheckCircle2, AlertCircle, Loader2, Sparkles, ShieldCheck, ArrowRight, Link2, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

export interface TimelineStep {
  id: string;
  title: string;
  description: string;
  status: "completed" | "in_progress" | "pending" | "blocked";
  meta?: string;
  agent?: string;
}

interface AgentExecutionTimelineProps {
  steps: TimelineStep[];
  paymentLinkUrl?: string;
  transactionId?: string;
  isExecuting?: boolean;
}

export function AgentExecutionTimeline({ steps, paymentLinkUrl, transactionId, isExecuting }: AgentExecutionTimelineProps) {
  return (
    <div className="space-y-4">
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
        {steps.map((step, idx) => {
          const isCompleted = step.status === "completed";
          const isInProgress = step.status === "in_progress";
          const isBlocked = step.status === "blocked";

          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.1 }}
              className="relative flex items-start gap-4"
            >
              {/* Node Icon */}
              <div className="absolute -left-6 top-0 flex items-center justify-center">
                {isCompleted ? (
                  <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-white shadow-sm ring-4 ring-white">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  </div>
                ) : isInProgress ? (
                  <div className="flex h-5 w-5 items-center justify-center rounded-full bg-[#0052cc] text-white shadow-sm ring-4 ring-white animate-spin">
                    <Loader2 className="h-3.5 w-3.5" />
                  </div>
                ) : isBlocked ? (
                  <div className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-white shadow-sm ring-4 ring-white">
                    <AlertCircle className="h-3.5 w-3.5" />
                  </div>
                ) : (
                  <div className="h-4 w-4 rounded-full bg-slate-200 ring-4 ring-white" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 rounded-lg border border-slate-200/80 bg-white p-3.5 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-900">{step.title}</span>
                  {step.agent && (
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 font-mono">
                      {step.agent}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-slate-600 leading-relaxed">{step.description}</p>
                {step.meta && (
                  <div className="mt-2 flex items-center gap-1.5 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-1 rounded border border-emerald-200">
                    <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
                    <span>{step.meta}</span>
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {paymentLinkUrl && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white">
                <Link2 className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-900">
                  Razorpay Test Payment Link Generated
                </h4>
                <p className="text-xs text-emerald-700 mt-0.5 font-mono">{paymentLinkUrl}</p>
              </div>
            </div>
            <a
              href={transactionId ? `/pay/${transactionId}` : (paymentLinkUrl || "/pay/txn_4999_upi")}
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
    </div>
  );
}
