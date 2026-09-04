import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/app-shell";
import { AuthProvider } from "@/lib/auth-context";

export const metadata: Metadata = {
  title: "RazorRecover AI | Autonomous Merchant Revenue Recovery",
  description:
    "Autonomous AI revenue recovery platform for merchants powered by multi-agent reasoning, RAG policies, ML risk prediction, and Razorpay Test Mode integration.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#f8fafc] text-slate-900 antialiased font-sans">
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}

