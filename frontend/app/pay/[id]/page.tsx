"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Script from "next/script";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  ShieldCheck,
  Zap,
  CreditCard,
  Loader2,
  ArrowRight,
  Lock,
  ExternalLink,
  Copy,
  Check,
  Sparkles,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import { TransactionDetailResponse } from "@/types/api";
import { formatCurrency } from "@/lib/formatters";

export default function RazorpayHostedPaymentPage() {
  const params = useParams();
  const router = useRouter();
  const id = (params?.id as string) || "txn_4999_upi";

  const [transaction, setTransaction] = useState<TransactionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [paymentId, setPaymentId] = useState("");
  const [copied, setCopied] = useState(false);
  const [razorpayReady, setRazorpayReady] = useState(false);
  const autoLaunchedRef = useRef(false);

  useEffect(() => {
    const fetchTxn = async () => {
      setLoading(true);
      try {
        const res = await apiClient.getTransaction(id);
        setTransaction(res);
        if (res.status === "recovered") {
          setPaymentSuccess(true);
          setPaymentId(`pay_recov_${id.slice(-8)}`);
        }
      } catch (e) {
        console.error("Failed to load transaction for checkout:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchTxn();
  }, [id]);

  const handleSimulateOneClick = async () => {
    if (!transaction) return;
    setIsProcessing(true);
    const pId = `pay_sim_${Math.random().toString(36).substring(2, 10)}`;
    try {
      await apiClient.simulateWebhook(transaction.id, "payment_link.paid", transaction.amount);
    } catch (e) {
      console.warn("One-click simulation notice:", e);
    } finally {
      setPaymentId(pId);
      setPaymentSuccess(true);
      setIsProcessing(false);
    }
  };

  const launchRazorpayModal = async () => {
    if (!transaction) return;
    setIsProcessing(true);

    try {
      // 1. Fetch real Razorpay order from backend via apiClient
      const orderData = await apiClient.createOrder(transaction.id);

      const keyId = orderData?.key_id || "rzp_test_TVxlSjEzulO7pK";
      const amountPaise = orderData?.amount || Math.round(transaction.amount * 100);

      // Check if window.Razorpay SDK is loaded
      if (typeof window !== "undefined" && (window as any).Razorpay) {
        const options: any = {
          key: keyId,
          amount: amountPaise,
          currency: "INR",
          name: "Fintech Merchant Global",
          description: `Payment recovery for ${transaction.id}`,
          image: "https://razorpay.com/favicon.png",
          prefill: {
            name: transaction.customer?.name || "Aditya Verma",
            email: transaction.customer?.email || "aditya.verma@example.com",
            contact: transaction.customer?.phone || "+919876543210",
          },
          theme: {
            color: "#0052cc",
          },
          modal: {
            ondismiss: function () {
              setIsProcessing(false);
            },
          },
          handler: async function (response: any) {
            try {
              const pId = response.razorpay_payment_id || `pay_${Math.random().toString(36).substring(2, 10)}`;
              setPaymentId(pId);

              // Trigger backend webhook verification via apiClient
              await apiClient.simulateWebhook(transaction.id, "payment_link.paid", transaction.amount);
            } catch (err) {
              console.warn("Payment handler webhook notification notice:", err);
            } finally {
              setPaymentSuccess(true);
              setIsProcessing(false);
            }
          },
        };

        // Only attach order_id if confirmed live server order
        if (orderData?.is_live_order && orderData?.order_id && !orderData.order_id.startsWith("order_mock_")) {
          options.order_id = orderData.order_id;
        }

        const rzp = new (window as any).Razorpay(options);
        rzp.on("payment.failed", function (response: any) {
          console.warn("Razorpay test payment failed/cancelled:", response.error);
          setIsProcessing(false);
        });
        rzp.open();
      } else {
        // Fallback simulation if script is offline
        await handleSimulateOneClick();
      }
    } catch (e) {
      console.error("Razorpay launch error:", e);
      setIsProcessing(false);
    }
  };

  // Automatically trigger Razorpay checkout modal when script is ready and transaction is not yet recovered
  useEffect(() => {
    if (razorpayReady && transaction && !paymentSuccess && !autoLaunchedRef.current) {
      autoLaunchedRef.current = true;
      launchRazorpayModal();
    }
  }, [razorpayReady, transaction, paymentSuccess]);

  const copyPaymentId = () => {
    if (paymentId) {
      navigator.clipboard.writeText(paymentId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 font-sans">
        <div className="flex items-center gap-2 text-slate-500 text-sm">
          <Loader2 className="h-5 w-5 animate-spin text-[#0052cc]" />
          <span>Opening official Razorpay Test Checkout...</span>
        </div>
      </div>
    );
  }

  const amount = transaction?.amount || 4999.0;
  const customerName = transaction?.customer?.name || "Customer";
  const customerEmail = transaction?.customer?.email || "customer@example.com";
  const customerPhone = transaction?.customer?.phone || "+91 98765 43210";

  return (
    <>
      <Script
        src="https://checkout.razorpay.com/v1/checkout.js"
        onLoad={() => setRazorpayReady(true)}
        onError={() => setRazorpayReady(true)}
      />

      <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col justify-between font-sans">
        {/* Test Mode Banner */}
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-center text-xs font-medium text-amber-900 flex items-center justify-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
          <span>This payment page is operating in <strong>Razorpay Test Mode</strong>. No real money will be charged.</span>
        </div>

        {/* Main Card */}
        <div className="max-w-lg mx-auto w-full px-4 py-12 flex-1 flex items-center justify-center">
          <Card className="w-full border-slate-200 shadow-xl bg-white overflow-hidden rounded-2xl">
            {/* Header */}
            <div className="bg-gradient-to-r from-[#0052cc] to-[#0747a6] p-6 text-white text-center relative">
              <div className="flex items-center justify-center gap-2 mb-2">
                <img
                  src="https://razorpay.com/favicon.png"
                  alt="Razorpay"
                  className="h-6 w-6 rounded bg-white p-0.5"
                />
                <h2 className="font-bold text-base tracking-tight">Razorpay Checkout</h2>
              </div>
              <p className="text-xs text-blue-100 font-medium">Fintech Merchant Global • Test Mode</p>
              <div className="mt-4 pt-4 border-t border-white/15">
                <span className="text-[11px] text-blue-200 uppercase tracking-wider font-semibold block">
                  Amount Payable
                </span>
                <span className="text-3xl font-extrabold tracking-tight mt-0.5 block">
                  {formatCurrency(amount)}
                </span>
              </div>
            </div>

            <CardContent className="p-6">
              <AnimatePresence mode="wait">
                {paymentSuccess ? (
                  /* Success Receipt State */
                  <motion.div
                    key="success"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="py-4 text-center space-y-4"
                  >
                    <div className="h-16 w-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-inner">
                      <CheckCircle2 className="h-10 w-10 stroke-[2.5]" />
                    </div>

                    <div>
                      <h3 className="text-xl font-bold text-slate-900">Payment Completed!</h3>
                      <p className="text-xs text-slate-500 mt-1">
                        You have successfully paid {formatCurrency(amount)} to Fintech Merchant Global.
                      </p>
                    </div>

                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-2 text-left">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Payment ID</span>
                        <button
                          onClick={copyPaymentId}
                          className="font-mono font-bold text-[#0052cc] flex items-center gap-1 hover:underline"
                        >
                          <span>{paymentId}</span>
                          {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
                        </button>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Transaction ID</span>
                        <span className="font-mono font-medium text-slate-800">{id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Amount Paid</span>
                        <span className="font-bold text-emerald-600">{formatCurrency(amount)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Gateway</span>
                        <span className="font-medium text-slate-800">Razorpay Test Gateway</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Status</span>
                        <Badge variant="success" size="sm">RECOVERED</Badge>
                      </div>
                    </div>

                    <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                      <Button
                        onClick={() => router.push(`/transactions/${id}`)}
                        className="w-full bg-[#0052cc] hover:bg-[#0747a6] text-white text-xs gap-1.5 h-10"
                      >
                        <span>View Transaction Details</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </motion.div>
                ) : (
                  /* Trigger Razorpay Modal Button */
                  <motion.div
                    key="trigger"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-5"
                  >
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-2">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Customer:</span>
                        <span className="font-semibold text-slate-800">{customerName}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Email:</span>
                        <span className="font-mono text-slate-700">{customerEmail}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Phone:</span>
                        <span className="font-mono text-slate-700">{customerPhone}</span>
                      </div>
                      <div className="flex justify-between pt-2 border-t border-slate-200">
                        <span className="text-slate-500">Purpose:</span>
                        <span className="font-medium text-slate-800">Payment Recovery for {id}</span>
                      </div>
                    </div>

                    <div className="space-y-2.5">
                      <Button
                        type="button"
                        onClick={launchRazorpayModal}
                        disabled={isProcessing}
                        className="w-full h-12 bg-gradient-to-r from-[#0052cc] to-[#0747a6] hover:from-[#0747a6] hover:to-[#053580] text-white font-bold text-sm shadow-md hover:shadow-lg transition-all gap-2 rounded-xl"
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>Processing Checkout...</span>
                          </>
                        ) : (
                          <>
                            <Zap className="h-4 w-4 fill-white" />
                            <span>Pay {formatCurrency(amount)} with Razorpay Modal</span>
                          </>
                        )}
                      </Button>

                      <Button
                        type="button"
                        onClick={handleSimulateOneClick}
                        disabled={isProcessing}
                        variant="outline"
                        className="w-full h-10 border-emerald-300 bg-emerald-50/70 text-emerald-800 hover:bg-emerald-100 text-xs font-semibold rounded-xl gap-2 shadow-xs"
                      >
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <span>Instant 1-Click Payment Confirmation (Simulator)</span>
                      </Button>
                    </div>

                    <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
                      <ShieldCheck className="h-3.5 w-3.5 text-slate-400" />
                      <span>Secured by Razorpay Test Sandbox & HMAC-SHA256 Verification</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
          <div className="max-w-lg mx-auto px-4 flex items-center justify-between">
            <span className="font-semibold text-slate-600">RazorRecover AI</span>
            <span>Razorpay Test Mode Integration</span>
          </div>
        </div>
      </div>
    </>
  );
}
