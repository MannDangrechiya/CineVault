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
  Search,
  Share2,
} from "lucide-react";

export default function HomePage() {
  return (
    <PageContainer
      title="CineVault OS v2.0"
      subtitle="Universal, self-hostable cinematic intelligence & personal media catalog platform."
    >
      <div className="space-y-8">
        {/* Cinematic OLED Hero Banner */}
        <div className="p-6 sm:p-10 rounded-3xl bg-gradient-to-br from-zinc-900 via-zinc-950 to-zinc-950 border border-zinc-800/80 relative overflow-hidden shadow-2xl shadow-violet-950/20">
          {/* Subtle Ambient Violet & Emerald Glows */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 right-1/3 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-xs font-semibold text-violet-300 mb-4 backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5 text-violet-400" />
              <span>Cinematic OLED Edition • v2.0</span>
            </div>

            <h2 className="text-2xl sm:text-4xl lg:text-5xl font-black text-zinc-50 tracking-tight leading-tight">
              Explore, Curate & Own Your Complete Cinematic World
            </h2>

            <p className="text-xs sm:text-sm text-zinc-400 mt-4 leading-relaxed max-w-2xl">
              Canonical metadata provenance, offline-first personal library synchronization, AI-grounded neural recommendation intelligence, and sovereign data portability.
            </p>

            <div className="flex flex-wrap items-center gap-3 mt-7">
              <Link
                href="/movies"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/30 transition-all hover:scale-105"
              >
                <Film className="w-4 h-4" />
                Browse Movies
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>

              <Link
                href="/social"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-full transition-all"
              >
                <Share2 className="w-4 h-4 text-emerald-400" />
                Social Inbox & AI Matches
              </Link>

              <Link
                href="/series"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-zinc-850 border border-zinc-800 rounded-full transition-all"
              >
                <Tv className="w-4 h-4 text-zinc-400" />
                TV Series
              </Link>

              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-zinc-400 hover:text-zinc-200 bg-zinc-950/60 hover:bg-zinc-900 border border-zinc-900 rounded-full transition-all"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Access Navigation Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/social"
            className="p-5 rounded-2xl bg-zinc-900/30 hover:bg-zinc-900/60 border border-zinc-900 hover:border-violet-500/40 transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400 group-hover:scale-105 transition-transform mb-3">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-zinc-200 group-hover:text-violet-300 transition-colors">
                AI Taste Match
              </h3>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                Vector
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
              Curated peer recommendations & neural taste alignment.
            </p>
          </Link>

          <Link
            href="/watchlist"
            className="p-5 rounded-2xl bg-zinc-900/30 hover:bg-zinc-900/60 border border-zinc-900 hover:border-zinc-700 transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300 group-hover:scale-105 transition-transform mb-3">
              <Bookmark className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-zinc-200 group-hover:text-zinc-100 transition-colors">
              Watchlist
            </h3>
            <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
              Curated queue of movies and series to watch next.
            </p>
          </Link>

          <Link
            href="/history"
            className="p-5 rounded-2xl bg-zinc-900/30 hover:bg-zinc-900/60 border border-zinc-900 hover:border-zinc-700 transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300 group-hover:scale-105 transition-transform mb-3">
              <History className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-zinc-200 group-hover:text-zinc-100 transition-colors">
              Watch History
            </h3>
            <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
              Append-only timeline of viewing events and progress.
            </p>
          </Link>

          <Link
            href="/collections"
            className="p-5 rounded-2xl bg-zinc-900/30 hover:bg-zinc-900/60 border border-zinc-900 hover:border-zinc-700 transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300 group-hover:scale-105 transition-transform mb-3">
              <FolderHeart className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-zinc-200 group-hover:text-zinc-100 transition-colors">
              Collections
            </h3>
            <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
              Franchise watch orders, thematic marathons, and sets.
            </p>
          </Link>
        </div>

        {/* Feature Highlights Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-900 space-y-3">
            <div className="flex items-center gap-2 text-violet-400 font-semibold text-sm">
              <Bot className="w-4 h-4" />
              <span>AI Conversational Assistant</span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Ask natural queries like <em>&quot;Compare Dune 1984 vs Dune 2021&quot;</em> or build custom marathon viewing schedules tailored to your mood and streaming subscriptions.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-900 space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
              <Search className="w-4 h-4" />
              <span>Faceted Search & Discovery</span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Filter canonical titles instantly across production year, original country, content type, genres, and active streaming provider availability in your region.
            </p>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
