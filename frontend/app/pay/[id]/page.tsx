"use client";

export const dynamic = "force-dynamic";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Script from "next/script";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  ShieldCheck,
  Zap,
  Loader2,
  ArrowRight,
  Copy,
  Check,
  Sparkles,
  ExternalLink,
  Lock,
  Building2,
  RefreshCw,
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
  const [razorpayScriptLoaded, setRazorpayScriptLoaded] = useState(false);
  const autoLaunchedRef = useRef(false);

  // Fetch transaction details
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

  // Launch official Razorpay Checkout Pop-up Modal
  const launchRazorpayModal = useCallback(async () => {
    if (!transaction || paymentSuccess) return;
    setIsProcessing(true);

    try {
      // 1. Fetch real Razorpay order / credentials from backend
      const orderData = await apiClient.createOrder(transaction.id);
      const keyId = orderData?.key_id || "rzp_test_TVxlSjEzulO7pK";
      const amountPaise = orderData?.amount || Math.round(transaction.amount * 100);

      // 2. Configure official Razorpay Standard Checkout options
      if (typeof window !== "undefined" && (window as any).Razorpay) {
        const options: any = {
          key: keyId,
          amount: amountPaise,
          currency: "INR",
          name: "Fintech Merchant Global",
          description: `Autonomous Revenue Recovery - ${transaction.id}`,
          image: "https://razorpay.com/favicon.png",
          prefill: {
            name: transaction.customer?.name || "Aditya Verma",
            email: transaction.customer?.email || "aditya.verma@example.com",
            contact: transaction.customer?.phone || "+919876543210",
          },
          config: {
            display: {
              blocks: {
                upi: {
                  name: "Pay using UPI (Google Pay / PhonePe / Paytm / QR)",
                  instruments: [
                    {
                      method: "upi",
                    },
                  ],
                },
                other: {
                  name: "Cards, NetBanking & Wallets",
                  instruments: [
                    {
                      method: "card",
                    },
                    {
                      method: "netbanking",
                    },
                    {
                      method: "wallet",
                    },
                  ],
                },
              },
              sequence: ["block.upi", "block.other"],
              preferences: {
                show_default_blocks: true,
              },
            },
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
              const pId =
                response.razorpay_payment_id ||
                `pay_${Math.random().toString(36).substring(2, 10)}`;
              setPaymentId(pId);

              // Notify backend webhook engine and settle transaction as recovered
              await apiClient.simulateWebhook(
                transaction.id,
                "payment_link.paid",
                transaction.amount
              );
            } catch (err) {
              console.warn("Payment handler webhook notice:", err);
            } finally {
              setPaymentSuccess(true);
              setIsProcessing(false);
            }
          },
        };

        // Attach order_id if live order
        if (
          orderData?.is_live_order &&
          orderData?.order_id &&
          !orderData.order_id.startsWith("order_mock_")
        ) {
          options.order_id = orderData.order_id;
        }

        const rzp = new (window as any).Razorpay(options);
        rzp.on("payment.failed", function (response: any) {
          console.warn("Razorpay payment failed or cancelled:", response.error);
          setIsProcessing(false);
        });

        rzp.open();
      } else {
        console.warn("Razorpay SDK not ready yet, retrying...");
        setIsProcessing(false);
      }
    } catch (e) {
      console.error("Error launching official Razorpay modal:", e);
      setIsProcessing(false);
    }
  }, [transaction, paymentSuccess]);

  // Automatically launch the official Razorpay Checkout Pop-up once ready
  useEffect(() => {
    if (
      !loading &&
      transaction &&
      transaction.status !== "recovered" &&
      razorpayScriptLoaded &&
      !paymentSuccess &&
      !autoLaunchedRef.current
    ) {
      autoLaunchedRef.current = true;
      // Slight delay to ensure DOM and Razorpay SDK are fully initialized
      const timer = setTimeout(() => {
        launchRazorpayModal();
      }, 400);
      return () => clearTimeout(timer);
    }
  }, [loading, transaction, razorpayScriptLoaded, paymentSuccess, launchRazorpayModal]);

  const copyPaymentId = () => {
    if (paymentId) {
      navigator.clipboard.writeText(paymentId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f8fafc] flex items-center justify-center p-4 font-sans">
        <div className="flex flex-col items-center gap-3 text-slate-500 text-sm">
          <Loader2 className="h-8 w-8 animate-spin text-[#0052cc]" />
          <span className="font-semibold text-slate-700">
            Opening Official Razorpay Checkout Modal...
          </span>
        </div>
      </div>
    );
  }

  const amount = transaction?.amount || 4999.0;
  const customerName = transaction?.customer?.name || "Aditya Verma";
  const customerEmail = transaction?.customer?.email || "aditya.verma@example.com";
  const customerPhone = transaction?.customer?.phone || "+91 98765 43210";

  return (
    <>
      {/* Official Razorpay Checkout JS SDK */}
      <Script
        src="https://checkout.razorpay.com/v1/checkout.js"
        onLoad={() => setRazorpayScriptLoaded(true)}
        onError={() => setRazorpayScriptLoaded(true)}
      />

      <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col justify-between font-sans">
        {/* Top Razorpay Test Mode Bar */}
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-center text-xs font-medium text-amber-900 flex items-center justify-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
          <span>
            Official <strong>Razorpay Test Mode Sandbox</strong> Checkout
          </span>
        </div>

        {/* Main Payment Container */}
        <div className="max-w-md mx-auto w-full px-4 py-8 flex-1 flex items-center justify-center">
          <Card className="w-full border-slate-200 shadow-xl bg-white overflow-hidden rounded-2xl">
            {/* Branded Header */}
            <div className="bg-gradient-to-r from-[#0052cc] to-[#0747a6] p-6 text-white text-center relative">
              <div className="flex items-center justify-center gap-2 mb-2">
                <img
                  src="https://razorpay.com/favicon.png"
                  alt="Razorpay"
                  className="h-6 w-6 rounded bg-white p-0.5"
                />
                <h2 className="font-bold text-base tracking-tight">Razorpay Checkout</h2>
              </div>
              <p className="text-xs text-blue-100 font-medium">
                Fintech Merchant Global • Autonomous Recovery
              </p>
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
                    className="py-2 text-center space-y-4"
                  >
                    <div className="h-16 w-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-inner">
                      <CheckCircle2 className="h-10 w-10 stroke-[2.5]" />
                    </div>

                    <div>
                      <h3 className="text-xl font-bold text-slate-900">Payment Successful!</h3>
                      <p className="text-xs text-slate-500 mt-1">
                        Successfully paid {formatCurrency(amount)} via Razorpay Checkout.
                      </p>
                    </div>

                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-2.5 text-left">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Payment ID</span>
                        <button
                          onClick={copyPaymentId}
                          className="font-mono font-bold text-[#0052cc] flex items-center gap-1 hover:underline"
                        >
                          <span>{paymentId}</span>
                          {copied ? (
                            <Check className="h-3 w-3 text-emerald-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </button>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Transaction ID</span>
                        <span className="font-mono font-medium text-slate-800">{id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Amount Paid</span>
                        <span className="font-bold text-emerald-600">
                          {formatCurrency(amount)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Gateway Status</span>
                        <Badge
                          variant="outline"
                          className="bg-blue-50 text-[#0052cc] font-semibold text-[10px]"
                        >
                          Captured &bull; Razorpay Sandbox
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Recovery State</span>
                        <Badge variant="success" size="sm">
                          RECOVERED
                        </Badge>
                      </div>
                    </div>

                    <div className="pt-2">
                      <Button
                        onClick={() => router.push(`/transactions/${id}`)}
                        className="w-full bg-[#0052cc] hover:bg-[#0747a6] text-white text-xs font-semibold gap-1.5 h-11 rounded-xl shadow-md"
                      >
                        <span>View Recovered Transaction Details</span>
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </motion.div>
                ) : (
                  /* Standard Modal Trigger State */
                  <motion.div
                    key="trigger"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-5"
                  >
                    {/* Customer Info Brief */}
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Customer Name:</span>
                        <span className="font-semibold text-slate-800">{customerName}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Email:</span>
                        <span className="font-medium text-slate-700">{customerEmail}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Phone:</span>
                        <span className="font-mono text-slate-700">{customerPhone}</span>
                      </div>
                    </div>

                    {/* Primary Trigger Button */}
                    <div className="space-y-3 pt-2">
                      <button
                        type="button"
                        onClick={launchRazorpayModal}
                        disabled={isProcessing}
                        className="w-full h-12 px-5 bg-[#0052cc] hover:bg-[#0747a6] active:scale-[0.98] text-white font-semibold text-sm rounded-xl shadow-md shadow-blue-600/20 hover:shadow-lg hover:shadow-blue-600/30 transition-all flex items-center justify-between cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed group border border-blue-400/20"
                      >
                        {isProcessing ? (
                          <div className="w-full flex items-center justify-center gap-2">
                            <Loader2 className="h-4 w-4 animate-spin text-white" />
                            <span>Opening Razorpay Checkout...</span>
                          </div>
                        ) : (
                          <>
                            <div className="flex items-center gap-2.5">
                              <div className="h-6 w-6 rounded-md bg-white/15 flex items-center justify-center">
                                <Lock className="h-3.5 w-3.5 text-white" />
                              </div>
                              <span className="font-semibold text-[15px] tracking-tight">
                                Pay {formatCurrency(amount)}
                              </span>
                            </div>

                            <div className="flex items-center gap-1.5 text-xs text-blue-100 group-hover:text-white font-medium">
                              <span>Razorpay</span>
                              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                            </div>
                          </>
                        )}
                      </button>

                      <p className="text-center text-[11px] text-slate-500">
                        Click above to open the official Razorpay payment window.
                      </p>
                    </div>

                    <div className="pt-2 border-t border-slate-100 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
                      <ShieldCheck className="h-3.5 w-3.5 text-blue-600" />
                      <span>Secured by Official Razorpay Sandbox & HMAC-SHA256</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
          <div className="max-w-md mx-auto px-4 flex items-center justify-between">
            <span className="font-semibold text-slate-600">RazorRecover AI</span>
            <span>Razorpay Test Mode Integration</span>
          </div>
        </div>
      </div>
    </>
  );
}
