"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  ExternalLink,
  AlertTriangle,
  Zap,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { TransactionListItem } from "@/types/api";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { PageTransition, staggerContainer, itemFadeUp } from "@/components/animations/page-transition";

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<TransactionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [methodFilter, setMethodFilter] = useState("all");

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getTransactions(statusFilter, methodFilter, search);
      setTransactions(res.items);
    } catch (e) {
      console.error("Failed to load transactions:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [statusFilter, methodFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadTransactions();
  };

  return (
    <PageTransition className="space-y-6">
      {/* Header */}
      <motion.div
        variants={itemFadeUp}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Transactions Explorer & Risk Stream
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Real-time feed of merchant checkouts, deterministic loss probability, and AI recovery status
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadTransactions} className="gap-1.5 hover:shadow-xs transition-all">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
          <Link href="/transactions/txn_4999_upi">
            <Button size="sm" className="gap-1.5 bg-[#0052cc] hover:shadow-md hover:scale-[1.02] transition-all">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Demo ₹4,999 Case</span>
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* Filters Bar */}
      <motion.div variants={itemFadeUp}>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row items-center gap-3">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by customer name, email, or transaction ID (e.g. txn_4999)..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="h-9 w-full rounded-lg border border-slate-200 bg-slate-50/50 pl-9 pr-4 text-xs text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none transition-colors"
                />
              </div>

              <div className="flex flex-wrap sm:flex-nowrap items-center gap-2 w-full md:w-auto">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="h-9 flex-1 sm:flex-initial rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-700 focus:outline-none cursor-pointer"
                >
                  <option value="all">All Statuses</option>
                  <option value="failed">Failed</option>
                  <option value="pending">Pending</option>
                  <option value="recovered">Recovered</option>
                  <option value="success">Success</option>
                </select>

                <select
                  value={methodFilter}
                  onChange={(e) => setMethodFilter(e.target.value)}
                  className="h-9 flex-1 sm:flex-initial rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-700 focus:outline-none cursor-pointer"
                >
                  <option value="all">All Methods</option>
                  <option value="upi">UPI</option>
                  <option value="card">Card</option>
                  <option value="netbanking">NetBanking</option>
                  <option value="subscription">Subscription</option>
                </select>

                <Button type="submit" variant="secondary" size="sm" className="h-9 px-4 w-full sm:w-auto hover:bg-slate-200 transition-all">
                  Search
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </motion.div>

      {/* Transactions Table */}
      <motion.div variants={itemFadeUp}>
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs min-w-[750px]">
                <thead className="bg-slate-50/75 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">ID / Time</th>
                    <th className="px-4 py-3">Customer</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Method & Bank</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Risk Level</th>
                    <th className="px-4 py-3">Loss Prob. / At Risk</th>
                    <th className="px-4 py-3 text-right">Investigation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transactions.map((txn, idx) => {
                    const isRecovered = txn.status === "recovered";
                    const isFailed = txn.status === "failed";
                    const isPending = txn.status === "pending";

                    const riskLevel = txn.risk_level || (
                      (txn.loss_probability ?? 0.5) >= 0.75 ? "CRITICAL"
                      : (txn.loss_probability ?? 0.5) >= 0.50 ? "HIGH"
                      : (txn.loss_probability ?? 0.5) >= 0.25 ? "MEDIUM"
                      : "LOW"
                    );

                    return (
                      <motion.tr
                        key={txn.id}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2, delay: idx * 0.03 }}
                        className="hover:bg-slate-50/60 transition-colors"
                      >
                        <td className="px-4 py-3.5 font-mono">
                          <div className="font-semibold text-slate-900">{txn.id}</div>
                          <div className="text-[10px] text-slate-400">{txn.created_at}</div>
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="font-semibold text-slate-800">{txn.customer_name}</div>
                          <div className="text-[10px] text-slate-400">{txn.customer_email}</div>
                        </td>
                        <td className="px-4 py-3.5 font-bold text-slate-900">
                          {formatCurrency(txn.amount)}
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="font-medium text-slate-800 uppercase text-[11px]">
                            {txn.payment_method}
                          </div>
                          {txn.bank && (
                            <div className="text-[10px] text-slate-400 font-medium">{txn.bank}</div>
                          )}
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge
                            variant={
                              isRecovered ? "success" : isFailed ? "danger" : isPending ? "warning" : "neutral"
                            }
                            size="sm"
                          >
                            {txn.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5">
                          {txn.status !== "success" && !isRecovered ? (
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold tracking-wide ${
                                riskLevel === "CRITICAL"
                                  ? "bg-red-100 text-red-800 border border-red-300"
                                  : riskLevel === "HIGH"
                                  ? "bg-orange-100 text-orange-800 border border-orange-300"
                                  : riskLevel === "MEDIUM"
                                  ? "bg-amber-100 text-amber-800 border border-amber-300"
                                  : "bg-emerald-100 text-emerald-800 border border-emerald-300"
                              }`}
                            >
                              {riskLevel}
                            </span>
                          ) : (
                            <span className="text-slate-400 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3.5">
                          {txn.status !== "success" && !isRecovered && txn.loss_probability !== undefined ? (
                            <div>
                              <div className="font-bold text-red-600">
                                {formatCurrency(txn.revenue_at_risk || txn.amount * (txn.loss_probability || 0.5))}
                              </div>
                              <div className="text-[10px] text-slate-500 font-mono">
                                {roundPct(txn.loss_probability * 100)}% loss prob.
                              </div>
                            </div>
                          ) : isRecovered ? (
                            <span className="text-emerald-600 font-medium text-xs">Recovered</span>
                          ) : (
                            <span className="text-slate-400 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <Link href={`/transactions/${txn.id}`}>
                            <Button variant="outline" size="sm" className="h-7 px-2.5 text-xs gap-1 hover:border-blue-400 hover:text-[#0052cc] transition-all">
                              <span>Investigate</span>
                              <ArrowRight className="h-3 w-3" />
                            </Button>
                          </Link>
                        </td>
                      </motion.tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </PageTransition>
  );
}

function roundPct(val: number): string {
  return val.toFixed(1);
}
