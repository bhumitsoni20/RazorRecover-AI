"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Sidebar } from "./sidebar";
import { Navbar } from "./navbar";
import { Loader2 } from "lucide-react";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const rawPathname = usePathname();
  const pathname = rawPathname || "";
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Route classifications
  const isAuthPage = pathname === "/login" || pathname === "/signup";
  const isPublicPaymentPage = pathname.startsWith("/pay");
  const isOnboardingPage =
    pathname === "/onboarding/razorpay" || pathname === "/verification-pending";
  const isExempt = isAuthPage || isPublicPaymentPage || isOnboardingPage;

  // Close mobile sidebar automatically on navigation
  useEffect(() => {
    setIsMobileSidebarOpen(false);
  }, [pathname]);

  // Handle escape key to close mobile drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsMobileSidebarOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Route Gating & Protection
  useEffect(() => {
    if (!mounted || loading) return;

    // 1. If on login/signup but user is already logged in
    if (isAuthPage && user) {
      if (user.verification_status === "VERIFIED") {
        router.replace("/dashboard");
      } else {
        router.replace("/verification-pending");
      }
      return;
    }

    // 2. If on protected route (dashboard, transactions, etc.)
    if (!isExempt) {
      if (!user) {
        router.replace("/login");
        return;
      }
      if (user.verification_status !== "VERIFIED") {
        router.replace("/verification-pending");
        return;
      }
    }

    // 3. If on onboarding/pending page but not logged in
    if (isOnboardingPage && !user) {
      router.replace("/login");
      return;
    }
  }, [mounted, user, loading, pathname, isAuthPage, isExempt, isOnboardingPage, router]);

  // Public checkout pages (customers paying recovery links) - always render immediately
  if (isPublicPaymentPage) {
    return (
      <div className="min-h-screen bg-[#f8fafc] flex flex-col justify-center">
        {children}
      </div>
    );
  }

  // Auth pages & onboarding pages
  if (isAuthPage || isOnboardingPage) {
    return (
      <div className="min-h-screen bg-[#f8fafc] flex flex-col justify-center">
        {children}
      </div>
    );
  }

  // Before mounting or while initial auth session is loading on protected routes
  if (!mounted || loading) {
    return (
      <div className="min-h-screen bg-[#f8fafc] flex flex-col items-center justify-center space-y-3">
        <Loader2 className="h-8 w-8 animate-spin text-[#0052cc]" />
        <p className="text-xs font-semibold text-slate-500">
          Loading merchant workspace...
        </p>
      </div>
    );
  }

  // If unauthenticated or unverified on protected route, show redirect indicator
  if (!user || user.verification_status !== "VERIFIED") {
    return (
      <div className="min-h-screen bg-[#f8fafc] flex flex-col items-center justify-center space-y-3">
        <Loader2 className="h-8 w-8 animate-spin text-[#0052cc]" />
        <p className="text-xs font-semibold text-slate-500">
          Redirecting to authorized route...
        </p>
      </div>
    );
  }

  // Verified Merchant Main Application Layout
  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col">
      {/* Mobile Backdrop Overlay */}
      {isMobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 lg:hidden transition-opacity duration-300"
          onClick={() => setIsMobileSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar (Fixed on Desktop, Slide-over Drawer on Mobile) */}
      <Sidebar
        isOpen={isMobileSidebarOpen}
        onClose={() => setIsMobileSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="lg:pl-64 flex flex-col min-h-screen w-full min-w-0 transition-all duration-300">
        <Navbar onOpenSidebar={() => setIsMobileSidebarOpen(true)} />
        <main className="flex-1 p-3.5 sm:p-6 md:p-8 max-w-7xl w-full mx-auto min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
}
