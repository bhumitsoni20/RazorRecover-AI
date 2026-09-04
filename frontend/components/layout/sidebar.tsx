"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ArrowLeftRight,
  Sparkles,
  ShieldCheck,
  Cpu,
  BarChart3,
  Zap,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/recovery", label: "AI Recovery", icon: Sparkles, badge: "Live" },
  { href: "/audit", label: "Audit & Policy", icon: ShieldCheck },
  { href: "/agents", label: "Agents Telemetry", icon: Cpu },
  { href: "/evaluation", label: "Evaluation & ROI", icon: BarChart3 },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const rawPathname = usePathname();
  const pathname = rawPathname || "";

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-50 flex h-screen w-72 lg:w-64 flex-col border-r border-slate-200/90 bg-white text-slate-800 shadow-xl lg:shadow-sm transition-transform duration-300 ease-in-out",
        isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between border-b border-slate-100 px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-[#0052cc] to-[#1e40af] text-white shadow-md shadow-blue-500/20">
            <Zap className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-[15px] tracking-tight text-slate-900 flex items-center gap-1.5">
              RazorRecover <span className="rounded bg-blue-100 px-1 py-0.2 text-[10px] font-bold text-blue-700">AI</span>
            </span>
            <span className="text-[11px] text-slate-400 font-medium">Autonomous Revenue Recovery</span>
          </div>
        </div>

        {/* Mobile Close Button */}
        <button
          onClick={onClose}
          className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          aria-label="Close sidebar"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Platform
        </div>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(`${item.href}/`)) || (item.href === "/dashboard" && pathname === "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => onClose?.()}
              className={cn(
                "group flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-blue-50/80 text-[#0052cc] shadow-sm font-semibold"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={cn(
                    "h-4 w-4 transition-colors",
                    isActive ? "text-[#0052cc]" : "text-slate-400 group-hover:text-slate-600"
                  )}
                />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 border border-emerald-200">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Engine Status Widget */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="rounded-lg border border-slate-200/80 bg-white p-3 shadow-sm">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-xs font-semibold text-slate-800">Engine Active</span>
            </div>
            <span className="text-[11px] font-medium text-slate-500">99.8% SLA</span>
          </div>
          <p className="text-[11px] text-slate-500 leading-snug">
            Autonomous multi-agent recovery watching failed checkouts.
          </p>
          <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-100 pt-2 font-mono">
            <span>Razorpay Mode:</span>
            <span className="font-semibold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">TEST</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
