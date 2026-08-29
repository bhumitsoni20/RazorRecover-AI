"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  XCircle,
  ArrowRight,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api-client";
import { RecoveryActionItem } from "@/types/api";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { PageTransition, itemFadeUp } from "@/components/animations/page-transition";

export default function RecoveryPage() {
  const [actions, setActions] = useState<RecoveryActionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");

  const loadActions = async () => {
    setLoading(true);
    const res = await apiClient.getRecoveryActions(activeTab);
    setActions(res);
    setLoading(false);
  };

  useEffect(() => {
    loadActions();
  }, [activeTab]);

  const handleApprove = async (transactionId: string) => {
    await apiClient.approveRecovery(transactionId, true);
    loadActions();
  };

  const handleReject = async (transactionId: string) => {
    await apiClient.approveRecovery(transactionId, false);
    loadActions();
  };

  const filteredActions = actions.filter((act) => {
    if (activeTab === "all") return true;
    if (activeTab === "pending_approval") return act.policy_decision === "HUMAN_APPROVAL_REQUIRED" && act.status === "pending";
    if (activeTab === "recovered") return act.status === "recovered";
    if (activeTab === "automated") return act.policy_decision === "APPROVED";
    return true;
  });

  return (
    <PageTransition className="space-y-6">
      {/* Header */}
      <motion.div
        variants={itemFadeUp}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Autonomous Recovery Hub
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Monitor autonomous payment links, retry schedules, and human approval queues
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={loadActions} className="gap-1.5 hover:shadow-xs transition-all">
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh Queue</span>
          </Button>
        </div>
      </motion.div>

      {/* Tabs Filter */}
      <motion.div variants={itemFadeUp}>
        <Tabs
          tabs={[
            { id: "all", label: "All Recovery Actions", count: actions.length },
            { id: "pending_approval", label: "Requires Human Review", count: actions.filter(a => a.policy_decision === "HUMAN_APPROVAL_REQUIRED" && a.status === "pending").length },
            { id: "automated", label: "Autonomous Actions", count: actions.filter(a => a.policy_decision === "APPROVED").length },
            { id: "recovered", label: "Recovered Revenue", count: actions.filter(a => a.status === "recovered").length },
          ]}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      </motion.div>

      {/* Actions Grid / List */}
      <motion.div variants={itemFadeUp}>
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/75 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Transaction</th>
                    <th className="px-4 py-3">Customer</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Action Type</th>
                    <th className="px-4 py-3">Policy Verdict</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Recovered Amount</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredActions.map((act, idx) => {
                    const needsApproval = act.policy_decision === "HUMAN_APPROVAL_REQUIRED" && act.status === "pending";
                    const isRecovered = act.status === "recovered";

                    return (
                      <motion.tr
                        key={act.id}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2, delay: idx * 0.04 }}
                        className="hover:bg-slate-50/60 transition-colors"
                      >
                        <td className="px-4 py-3.5 font-mono font-medium text-slate-900">
                          <Link href={`/transactions/${act.transaction_id}`} className="hover:underline text-[#0052cc]">
                            {act.transaction_id}
                          </Link>
                        </td>
                        <td className="px-4 py-3.5 font-semibold text-slate-800">
                          {act.customer_name}
                        </td>
                        <td className="px-4 py-3.5 font-bold text-slate-900">
                          {formatCurrency(act.amount)}
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-1.5 font-medium text-slate-800">
                            <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                            <span className="capitalize">{act.action_type.replace("_", " ")}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 mt-0.5">{act.reason}</div>
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge
                            variant={act.policy_decision === "APPROVED" ? "success" : act.policy_decision === "BLOCKED" ? "danger" : "warning"}
                            size="sm"
                          >
                            {act.policy_decision}
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge
                            variant={isRecovered ? "success" : act.status === "pending" ? "warning" : "default"}
                            size="sm"
                          >
                            {act.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5 font-bold text-emerald-600">
                          {act.amount_recovered > 0 ? formatCurrency(act.amount_recovered) : "—"}
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          {needsApproval ? (
                            <div className="flex items-center justify-end gap-1.5">
                              <Button
                                size="sm"
                                variant="success"
                                className="h-7 px-2 text-[11px] hover:scale-105 active:scale-95 transition-transform"
                                onClick={() => handleApprove(act.transaction_id)}
                              >
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 px-2 text-[11px] text-red-600 border-red-200 hover:bg-red-50"
                                onClick={() => handleReject(act.transaction_id)}
                              >
                                Reject
                              </Button>
                            </div>
                          ) : (
                            <Link href={`/transactions/${act.transaction_id}`}>
                              <Button variant="outline" size="sm" className="h-7 px-2.5 text-xs hover:border-blue-400 hover:text-[#0052cc] transition-all">
                                Details
                              </Button>
                            </Link>
                          )}
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
