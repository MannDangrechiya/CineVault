import React from "react";
import Link from "next/link";
import { PageContainer } from "@/components/ui/PageContainer";
import { LayoutDashboard, ShieldCheck, ArrowRight, Layers, Sparkles } from "lucide-react";

export default function HomePage() {
  return (
    <PageContainer
      title="CineVault OS Web Foundation"
      subtitle="Day 1 Web Client Architecture (Next.js App Router + React + TypeScript)"
    >
      <div className="space-y-6">
        {/* Welcome Hero Banner */}
        <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-violet-950/40 border border-slate-800 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-950/60 border border-violet-700/40 text-xs font-semibold text-violet-300 mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Foundation Established</span>
            </div>
            <h2 className="text-xl sm:text-3xl font-extrabold text-slate-100 tracking-tight">
              Welcome to CineVault OS Web Client
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-2 leading-relaxed">
              The Next.js App Router application shell is fully configured with responsive desktop & mobile navigation, dark-mode styling, and page container states.
            </p>
            <div className="flex flex-wrap items-center gap-3 mt-6">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-xl shadow-lg shadow-violet-900/30 transition-all"
              >
                <LayoutDashboard className="w-4 h-4" />
                Go to Dashboard
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/library"
                className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-slate-300 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 rounded-xl transition-all"
              >
                <Layers className="w-4 h-4" />
                Browse Library Placeholder
              </Link>
            </div>
          </div>
        </div>

        {/* Core Architecture Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/80 space-y-2">
            <div className="w-8 h-8 rounded-lg bg-violet-950/60 border border-violet-800/50 flex items-center justify-center text-violet-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200">Zero Paid SaaS Dependencies</h3>
            <p className="text-xs text-slate-400">
              CineVault OS remains 100% free, open-source, and self-hostable.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/80 space-y-2">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/50 flex items-center justify-center text-cyan-400">
              <Layers className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200">Protected Backend</h3>
            <p className="text-xs text-slate-400">
              FastAPI backend, PostgreSQL schema, and domain rules are preserved without alteration.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/80 space-y-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/60 border border-emerald-800/50 flex items-center justify-center text-emerald-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200">Responsive App Shell</h3>
            <p className="text-xs text-slate-400">
              Sidebar for desktop screens, bottom tab bar and slide-over menu for mobile views.
            </p>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
