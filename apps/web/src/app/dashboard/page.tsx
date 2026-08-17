"use client";

import React from "react";
import Link from "next/link";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  Film,
  Sparkles,
  Inbox,
  Clock,
  TrendingUp,
  Bookmark,
  ArrowRight,
  Share2,
} from "lucide-react";

export default function DashboardPage() {
  return (
    <PageContainer
      title="Dashboard & Intelligence"
      subtitle="Overview of user watch activity, catalog stats, and personal AI recommendations"
      action={
        <Link
          href="/social"
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/30 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Open AI Matches</span>
        </Link>
      }
    >
      <div className="space-y-8">
        {/* Metric Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center justify-between">
            <div>
              <span className="text-xs font-medium text-zinc-400">Total Catalog Titles</span>
              <h3 className="text-2xl font-bold text-zinc-100 mt-1">1,420</h3>
              <span className="text-[11px] text-emerald-400 flex items-center gap-1 mt-1">
                <TrendingUp className="w-3 h-3" /> +12 added this week
              </span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
              <Film className="w-5 h-5" />
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center justify-between">
            <div>
              <span className="text-xs font-medium text-zinc-400">AI Taste Match Score</span>
              <h3 className="text-2xl font-bold text-emerald-400 mt-1">98.4%</h3>
              <span className="text-[11px] text-zinc-400 mt-1">Neural vector precision</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Sparkles className="w-5 h-5" />
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center justify-between">
            <div>
              <span className="text-xs font-medium text-zinc-400">Social Inbox Queue</span>
              <h3 className="text-2xl font-bold text-zinc-100 mt-1">5 Pending</h3>
              <span className="text-[11px] text-violet-400 mt-1">From friends & AI</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
              <Inbox className="w-5 h-5" />
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center justify-between">
            <div>
              <span className="text-xs font-medium text-zinc-400">Watch Time Logged</span>
              <h3 className="text-2xl font-bold text-zinc-100 mt-1">348 hrs</h3>
              <span className="text-[11px] text-zinc-400 mt-1">Across 142 titles</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300">
              <Clock className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Intelligence Split: Recent AI Recommendations & Quick Access */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Columns: Top Neural Recommendations */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-zinc-900/30 border border-zinc-900 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-zinc-100">Top AI Taste Recommendations</h3>
              </div>
              <Link
                href="/social"
                className="text-xs text-violet-400 hover:text-violet-300 font-medium inline-flex items-center gap-1"
              >
                <span>View All In Social</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="space-y-3">
              {[
                {
                  title: "Dune: Part Two",
                  genre: "Sci-Fi • Denis Villeneuve",
                  match: 99,
                  note: "Desert cinematography and complex narrative alignment.",
                },
                {
                  title: "Blade Runner 2049",
                  genre: "Cyberpunk • Roger Deakins",
                  match: 98,
                  note: "Atmospheric neon color palettes and pacing.",
                },
                {
                  title: "Arrival",
                  genre: "Sci-Fi • Ted Chiang adaptation",
                  match: 97,
                  note: "Non-linear linguistic exploration.",
                },
              ].map((item) => (
                <div
                  key={item.title}
                  className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-900 flex items-center justify-between gap-4 hover:border-zinc-800 transition-colors"
                >
                  <div className="space-y-1">
                    <h4 className="text-xs font-bold text-zinc-100">{item.title}</h4>
                    <p className="text-[11px] text-zinc-400">{item.genre}</p>
                    <p className="text-[11px] text-zinc-500 italic">&ldquo;{item.note}&rdquo;</p>
                  </div>

                  <div className="shrink-0 flex items-center gap-3">
                    <span className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full text-xs font-semibold">
                      <Sparkles className="w-3 h-3" />
                      {item.match}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Quick Quicklinks */}
          <div className="space-y-4">
            <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-900 space-y-4">
              <h3 className="text-sm font-bold text-zinc-100">Quick Actions</h3>

              <div className="space-y-2">
                <Link
                  href="/movies"
                  className="flex items-center justify-between p-3 rounded-xl bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300 hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <Film className="w-4 h-4 text-violet-400" />
                    <span>Browse Movie Catalog</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-500" />
                </Link>

                <Link
                  href="/social"
                  className="flex items-center justify-between p-3 rounded-xl bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300 hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <Share2 className="w-4 h-4 text-emerald-400" />
                    <span>Social Recommendations</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-500" />
                </Link>

                <Link
                  href="/watchlist"
                  className="flex items-center justify-between p-3 rounded-xl bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300 hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <Bookmark className="w-4 h-4 text-amber-400" />
                    <span>Manage Watchlist</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-500" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
