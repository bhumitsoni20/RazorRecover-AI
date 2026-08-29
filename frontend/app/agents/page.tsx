"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Cpu,
  Activity,
  CheckCircle2,
  Clock,
  Zap,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Terminal,
  RefreshCw,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { AgentsOverviewResponse } from "@/types/api";
import { formatPercentage } from "@/lib/formatters";
import { PageTransition, itemFadeUp, staggerContainer } from "@/components/animations/page-transition";

export default function AgentsPage() {
  const [data, setData] = useState<AgentsOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    const res = await apiClient.getAgentsOverview();
    setData(res);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <PageTransition className="space-y-6">
      {/* Header */}
      <motion.div
        variants={itemFadeUp}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            <Cpu className="h-6 w-6 text-[#0052cc]" />
            <span>AI Agents Observability & Telemetry</span>
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Real-time execution health, latency monitoring, and multi-agent workflow traces
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadData} className="gap-1.5 hover:shadow-xs transition-all">
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh Metrics</span>
        </Button>
      </motion.div>

      {/* Agents Status Cards */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        {data?.agents.map((agent) => (
          <motion.div
            key={agent.name}
            variants={itemFadeUp}
            whileHover={{ y: -3 }}
            transition={{ duration: 0.2 }}
          >
            <Card className="hover:shadow-md transition-shadow border-slate-200/90 h-full flex flex-col justify-between">
              <CardContent className="p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-[#0052cc]">
                      <Zap className="h-4 w-4" />
                    </div>
                    <div>
                      <h3 className="font-bold text-sm text-slate-900">{agent.name}</h3>
                    </div>
                  </div>
                  <Badge variant={agent.status === "active" ? "success" : "warning"} size="sm" className="gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                    <span>{agent.status}</span>
                  </Badge>
                </div>

                <p className="text-xs text-slate-500 leading-relaxed min-h-[36px]">
                  {agent.role}
                </p>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100 text-center">
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Total Runs</div>
                    <div className="text-sm font-bold text-slate-900 mt-0.5">{agent.total_runs.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Success</div>
                    <div className="text-sm font-bold text-emerald-600 mt-0.5">
                      {formatPercentage(agent.success_rate * 100)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Avg Latency</div>
                    <div className="text-sm font-bold text-blue-600 mt-0.5">{agent.avg_latency_ms}ms</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Recent Execution Run Logs */}
      <motion.div variants={itemFadeUp}>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Terminal className="h-4 w-4 text-slate-700" />
              <span>Recent Agent Execution Traces</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/75 border-y border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Run ID</th>
                    <th className="px-4 py-3">Agent</th>
                    <th className="px-4 py-3">Transaction</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Latency</th>
                    <th className="px-4 py-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data?.recent_runs.map((run, idx) => (
                    <motion.tr
                      key={run.id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2, delay: idx * 0.04 }}
                      className="hover:bg-slate-50/60 transition-colors"
                    >
                      <td className="px-4 py-3 font-mono font-medium text-slate-900">{run.id}</td>
                      <td className="px-4 py-3 font-semibold text-slate-800">{run.agent_name}</td>
                      <td className="px-4 py-3 font-mono text-blue-600">
                        {run.transaction_id || "—"}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={run.status === "success" ? "success" : "danger"} size="sm">
                          {run.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-600">{run.latency_ms}ms</td>
                      <td className="px-4 py-3 text-slate-400 font-mono">{run.started_at}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </PageTransition>
  );
}
