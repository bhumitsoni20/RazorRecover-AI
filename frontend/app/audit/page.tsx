"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldCheck,
  Search,
  Filter,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { AuditLogItem } from "@/types/api";
import { PageTransition, itemFadeUp, staggerContainer } from "@/components/animations/page-transition";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [agentFilter, setAgentFilter] = useState("all");
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const loadLogs = async () => {
    setLoading(true);
    const res = await apiClient.getAuditLogs(agentFilter);
    setLogs(res);
    setLoading(false);
  };

  useEffect(() => {
    loadLogs();
  }, [agentFilter]);

  const toggleExpand = (id: string) => {
    setExpandedLogId((prev) => (prev === id ? null : id));
  };

  return (
    <PageTransition className="space-y-6">
      {/* Header */}
      <motion.div
        variants={itemFadeUp}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            <ShieldCheck className="h-6 w-6 text-[#0052cc]" />
            <span>Audit & Compliance Trail</span>
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Cryptographically verifiable, immutable record of all agent decisions and policy evaluations
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-700 focus:outline-none cursor-pointer"
          >
            <option value="all">All Agents & Handlers</option>
            <option value="PolicyGuardrailEngine">PolicyGuardrailEngine</option>
            <option value="ActionExecutionAgent">ActionExecutionAgent</option>
            <option value="RazorpayWebhookHandler">RazorpayWebhookHandler</option>
            <option value="RevenueDetectionAgent">RevenueDetectionAgent</option>
          </select>
          <Button variant="outline" size="sm" onClick={loadLogs} className="gap-1.5 hover:shadow-xs transition-all">
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </Button>
        </div>
      </motion.div>

      {/* Audit Log Entries */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="space-y-3"
      >
        {logs.map((log) => {
          const isExpanded = expandedLogId === log.id;
          const isApproved = log.policy_result === "APPROVED" || log.policy_result === "PASSED";
          const isBlocked = log.policy_result === "BLOCKED";

          return (
            <motion.div key={log.id} variants={itemFadeUp}>
              <Card className="transition-all hover:border-slate-300 hover:shadow-xs">
                <div
                  onClick={() => toggleExpand(log.id)}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-4 gap-2.5 cursor-pointer select-none"
                >
                  <div className="flex items-start sm:items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-700 shrink-0 mt-0.5 sm:mt-0">
                      <FileCode className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                        <span className="font-mono text-xs font-bold text-slate-900">{log.action}</span>
                        <Badge variant="neutral" size="sm">
                          {log.agent_name}
                        </Badge>
                        {log.transaction_id && (
                          <span className="font-mono text-[11px] text-blue-600 bg-blue-50 px-1.5 py-0.2 rounded border border-blue-200">
                            {log.transaction_id}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 mt-1 leading-snug">{log.reasoning_summary}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
                    {log.policy_result && (
                      <Badge variant={isApproved ? "success" : isBlocked ? "danger" : "warning"} size="sm">
                        {log.policy_result}
                      </Badge>
                    )}
                    <span className="text-[11px] text-slate-400 font-mono">{log.created_at}</span>
                    <motion.div
                      animate={{ rotate: isExpanded ? 90 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronRight className="h-4 w-4 text-slate-400" />
                    </motion.div>
                  </div>
                </div>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25 }}
                      className="border-t border-slate-100 bg-slate-50/75 p-4 space-y-3 text-xs overflow-hidden"
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {log.input_data && (
                          <div>
                            <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">
                              Input Parameters
                            </span>
                            <pre className="mt-1 rounded-lg border border-slate-200 bg-white p-3 font-mono text-[11px] text-slate-800 overflow-x-auto">
                              {JSON.stringify(log.input_data, null, 2)}
                            </pre>
                          </div>
                        )}
                        {log.output_data && (
                          <div>
                            <span className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">
                              Output / Verdict
                            </span>
                            <pre className="mt-1 rounded-lg border border-slate-200 bg-white p-3 font-mono text-[11px] text-slate-800 overflow-x-auto">
                              {JSON.stringify(log.output_data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>
    </PageTransition>
  );
}
