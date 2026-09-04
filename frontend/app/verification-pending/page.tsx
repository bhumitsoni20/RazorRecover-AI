"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { apiClient } from "@/lib/api-client";
import {
  Clock,
  ShieldCheck,
  Building2,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  RefreshCw,
  AlertCircle,
  Loader2,
  Lock,
} from "lucide-react";

export default function VerificationPendingPage() {
  const router = useRouter();
  const { user, refreshUser, devVerify } = useAuth();

  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.verification_status === "VERIFIED") {
      router.push("/dashboard");
    }
  }, [user, router]);

  const handleCheckStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const status = await apiClient.getOnboardingStatus();
      if (status?.can_access_dashboard || status?.verification_status === "VERIFIED") {
        await refreshUser();
        router.push("/dashboard");
      } else {
        setMessage("Your merchant application is currently under automated compliance review.");
      }
    } catch (err: any) {
      setError(err.message || "Could not check verification status.");
    } finally {
      setLoading(false);
    }
  };

  const handleDevQuickVerify = async () => {
    setVerifying(true);
    setError(null);
    try {
      await devVerify("VERIFIED", "Instant demo verification triggered from UI console");
      await refreshUser();
      setMessage("Account successfully verified! Redirecting to dashboard...");
      setTimeout(() => {
        router.push("/dashboard");
      }, 1000);
    } catch (err: any) {
      setError(err.message || "Failed to trigger dev verification.");
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-8 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-lg space-y-6">
        {/* Header Badge */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 shadow-sm animate-pulse">
            <Clock className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Merchant Verification Pending
          </h1>
          <p className="text-sm text-slate-500">
            Step 2 of 2: Your merchant account is awaiting verification approval before dashboard access is unlocked
          </p>
        </div>

        {/* Merchant Info Card */}
        {user && (
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                  <Building2 className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-slate-900">
                    {user.business_name}
                  </h2>
                  <p className="text-xs text-slate-500">{user.email}</p>
                </div>
              </div>
              <span className="text-[11px] font-mono font-semibold px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                {user.verification_status}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 pt-1">
              <div>
                <span className="text-slate-400 block text-[10px]">Razorpay Account:</span>
                <span className="font-mono text-slate-800">
                  {user.razorpay_account_id || "acc_demo_fashion"}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Gateway Status:</span>
                <span className="font-semibold text-emerald-600">
                  {user.razorpay_connection_status}
                </span>
              </div>
            </div>
          </div>
        )}

        {message && (
          <div className="flex items-start gap-2.5 rounded-lg border border-emerald-200 bg-emerald-50 p-3.5 text-xs text-emerald-800 animate-in fade-in">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />
            <span>{message}</span>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2.5 rounded-lg border border-rose-200 bg-rose-50 p-3.5 text-xs text-rose-800 animate-in fade-in">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Verification Check & Dev Controls */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
          <button
            type="button"
            onClick={handleCheckStatus}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 py-2.5 px-4 text-xs font-semibold text-slate-800 transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-slate-600" />
                <span>Checking Gateway Status...</span>
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 text-slate-500" />
                <span>Refresh Verification Status</span>
              </>
            )}
          </button>

          {/* Dev Demo Instant Verify Callout */}
          <div className="rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50/80 via-indigo-50/50 to-white p-4 space-y-3">
            <div className="flex items-center gap-1.5 text-xs font-bold text-blue-900">
              <Sparkles className="h-4 w-4 text-blue-600" />
              <span>Development / Evaluation Quick-Action</span>
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              In development mode, you can instantly transition this merchant account from <strong className="text-amber-700">PENDING</strong> to <strong className="text-emerald-700">VERIFIED</strong> with cryptographically sealed audit logging.
            </p>
            <button
              type="button"
              onClick={handleDevQuickVerify}
              disabled={verifying}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 py-2.5 px-4 text-xs font-semibold text-white shadow-md shadow-blue-500/20 hover:opacity-95 active:scale-[0.99] disabled:opacity-50 transition-all"
            >
              {verifying ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Sealing Verification in Audit Trail...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4" />
                  <span>Instant Verify Account &amp; Unlock Dashboard</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Security Notice */}
        <div className="flex items-center justify-center gap-2 text-center text-[11px] text-slate-400">
          <Lock className="h-3.5 w-3.5" />
          <span>Restricted Route Gating: Access to /dashboard requires VERIFIED status</span>
        </div>
      </div>
    </div>
  );
}
