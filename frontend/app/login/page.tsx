"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  ShieldCheck,
  Lock,
  Mail,
  ArrowRight,
  Sparkles,
  Store,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const res = await login(email, password);
      if (res.redirect_url) {
        router.push(res.redirect_url);
      } else {
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-8 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            RazorRecover <span className="text-blue-600 font-extrabold">AI</span>
          </h1>
          <p className="text-sm text-slate-500">
            Sign in to access your autonomous revenue recovery console
          </p>
        </div>

        {/* Demo Quick-Fill Callout */}
        <div className="rounded-xl border border-blue-100 bg-gradient-to-b from-blue-50/70 to-white p-4 shadow-xs">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-900 mb-2.5">
            <Sparkles className="h-3.5 w-3.5 text-blue-600" />
            <span>Interactive Demo Merchant Accounts</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() =>
                handleQuickLogin("merchant1@demo.razorrecover.ai", "DemoMerchant123!")
              }
              className="text-left p-2.5 rounded-lg border border-emerald-200/80 bg-white hover:border-emerald-400 hover:shadow-xs transition-all group"
            >
              <div className="flex items-center justify-between text-[11px] font-semibold text-emerald-700">
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> Merchant 1
                </span>
                <span className="text-[9px] bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded font-mono">
                  VERIFIED
                </span>
              </div>
              <p className="text-[10px] text-slate-500 mt-1 truncate">
                Demo Electronics
              </p>
            </button>

            <button
              type="button"
              onClick={() =>
                handleQuickLogin("merchant2@demo.razorrecover.ai", "DemoMerchant123!")
              }
              className="text-left p-2.5 rounded-lg border border-amber-200/80 bg-white hover:border-amber-400 hover:shadow-xs transition-all group"
            >
              <div className="flex items-center justify-between text-[11px] font-semibold text-amber-700">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" /> Merchant 2
                </span>
                <span className="text-[9px] bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded font-mono">
                  PENDING
                </span>
              </div>
              <p className="text-[10px] text-slate-500 mt-1 truncate">
                Demo Fashion Store
              </p>
            </button>
          </div>
        </div>

        {/* Login Form Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
          {error && (
            <div className="mb-5 flex items-start gap-2.5 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 animate-in fade-in">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Merchant Work Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="merchant@example.com"
                  className="w-full rounded-lg border border-slate-200 bg-slate-50/50 pl-9 pr-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full rounded-lg border border-slate-200 bg-slate-50/50 pl-9 pr-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 py-2.5 px-4 text-sm font-semibold text-white shadow-md shadow-blue-500/20 hover:opacity-95 active:scale-[0.99] disabled:opacity-50 transition-all"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-500">
              Don't have a merchant account?{" "}
              <Link
                href="/signup"
                className="font-semibold text-blue-600 hover:text-blue-700 underline underline-offset-2"
              >
                Register as Merchant
              </Link>
            </p>
          </div>
        </div>

        {/* Security Footer Notice */}
        <div className="flex items-center justify-center gap-2 text-center text-[11px] text-slate-400">
          <Store className="h-3.5 w-3.5" />
          <span>Multi-Tenant Isolated Merchant Cloud &bull; SHA-256 Audit Sealed</span>
        </div>
      </div>
    </div>
  );
}
