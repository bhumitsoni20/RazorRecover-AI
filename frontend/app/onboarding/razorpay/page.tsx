"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { apiClient } from "@/lib/api-client";
import {
  ShieldCheck,
  CreditCard,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Zap,
  Building2,
  AlertCircle,
  Loader2,
  KeyRound,
} from "lucide-react";

export default function OnboardingRazorpayPage() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();

  const [accountId, setAccountId] = useState("");
  const [businessCategory, setBusinessCategory] = useState("ecommerce");
  const [testModeEnabled, setTestModeEnabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (user?.razorpay_account_id) {
      setAccountId(user.razorpay_account_id);
    }
  }, [user]);

  const handleGenerateAccountId = () => {
    const randomHex = Math.random().toString(36).substring(2, 8).toLowerCase();
    setAccountId(`acc_rzp_demo_${randomHex}`);
    setError(null);
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setStatusMessage(null);

    try {
      const updated = await apiClient.connectRazorpay({
        razorpay_account_id: accountId.trim() || undefined,
        business_category: businessCategory,
        test_mode_enabled: testModeEnabled,
      });

      await refreshUser();

      if (updated.verification_status === "VERIFIED") {
        router.push("/dashboard");
      } else {
        router.push("/verification-pending");
      }
    } catch (err: any) {
      setError(err.message || "Failed to connect Razorpay account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-8 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-lg space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25">
            <CreditCard className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Connect Razorpay Account
          </h1>
          <p className="text-sm text-slate-500">
            Step 1 of 2: Link your payment gateway account for autonomous recovery actions
          </p>
        </div>

        {/* Current Merchant Card */}
        {user && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-900">
                  {user.business_name}
                </p>
                <p className="text-[11px] text-slate-500">{user.email}</p>
              </div>
            </div>
            <span
              className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full border ${
                user.razorpay_connection_status === "CONNECTED"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-amber-50 text-amber-700 border-amber-200"
              }`}
            >
              {user.razorpay_connection_status}
            </span>
          </div>
        )}

        {/* Connection Form */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
          {error && (
            <div className="mb-5 flex items-start gap-2.5 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 animate-in fade-in">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleConnect} className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  Razorpay Account ID / Mid
                </label>
                <button
                  type="button"
                  onClick={handleGenerateAccountId}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-700 hover:underline"
                >
                  <Sparkles className="h-3 w-3" />
                  <span>Generate Test Account ID</span>
                </button>
              </div>
              <div className="relative">
                <KeyRound className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  required
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  placeholder="acc_rzp_demo_electronics"
                  className="w-full rounded-lg border border-slate-200 bg-slate-50/50 pl-9 pr-3.5 py-2 text-sm font-mono text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Merchant Business Category
              </label>
              <select
                value={businessCategory}
                onChange={(e) => setBusinessCategory(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-slate-50/50 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
              >
                <option value="ecommerce">E-Commerce &amp; Retail</option>
                <option value="saas">SaaS &amp; Digital Subscriptions</option>
                <option value="fintech">Fintech &amp; Financial Services</option>
                <option value="education">EdTech &amp; Courses</option>
                <option value="travel">Travel &amp; Hospitality</option>
              </select>
            </div>

            <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-3.5 space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={testModeEnabled}
                  onChange={(e) => setTestModeEnabled(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-xs font-semibold text-blue-950">
                  Enable Razorpay Test Mode Sandbox Integration
                </span>
              </label>
              <p className="text-[11px] text-blue-800/80 leading-relaxed pl-6">
                Allows RazorRecover AI to generate secure Payment Links and process mock webhook recoveries without touching live production settlement accounts.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || !accountId}
              className="w-full mt-3 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 py-2.5 px-4 text-sm font-semibold text-white shadow-md shadow-blue-500/20 hover:opacity-95 active:scale-[0.99] disabled:opacity-50 transition-all"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Connecting Account...</span>
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  <span>Connect &amp; Proceed to Verification</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
