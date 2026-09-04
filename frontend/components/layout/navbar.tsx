"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Bell,
  Store,
  Sparkles,
  Menu,
  LogOut,
  ShieldCheck,
  CheckCircle2,
  ChevronDown,
  User,
  CreditCard,
  Building2,
  Clock,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

interface NavbarProps {
  onOpenSidebar?: () => void;
}

export function Navbar({ onOpenSidebar }: NavbarProps) {
  const [activeMode, setActiveMode] = useState<"real_test" | "simulation">("real_test");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { user, logout } = useAuth();

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const getInitials = (name?: string, email?: string) => {
    if (name) {
      const parts = name.trim().split(" ");
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return name.substring(0, 2).toUpperCase();
    }
    if (email) return email.substring(0, 2).toUpperCase();
    return "AD";
  };

  const displayName = user?.owner_name || "Admin Merchant";
  const displayEmail = user?.email || "admin@fintechmerchant.com";
  const displayBusiness = user?.business_name || "Fintech Merchant";
  const isVerified = user?.verification_status === "VERIFIED";

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 sm:px-6 backdrop-blur-md">
      {/* Left side: Mobile Menu Button + Merchant Context */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Mobile Drawer Trigger */}
        <button
          onClick={onOpenSidebar}
          className="lg:hidden flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-xs"
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Merchant Context */}
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50/70 px-2.5 py-1.5 text-xs text-slate-700 hover:bg-slate-100 transition-colors">
          <Store className="h-3.5 w-3.5 text-blue-600 shrink-0" />
          <span className="font-semibold text-slate-900 truncate max-w-[120px] sm:max-w-[180px] md:max-w-none">
            {displayBusiness}
          </span>
          <span className="hidden sm:inline text-slate-400 font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-slate-200">
            {user?.currency ? `${user.currency} (₹)` : "INR (₹)"}
          </span>
          {isVerified && (
            <span className="hidden md:inline-flex items-center gap-0.5 text-[9px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 rounded-full">
              <CheckCircle2 className="h-2.5 w-2.5" />
              VERIFIED
            </span>
          )}
        </div>

        {/* Mode Selector */}
        <div className="hidden md:flex items-center rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-[11px]">
          <button
            onClick={() => setActiveMode("real_test")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-semibold transition-all ${
              activeMode === "real_test"
                ? "bg-white text-blue-700 shadow-xs border border-blue-200/60"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                activeMode === "real_test" ? "bg-blue-600 animate-pulse" : "bg-slate-400"
              }`}
            ></span>
            <span>Razorpay Test Mode</span>
          </button>
          <button
            onClick={() => setActiveMode("simulation")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-semibold transition-all ${
              activeMode === "simulation"
                ? "bg-white text-purple-700 shadow-xs border border-purple-200/60"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                activeMode === "simulation" ? "bg-purple-600 animate-pulse" : "bg-slate-400"
              }`}
            ></span>
            <span>Simulation</span>
          </button>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Quick Demo Action Button */}
        <Link
          href="/transactions/txn_4999_upi"
          className="inline-flex items-center gap-1.5 sm:gap-2 rounded-lg bg-gradient-to-r from-[#0052cc] to-[#1e40af] px-2.5 sm:px-3.5 py-1.5 text-[11px] sm:text-xs font-semibold text-white shadow-sm hover:opacity-95 transition-all"
        >
          <Sparkles className="h-3.5 w-3.5 shrink-0" />
          <span className="hidden sm:inline">Demo ₹4,999 Case</span>
          <span className="sm:hidden">Demo Case</span>
        </Link>

        {/* Notifications */}
        <button className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-blue-600"></span>
        </button>

        <div className="h-6 w-px bg-slate-200"></div>

        {/* User Profile Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setIsDropdownOpen((prev) => !prev)}
            aria-expanded={isDropdownOpen}
            aria-haspopup="true"
            className={`flex items-center gap-2 rounded-xl p-1.5 sm:px-2.5 sm:py-1.5 text-left transition-all border ${
              isDropdownOpen
                ? "bg-slate-100/90 border-slate-300 ring-2 ring-blue-500/10"
                : "border-transparent hover:border-slate-200 hover:bg-slate-50/80"
            }`}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white shrink-0 shadow-xs">
              {getInitials(displayName, displayEmail)}
            </div>
            <div className="hidden xl:flex flex-col text-left">
              <span className="text-xs font-semibold text-slate-900 leading-tight">
                {displayName}
              </span>
              <span className="text-[10px] text-slate-400 truncate max-w-[140px]">
                {displayEmail}
              </span>
            </div>
            <ChevronDown
              className={`h-4 w-4 text-slate-400 transition-transform duration-200 ${
                isDropdownOpen ? "rotate-180 text-blue-600" : ""
              }`}
            />
          </button>

          {/* Interactive Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute right-0 top-full mt-2 w-72 rounded-2xl border border-slate-200/90 bg-white p-2 shadow-xl shadow-slate-900/10 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              {/* Profile Card Summary */}
              <div className="rounded-xl bg-slate-50/80 p-3 mb-1 border border-slate-100">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white shrink-0">
                    {getInitials(displayName, displayEmail)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-slate-900 truncate">
                      {displayName}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate">
                      {displayEmail}
                    </p>
                  </div>
                </div>

                <div className="mt-2.5 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500 font-medium">Merchant Status:</span>
                  <span
                    className={`inline-flex items-center gap-1 font-semibold text-[10px] px-2 py-0.5 rounded-full border ${
                      isVerified
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-amber-50 text-amber-700 border-amber-200"
                    }`}
                  >
                    {isVerified ? (
                      <>
                        <CheckCircle2 className="h-3 w-3" />
                        VERIFIED
                      </>
                    ) : (
                      <>
                        <Clock className="h-3 w-3" />
                        PENDING
                      </>
                    )}
                  </span>
                </div>
              </div>

              {/* Merchant Details */}
              <div className="px-2 py-1.5 space-y-1">
                <div className="flex items-center justify-between text-[11px] py-1 text-slate-600">
                  <span className="flex items-center gap-1.5 text-slate-500">
                    <Building2 className="h-3.5 w-3.5 text-slate-400" />
                    Store
                  </span>
                  <span className="font-semibold text-slate-800 truncate max-w-[130px]">
                    {displayBusiness}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[11px] py-1 text-slate-600">
                  <span className="flex items-center gap-1.5 text-slate-500">
                    <CreditCard className="h-3.5 w-3.5 text-slate-400" />
                    Gateway
                  </span>
                  <span className="font-mono text-[10px] text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                    {user?.razorpay_account_id || "acc_rzp_demo"}
                  </span>
                </div>
              </div>

              <div className="h-px bg-slate-100 my-1"></div>

              {/* Navigation Links */}
              <div className="space-y-0.5">
                <Link
                  href="/onboarding/razorpay"
                  onClick={() => setIsDropdownOpen(false)}
                  className="flex items-center justify-between rounded-lg px-2.5 py-2 text-xs text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors font-medium"
                >
                  <span className="flex items-center gap-2">
                    <CreditCard className="h-3.5 w-3.5 text-slate-400" />
                    Razorpay Gateway Settings
                  </span>
                  <ExternalLink className="h-3 w-3 text-slate-400" />
                </Link>

                <Link
                  href="/audit"
                  onClick={() => setIsDropdownOpen(false)}
                  className="flex items-center justify-between rounded-lg px-2.5 py-2 text-xs text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors font-medium"
                >
                  <span className="flex items-center gap-2">
                    <ShieldCheck className="h-3.5 w-3.5 text-slate-400" />
                    Cryptographic Audit Trail
                  </span>
                  <ExternalLink className="h-3 w-3 text-slate-400" />
                </Link>
              </div>

              <div className="h-px bg-slate-100 my-1"></div>

              {/* Sign Out Button */}
              <button
                type="button"
                onClick={async () => {
                  setIsDropdownOpen(false);
                  await logout();
                }}
                className="w-full flex items-center gap-2 rounded-xl px-2.5 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 hover:text-rose-700 transition-colors group"
              >
                <LogOut className="h-4 w-4 text-rose-500 group-hover:translate-x-0.5 transition-transform" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
