"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  TrendingUp,
  AlertTriangle,
  Sparkles,
  ArrowUpRight,
  ShieldCheck,
  Zap,
  CheckCircle2,
  Clock,
  ChevronRight,
  RefreshCw,
  Activity,
  AlertCircle,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { DashboardSummaryResponse } from "@/types/api";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { AnimatedCounter } from "@/components/animations/animated-counter";
import { PageTransition, staggerContainer, itemFadeUp } from "@/components/animations/page-transition";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getDashboardSummary();
      setData(res);
    } catch (err) {
      console.error("Failed to load dashboard summary:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const metrics = data?.metrics;

  return (
    <PageTransition className="space-y-6">
      {/* Top Banner / Welcome */}
      <motion.div
        variants={itemFadeUp}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Revenue Recovery Hub
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Real-time autonomous multi-agent revenue recovery & AI loss risk detection
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={loadData} className="gap-1.5 hover:shadow-xs transition-all">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
          <Link href="/transactions/txn_4999_upi">
            <Button size="sm" className="gap-1.5 bg-gradient-to-r from-[#0052cc] to-[#1e40af] shadow-sm hover:shadow-md hover:scale-[1.02] transition-all">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Investigate Failed ₹4,999</span>
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* Anomaly Detection Banner */}
      {metrics?.anomaly_detected ? (
        <motion.div
          variants={itemFadeUp}
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="rounded-xl border border-amber-300 bg-amber-50/90 p-4 shadow-sm"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-600 text-white shadow-xs">
                <AlertTriangle className="h-4 w-4" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-bold uppercase tracking-wider text-amber-900">
                    Payment Failure Rate Anomaly Detected
                  </span>
                  <Badge variant="warning" size="sm" className="animate-pulse">
                    Live Incident
                  </Badge>
                </div>
                <p className="text-xs text-amber-800 mt-1 leading-relaxed">
                  {metrics.anomaly_message || "Abnormal payment failure spike detected in recent checkout traffic. Autonomous payment link fallback active."}
                </p>
              </div>
            </div>
            <Link href="/agents" className="self-end sm:self-auto shrink-0">
              <Button variant="outline" size="sm" className="bg-white border-amber-300 text-amber-900 hover:bg-amber-100/50 text-xs">
                View Root Cause
              </Button>
            </Link>
          </div>
        </motion.div>
      ) : (
        <motion.div
          variants={itemFadeUp}
          className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-3.5 flex items-center justify-between shadow-xs"
        >
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-600 text-white">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-emerald-950 uppercase tracking-wider">
                Payment Networks & Gateways Stable
              </span>
              <p className="text-[11px] text-emerald-700">
                All payment methods (UPI, Card, Netbanking) operating within normal failure rate baselines.
              </p>
            </div>
          </div>
          <Badge variant="success" size="sm">
            Optimal
          </Badge>
        </motion.div>
      )}

      {/* 4 Core KPI Metrics with Animated Counters */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {/* Metric 1: Revenue at Risk */}
        <motion.div variants={itemFadeUp} whileHover={{ y: -3 }} transition={{ duration: 0.2 }}>
          <Card className="border-slate-200/90 hover:shadow-md transition-shadow">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Revenue At Risk
                </span>
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 text-red-600">
                  <AlertTriangle className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-slate-900">
                  {metrics ? (
                    <AnimatedCounter value={metrics.revenue_at_risk} prefix="₹" />
                  ) : (
                    "₹0"
                  )}
                </span>
              </div>
              <div className="mt-2 flex items-center text-xs text-slate-500">
                <span className="font-semibold text-red-600 mr-1.5 flex items-center">
                  Loss prob. weighted
                </span>
                <span>across failed txns</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Metric 2: Recovered Revenue */}
        <motion.div variants={itemFadeUp} whileHover={{ y: -3 }} transition={{ duration: 0.2 }}>
          <Card className="border-slate-200/90 hover:shadow-md transition-shadow">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Recovered Revenue
                </span>
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                  <TrendingUp className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-slate-900">
                  {metrics ? (
                    <AnimatedCounter value={metrics.recovered_revenue} prefix="₹" />
                  ) : (
                    "₹0"
                  )}
                </span>
              </div>
              <div className="mt-2 flex items-center text-xs text-slate-500">
                <span className="font-semibold text-emerald-600 mr-1.5 flex items-center">
                  Verified payments
                </span>
                <span>via payment links</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Metric 3: Recovery Rate */}
        <motion.div variants={itemFadeUp} whileHover={{ y: -3 }} transition={{ duration: 0.2 }}>
          <Card className="border-slate-200/90 hover:shadow-md transition-shadow">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Recovery Rate
                </span>
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-[#0052cc]">
                  <Zap className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-slate-900">
                  {metrics ? (
                    <AnimatedCounter value={metrics.recovery_rate} suffix="%" decimals={1} />
                  ) : (
                    "0.0%"
                  )}
                </span>
              </div>
              <div className="mt-2 flex items-center text-xs text-slate-500">
                <span className="font-semibold text-blue-600 mr-1.5">
                  Autonomous
                </span>
                <span>success yield</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Metric 4: Active AI Actions */}
        <motion.div variants={itemFadeUp} whileHover={{ y: -3 }} transition={{ duration: 0.2 }}>
          <Card className="border-slate-200/90 hover:shadow-md transition-shadow">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Active AI Actions
                </span>
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-50 text-purple-600">
                  <Sparkles className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-slate-900">
                  {metrics ? (
                    <AnimatedCounter value={metrics.active_actions_count} />
                  ) : (
                    "0"
                  )}
                </span>
                {metrics && metrics.pending_human_approvals > 0 && (
                  <span className="text-xs font-medium text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                    {metrics.pending_human_approvals} for approval
                  </span>
                )}
              </div>
              <div className="mt-2 flex items-center text-xs text-slate-500">
                <span className="font-semibold text-purple-600 mr-1.5">
                  Autonomous
                </span>
                <span>under guardrails</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Main Row: Recovery Trend Chart + Revenue Leakage Breakdown */}
      <motion.div variants={itemFadeUp} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle>Revenue Recovery Trend</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Daily comparison of revenue at risk vs autonomous recovery (Last 7 Days)
              </p>
            </div>
            <Badge variant="default" size="sm">
              Live Database
            </Badge>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="h-64 w-full">
              {data?.trend && data.trend.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.trend} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorRecovered" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                      </linearGradient>
                      <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0052cc" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#0052cc" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} tickFormatter={(v) => `₹${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`} />
                    <Tooltip
                      formatter={(value: any) => [`₹${Number(value).toLocaleString("en-IN")}`, ""]}
                      contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0", fontSize: "12px" }}
                    />
                    <Area type="monotone" dataKey="revenue_at_risk" name="At Risk" stroke="#0052cc" strokeWidth={2} fillOpacity={1} fill="url(#colorRisk)" />
                    <Area type="monotone" dataKey="revenue_recovered" name="Recovered" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorRecovered)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  {loading ? "Loading trend data..." : "No trend data available."}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Revenue Leakage Breakdown */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Revenue Leakage Sources</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Calculated breakdown across failure categories
            </p>
          </CardHeader>
          <CardContent className="pt-3 space-y-4">
            {data?.leakage_breakdown && data.leakage_breakdown.length > 0 ? (
              data.leakage_breakdown.map((item, i) => (
                <motion.div
                  key={item.category}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.1 }}
                  className="space-y-1.5"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700">{item.category}</span>
                    <span className="font-bold text-slate-900">{formatCurrency(item.amount)}</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                    <motion.div
                      className="h-full rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${item.percentage}%` }}
                      transition={{ duration: 0.8, ease: "easeOut", delay: i * 0.1 }}
                      style={{ backgroundColor: item.color }}
                    />
                  </div>
                  <div className="flex justify-end text-[10px] text-slate-400 font-medium">
                    {item.percentage}% of total risk
                  </div>
                </motion.div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-400">
                {loading ? "Calculating leakage breakdown..." : "No active leakage detected."}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* AI Recovery Queue Table */}
      <motion.div variants={itemFadeUp}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-[#0052cc]" />
                <span>Autonomous AI Recovery Queue</span>
              </CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Failed checkouts investigated and evaluated with deterministic loss risk
              </p>
            </div>
            <Link href="/transactions">
              <Button variant="ghost" size="sm" className="gap-1 text-xs text-[#0052cc]">
                <span>View All Transactions</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs min-w-[700px]">
                <thead className="bg-slate-50/75 border-y border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Transaction</th>
                    <th className="px-4 py-3">Customer</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Issue Detected</th>
                    <th className="px-4 py-3">AI Recommendation</th>
                    <th className="px-4 py-3">Recovery Prob.</th>
                    <th className="px-4 py-3">Policy Check</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data?.recent_queue && data.recent_queue.length > 0 ? (
                    data.recent_queue.map((item, idx) => (
                      <motion.tr
                        key={item.transaction_id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.2, delay: idx * 0.03 }}
                        className="hover:bg-slate-50/60 transition-colors"
                      >
                        <td className="px-4 py-3.5 font-mono">
                          <span className="font-semibold text-slate-900">{item.transaction_id}</span>
                          <span className="block text-[10px] text-slate-400">{item.created_at}</span>
                        </td>
                        <td className="px-4 py-3.5 font-medium text-slate-800">
                          {item.customer_name}
                        </td>
                        <td className="px-4 py-3.5 font-bold text-slate-900">
                          {formatCurrency(item.amount)}
                        </td>
                        <td className="px-4 py-3.5">
                          <span className="rounded bg-red-50 px-2 py-0.5 text-[11px] font-mono text-red-700 border border-red-200">
                            {item.failure_reason}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          <span className="font-medium text-slate-800 capitalize">
                            {item.ai_recommendation.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-1.5">
                            <div className="h-1.5 w-12 rounded-full bg-slate-100 overflow-hidden">
                              <div
                                className="h-full bg-emerald-500"
                                style={{ width: `${item.recovery_probability * 100}%` }}
                              />
                            </div>
                            <span className="font-semibold text-emerald-700">
                              {formatPercentage(item.recovery_probability * 100)}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge
                            variant={
                              item.policy_decision === "APPROVED"
                                ? "success"
                                : item.policy_decision === "BLOCKED"
                                ? "danger"
                                : "warning"
                            }
                            size="sm"
                          >
                            {item.policy_decision === "HUMAN_APPROVAL_REQUIRED" ? "Human Review" : item.policy_decision}
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <Link href={`/transactions/${item.transaction_id}`}>
                            <Button variant="outline" size="sm" className="h-7 px-2.5 text-xs gap-1 hover:border-blue-400 hover:text-[#0052cc] transition-all">
                              <span>Investigate</span>
                              <ChevronRight className="h-3 w-3" />
                            </Button>
                          </Link>
                        </td>
                      </motion.tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-400">
                        {loading ? "Loading AI recovery queue..." : "No recent transactions found."}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </PageTransition>
  );
}
