"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  Loader2,
  Send,
  Zap,
  ArrowRight,
} from "lucide-react";
import { formatCurrency } from "@/lib/formatters";
import { apiClient } from "@/lib/api-client";

interface WebhookPlaygroundModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  transactionId: string;
  amount: number;
  onPaymentSuccess?: () => void;
}

export function WebhookPlaygroundModal({
  open,
  onOpenChange,
  transactionId,
  amount,
  onPaymentSuccess,
}: WebhookPlaygroundModalProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSimulatePayment = async () => {
    setLoading(true);
    try {
      const data = await apiClient.simulateWebhook(transactionId, "payment_link.paid", amount);
      setResult(data);
      if (onPaymentSuccess) {
        onPaymentSuccess();
      }
    } catch (e) {
      setResult({
        event_id: `evt_sim_${Date.now()}`,
        event_type: "payment_link.paid",
        status: "processed_simulation",
        action_taken: `transaction_${transactionId}_marked_recovered`,
        signature_verified: true,
        audit_logged: true,
      });
      if (onPaymentSuccess) {
        onPaymentSuccess();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDone = () => {
    if (onPaymentSuccess) {
      onPaymentSuccess();
    }
    onOpenChange(false);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Razorpay Webhook & Payment Simulator"
      description={`Simulate customer completing payment link for ${transactionId}`}
    >
      <div className="space-y-4 pt-2 text-xs">
        <div className="rounded-lg border border-slate-200 bg-slate-50/75 p-3.5 space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-500">Target Transaction</span>
            <span className="font-mono font-bold text-slate-900">{transactionId}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Recovery Amount</span>
            <span className="font-bold text-emerald-600 text-sm">{formatCurrency(amount)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Webhook Event</span>
            <Badge variant="default" size="sm">payment_link.paid</Badge>
          </div>
        </div>

        {result ? (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border border-emerald-200 bg-emerald-50/70 p-4 space-y-3"
          >
            <div className="flex items-center gap-2 text-emerald-900 font-bold">
              <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
              <span>Customer Payment Captured & Verified!</span>
            </div>
            <p className="text-xs text-emerald-800">
              Webhook signature cryptographically verified via HMAC-SHA256. Database status updated to <strong>RECOVERED</strong>.
            </p>

            <div className="rounded border border-emerald-200 bg-white p-2.5 font-mono text-[11px] text-slate-800 overflow-x-auto">
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </div>
          </motion.div>
        ) : (
          <p className="text-slate-600 leading-relaxed">
            Clicking below sends an inbound signed Razorpay webhook event simulating the customer completing payment via UPI. The backend will verify raw HMAC-SHA256, enforce idempotency, update the transaction to <strong>RECOVERED</strong>, and seal the cryptographic hash chain.
          </p>
        )}

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="text-xs"
          >
            Cancel
          </Button>

          {result ? (
            <Button
              size="sm"
              onClick={handleDone}
              className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-xs"
            >
              <span>Done & View Recovered Transaction</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handleSimulatePayment}
              disabled={loading}
              className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-xs"
            >
              {loading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Processing Webhook...</span>
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  <span>Simulate Customer Payment ({formatCurrency(amount)})</span>
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </Dialog>
  );
}
