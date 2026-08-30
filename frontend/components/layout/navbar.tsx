"use client";

import React, { useState } from "react";
import { Bell, Search, ShieldCheck, ChevronDown, Store, Sparkles, Activity, Check } from "lucide-react";
import Link from "next/link";

export function Navbar() {
  const [activeMode, setActiveMode] = useState<"real_test" | "simulation">("real_test");

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/80 bg-white/90 px-6 backdrop-blur-md">
      {/* Merchant Context */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50/70 px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer">
          <Store className="h-3.5 w-3.5 text-blue-600" />
          <span className="font-semibold text-slate-900">Fintech Merchant Global</span>
          <span className="text-slate-400 font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-slate-200">INR (₹)</span>
        </div>

        {/* Explicit Mode Selector: Real Test Mode vs Simulation Mode */}
        <div className="flex items-center rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-[11px]">
          <button
            onClick={() => setActiveMode("real_test")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-semibold transition-all ${
              activeMode === "real_test"
                ? "bg-white text-blue-700 shadow-xs border border-blue-200/60"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${activeMode === "real_test" ? "bg-blue-600 animate-pulse" : "bg-slate-400"}`}></span>
            <span>Razorpay Real Test Mode</span>
          </button>
          <button
            onClick={() => setActiveMode("simulation")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-semibold transition-all ${
              activeMode === "simulation"
                ? "bg-white text-purple-700 shadow-xs border border-purple-200/60"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${activeMode === "simulation" ? "bg-purple-600 animate-pulse" : "bg-slate-400"}`}></span>
            <span>Simulation Mode</span>
          </button>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Quick Demo Action Button */}
        <Link
          href="/transactions/txn_4999_upi"
          className="hidden sm:inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-[#0052cc] to-[#1e40af] px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:opacity-95 transition-all"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>Demo ₹4,999 Case</span>
        </Link>

        {/* Notifications */}
        <button className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-blue-600"></span>
        </button>

        <div className="h-6 w-px bg-slate-200"></div>

        {/* User profile */}
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
            AD
          </div>
          <div className="hidden lg:flex flex-col text-left">
            <span className="text-xs font-semibold text-slate-900 leading-tight">Admin Merchant</span>
            <span className="text-[10px] text-slate-400">admin@fintechmerchant.com</span>
          </div>
        </div>
      </div>
    </header>
  );
}
