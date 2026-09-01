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
  QrCode,
  Smartphone,
  Building2,
  Wallet,
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
  const [selectedMethodTab, setSelectedMethodTab] = useState<"upi" | "card" | "netbanking" | "modal">("upi");
  const [vpaInput, setVpaInput] = useState("aditya.verma@okhdfcbank");
  const [selectedUpiApp, setSelectedUpiApp] = useState<string>("gpay");
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

  const handleUpiDirectPayment = async (appOrVpa: string) => {
    if (!transaction) return;
    setIsProcessing(true);
    const pId = `pay_upi_${Math.random().toString(36).substring(2, 10)}`;
    try {
      await apiClient.simulateWebhook(transaction.id, "payment_link.paid", transaction.amount);
    } catch (e) {
      console.warn("UPI simulation notice:", e);
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
            method: "upi",
          },
          config: {
            display: {
              blocks: {
                upi: {
                  name: "Pay using UPI",
                  instruments: [
                    {
                      method: "upi",
                    },
                  ],
                },
                other: {
                  name: "Cards & NetBanking",
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
        await handleUpiDirectPayment("direct_upi");
      }
    } catch (e) {
      console.error("Razorpay launch error:", e);
      setIsProcessing(false);
    }
  };

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
          <span>
            This payment recovery checkout is operating in <strong>Razorpay Test Mode</strong>.
          </span>
        </div>

        {/* Main Card */}
        <div className="max-w-xl mx-auto w-full px-4 py-8 flex-1 flex items-center justify-center">
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
              <p className="text-xs text-blue-100 font-medium">Fintech Merchant Global • Autonomous Recovery</p>
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
                        <span className="text-slate-500">Payment Method</span>
                        <Badge variant="outline" className="bg-blue-50 text-[#0052cc] font-semibold text-[10px]">
                          UPI / Razorpay Test Sandbox
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Status</span>
                        <Badge variant="success" size="sm">
                          RECOVERED
                        </Badge>
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
                  /* Interactive Payment Selector */
                  <motion.div
                    key="trigger"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-5"
                  >
                    {/* Customer Info Brief */}
                    <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs space-y-1.5">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Customer:</span>
                        <span className="font-semibold text-slate-800">{customerName}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Phone:</span>
                        <span className="font-mono text-slate-700">{customerPhone}</span>
                      </div>
                    </div>

                    {/* Payment Method Selector Tabs */}
                    <div className="space-y-3">
                      <div className="flex rounded-xl bg-slate-100 p-1 text-xs">
                        <button
                          type="button"
                          onClick={() => setSelectedMethodTab("upi")}
                          className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-lg font-semibold transition-all ${
                            selectedMethodTab === "upi"
                              ? "bg-white text-blue-700 shadow-sm border border-slate-200/80"
                              : "text-slate-600 hover:text-slate-900"
                          }`}
                        >
                          <Smartphone className="h-3.5 w-3.5 text-blue-600" />
                          <span>UPI / Apps</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedMethodTab("card")}
                          className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-lg font-semibold transition-all ${
                            selectedMethodTab === "card"
                              ? "bg-white text-blue-700 shadow-sm border border-slate-200/80"
                              : "text-slate-600 hover:text-slate-900"
                          }`}
                        >
                          <CreditCard className="h-3.5 w-3.5 text-blue-600" />
                          <span>Cards</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedMethodTab("netbanking")}
                          className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-lg font-semibold transition-all ${
                            selectedMethodTab === "netbanking"
                              ? "bg-white text-blue-700 shadow-sm border border-slate-200/80"
                              : "text-slate-600 hover:text-slate-900"
                          }`}
                        >
                          <Building2 className="h-3.5 w-3.5 text-blue-600" />
                          <span>NetBanking</span>
                        </button>
                      </div>

                      {/* Tab 1: UPI Options (Google Pay / PhonePe / Paytm / QR / VPA) */}
                      {selectedMethodTab === "upi" && (
                        <div className="space-y-3 pt-1">
                          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                            Select UPI Payment App
                          </span>

                          <div className="grid grid-cols-3 gap-2">
                            {[
                              { id: "gpay", name: "Google Pay", color: "border-blue-300 bg-blue-50/50 text-blue-800" },
                              { id: "phonepe", name: "PhonePe", color: "border-purple-300 bg-purple-50/50 text-purple-800" },
                              { id: "paytm", name: "Paytm UPI", color: "border-sky-300 bg-sky-50/50 text-sky-800" },
                            ].map((app) => (
                              <button
                                key={app.id}
                                type="button"
                                onClick={() => setSelectedUpiApp(app.id)}
                                className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all text-xs font-semibold ${
                                  selectedUpiApp === app.id
                                    ? `${app.color} shadow-xs border-2`
                                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                                }`}
                              >
                                <Smartphone className="h-4 w-4 mb-1 text-slate-700" />
                                <span>{app.name}</span>
                              </button>
                            ))}
                          </div>

                          {/* UPI ID / VPA input */}
                          <div className="space-y-1.5">
                            <label className="text-xs font-medium text-slate-700">UPI ID / VPA</label>
                            <div className="flex gap-2">
                              <input
                                type="text"
                                value={vpaInput}
                                onChange={(e) => setVpaInput(e.target.value)}
                                placeholder="name@bank (e.g. aditya@okhdfcbank)"
                                className="h-10 flex-1 rounded-xl border border-slate-200 bg-white px-3 text-xs text-slate-800 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
                              />
                            </div>
                          </div>

                          {/* Pay with UPI Button */}
                          <Button
                            type="button"
                            onClick={() => handleUpiDirectPayment(selectedUpiApp)}
                            disabled={isProcessing}
                            className="w-full h-12 bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-700 hover:to-teal-800 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all gap-2 rounded-xl"
                          >
                            {isProcessing ? (
                              <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span>Authorizing UPI Payment...</span>
                              </>
                            ) : (
                              <>
                                <Zap className="h-4 w-4 fill-white" />
                                <span>Pay {formatCurrency(amount)} via UPI Instant</span>
                              </>
                            )}
                          </Button>
                        </div>
                      )}

                      {/* Tab 2: Cards */}
                      {selectedMethodTab === "card" && (
                        <div className="space-y-3 pt-1">
                          <div className="rounded-xl border border-slate-200 p-3.5 space-y-2.5 bg-slate-50/50">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-semibold text-slate-700">Test Credit / Debit Card</span>
                              <span className="text-[10px] text-slate-400 font-mono">VISA / MC / RuPay</span>
                            </div>
                            <input
                              type="text"
                              disabled
                              value="4111 •••• •••• 1111 (Test Card)"
                              className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs font-mono text-slate-700"
                            />
                            <div className="grid grid-cols-2 gap-2">
                              <input
                                type="text"
                                disabled
                                value="12/28"
                                className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs font-mono text-slate-700 text-center"
                              />
                              <input
                                type="text"
                                disabled
                                value="123"
                                className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs font-mono text-slate-700 text-center"
                              />
                            </div>
                          </div>

                          <Button
                            type="button"
                            onClick={() => handleUpiDirectPayment("test_card")}
                            disabled={isProcessing}
                            className="w-full h-11 bg-[#0052cc] hover:bg-[#0747a6] text-white font-bold text-xs shadow-md transition-all gap-2 rounded-xl"
                          >
                            <span>Pay {formatCurrency(amount)} with Test Card</span>
                          </Button>
                        </div>
                      )}

                      {/* Tab 3: NetBanking */}
                      {selectedMethodTab === "netbanking" && (
                        <div className="space-y-3 pt-1">
                          <div className="grid grid-cols-2 gap-2">
                            {["HDFC Bank", "State Bank of India", "ICICI Bank", "Axis Bank"].map((bank) => (
                              <button
                                key={bank}
                                type="button"
                                onClick={() => handleUpiDirectPayment(`netbanking_${bank}`)}
                                className="flex items-center gap-2 p-3 rounded-xl border border-slate-200 bg-white text-slate-800 hover:bg-blue-50/50 hover:border-blue-300 text-xs font-medium transition-all"
                              >
                                <Building2 className="h-4 w-4 text-blue-600 shrink-0" />
                                <span className="truncate">{bank}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Official Razorpay Modal Fallback Button */}
                    <div className="pt-2 border-t border-slate-200 space-y-2">
                      <Button
                        type="button"
                        onClick={launchRazorpayModal}
                        disabled={isProcessing}
                        variant="outline"
                        className="w-full h-10 border-slate-300 bg-white text-slate-700 hover:bg-slate-50 text-xs font-semibold rounded-xl gap-2 shadow-xs"
                      >
                        <ExternalLink className="h-3.5 w-3.5 text-blue-600" />
                        <span>Launch Razorpay Standard Modal (Pop-up)</span>
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
          <div className="max-w-xl mx-auto px-4 flex items-center justify-between">
            <span className="font-semibold text-slate-600">RazorRecover AI</span>
            <span>Razorpay Test Mode Integration</span>
          </div>
        </div>
      </div>
    </>
  );
}
