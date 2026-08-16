import React from "react";
import Link from "next/link";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  Film,
  Tv,
  Bookmark,
  History,
  FolderHeart,
  LayoutDashboard,
  Bot,
  ArrowRight,
  Sparkles,
  DownloadCloud,
  Search,
} from "lucide-react";

export default function HomePage() {
  return (
    <PageContainer
      title="CineVault OS"
      subtitle="Universal, self-hostable cinematic intelligence & personal media catalog platform."
    >
      <div className="space-y-8">
        {/* Welcome Hero Banner */}
        <div className="p-6 sm:p-10 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-amber-950/30 border border-slate-800 relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950/60 border border-amber-600/40 text-xs font-semibold text-amber-300 mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Cinematic Operating System</span>
            </div>
            <h2 className="text-2xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
              Explore, Curate & Own Your Complete Cinematic World
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-3 leading-relaxed">
              Canonical metadata provenance, offline-first personal library synchronization, AI-grounded recommendation intelligence, and sovereign data portability.
            </p>
            <div className="flex flex-wrap items-center gap-3 mt-6">
              <Link
                href="/movies"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-slate-950 bg-amber-400 hover:bg-amber-300 rounded-xl shadow-lg shadow-amber-950/40 transition-all"
              >
                <Film className="w-4 h-4" />
                Browse Movies
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/series"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-slate-200 bg-slate-800/90 hover:bg-slate-800 border border-slate-700 rounded-xl transition-all"
              >
                <Tv className="w-4 h-4" />
                Browse TV Series
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-900/60 hover:bg-slate-800 border border-slate-800 rounded-xl transition-all"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard Analytics
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Access Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/watchlist"
            className="p-5 rounded-xl bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all group"
          >
            <div className="w-10 h-10 rounded-lg bg-amber-950/50 border border-amber-700/40 flex items-center justify-center text-amber-400 group-hover:scale-105 transition-transform mb-3">
              <Bookmark className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 group-hover:text-amber-300 transition-colors">
              Watchlist
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Curated queue of movies and series to watch next.
            </p>
          </Link>

          <Link
            href="/history"
            className="p-5 rounded-xl bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all group"
          >
            <div className="w-10 h-10 rounded-lg bg-blue-950/50 border border-blue-700/40 flex items-center justify-center text-blue-400 group-hover:scale-105 transition-transform mb-3">
              <History className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 group-hover:text-blue-300 transition-colors">
              Watch History
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Append-only timeline of viewing events and progress.
            </p>
          </Link>

          <Link
            href="/collections"
            className="p-5 rounded-xl bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all group"
          >
            <div className="w-10 h-10 rounded-lg bg-purple-950/50 border border-purple-700/40 flex items-center justify-center text-purple-400 group-hover:scale-105 transition-transform mb-3">
              <FolderHeart className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 group-hover:text-purple-300 transition-colors">
              Custom Lists
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Franchise watch orders, thematic marathons, and collections.
            </p>
          </Link>

          <Link
            href="/import"
            className="p-5 rounded-xl bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all group"
          >
            <div className="w-10 h-10 rounded-lg bg-emerald-950/50 border border-emerald-700/40 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition-transform mb-3">
              <DownloadCloud className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200 group-hover:text-emerald-300 transition-colors">
              Data Portability
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Full library JSON/CSV export and conflict-safe import.
            </p>
          </Link>
        </div>

        {/* Feature Highlights Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/30 border border-slate-800/80 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <Bot className="w-4 h-4" />
              <span>AI Conversational Assistant</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ask natural queries like <em>&quot;Compare Dune 1984 vs Dune 2021&quot;</em> or build custom marathon viewing schedules tailored to your mood and streaming subscriptions.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/30 border border-slate-800/80 space-y-3">
            <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
              <Search className="w-4 h-4" />
              <span>Faceted Search & Discovery</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Filter canonical titles instantly across production year, original country, content type, genres, and active streaming provider availability in your region.
            </p>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
