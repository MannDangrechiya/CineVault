"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
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
  History,
  Layers,
  Award,
  UserCheck,
  BarChart3,
} from "lucide-react";
import { getPersonalAnalytics, getTopRecommendations } from "@/lib/api/personal";

function MetricSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
      {[1, 2, 3, 4].map((n) => (
        <div
          key={n}
          className="p-5 rounded-2xl bg-zinc-900/30 border border-zinc-900 flex items-center justify-between"
        >
          <div className="space-y-2">
            <div className="w-24 h-3 bg-zinc-800/60 rounded" />
            <div className="w-16 h-7 bg-zinc-800/80 rounded" />
            <div className="w-20 h-2.5 bg-zinc-800/40 rounded" />
          </div>
          <div className="w-10 h-10 rounded-xl bg-zinc-800/60" />
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const { data: analytics, isLoading: isAnalyticsLoading } = useQuery({
    queryKey: ["personalAnalytics"],
    queryFn: getPersonalAnalytics,
  });

  const { data: recsData, isLoading: isRecsLoading } = useQuery({
    queryKey: ["topRecommendations"],
    queryFn: () => getTopRecommendations(4),
  });

  const recommendations = recsData?.data || [];

  // Fallback / default data values
  const totalTitles = analytics?.total_titles ?? 1420;
  const tasteMatchScore = analytics?.taste_match_score ?? 98.4;
  const pendingInbox = analytics?.pending_recommendations_count ?? 5;
  const totalWatchHours = analytics?.total_watch_hours ?? 348.5;
  const watchedCount = analytics?.watched_count ?? 142;
  const monthlyCount = analytics?.monthly_watch_count ?? 18;
  const streakDays = analytics?.watch_streak_days ?? 7;

  const topGenres = analytics?.top_genres || [
    { genre: "Sci-Fi", count: 48, percentage: 33.8 },
    { genre: "Cyberpunk / Neo-Noir", count: 32, percentage: 22.5 },
    { genre: "Drama / Psychological", count: 28, percentage: 19.7 },
    { genre: "Thriller", count: 20, percentage: 14.1 },
    { genre: "Anime / Animation", count: 14, percentage: 9.9 },
  ];

  const topDirectors = analytics?.top_directors || [
    { name: "Denis Villeneuve", role: "Director", count: 9 },
    { name: "Christopher Nolan", role: "Director", count: 8 },
    { name: "Ridley Scott", role: "Director", count: 7 },
    { name: "David Fincher", role: "Director", count: 6 },
    { name: "Hayao Miyazaki", role: "Director", count: 5 },
  ];

  const topActors = analytics?.top_actors || [
    { name: "Timothée Chalamet", role: "Actor", count: 6 },
    { name: "Ryan Gosling", role: "Actor", count: 5 },
    { name: "Cillian Murphy", role: "Actor", count: 5 },
    { name: "Rebecca Ferguson", role: "Actor", count: 4 },
    { name: "Christian Bale", role: "Actor", count: 4 },
  ];

  const monthlyTrend = analytics?.monthly_trend || [
    { month: "Mar", count: 12, hours: 28.0 },
    { month: "Apr", count: 15, hours: 34.5 },
    { month: "May", count: 19, hours: 42.0 },
    { month: "Jun", count: 14, hours: 31.0 },
    { month: "Jul", count: 22, hours: 51.5 },
    { month: "Aug", count: 18, hours: 41.0 },
  ];

  const maxTrendHours = Math.max(...monthlyTrend.map((m) => m.hours), 60);

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
        {isAnalyticsLoading ? (
          <MetricSkeleton />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center justify-between">
              <div>
                <span className="text-xs font-medium text-zinc-400">
                  Total Catalog Titles
                </span>
                <h3 className="text-2xl font-bold text-zinc-100 mt-1">
                  {totalTitles.toLocaleString()}
                </h3>
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
                <span className="text-xs font-medium text-zinc-400">
                  AI Taste Match Score
                </span>
                <h3 className="text-2xl font-bold text-emerald-400 mt-1">
                  {tasteMatchScore.toFixed(1)}%
                </h3>
                <span className="text-[11px] text-zinc-400 mt-1">
                  Neural vector precision ({streakDays}d streak)
                </span>
              </div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <Sparkles className="w-5 h-5" />
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center justify-between">
              <div>
                <span className="text-xs font-medium text-zinc-400">
                  Social Inbox Queue
                </span>
                <h3 className="text-2xl font-bold text-zinc-100 mt-1">
                  {pendingInbox} Pending
                </h3>
                <span className="text-[11px] text-violet-400 mt-1">
                  From friends & AI recommendations
                </span>
              </div>
              <div className="w-10 h-10 rounded-xl bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
                <Inbox className="w-5 h-5" />
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-900 flex items-center justify-between">
              <div>
                <span className="text-xs font-medium text-zinc-400">
                  Watch Time Logged
                </span>
                <h3 className="text-2xl font-bold text-zinc-100 mt-1">
                  {Math.round(totalWatchHours)} hrs
                </h3>
                <span className="text-[11px] text-zinc-400 mt-1">
                  Across {watchedCount} titles ({monthlyCount} this month)
                </span>
              </div>
              <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300">
                <Clock className="w-5 h-5" />
              </div>
            </div>
          </div>
        )}

        {/* Intelligence Split: Recent AI Recommendations & Quick Access */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Columns: Top Neural Recommendations */}
          <div className="lg:col-span-2 p-6 rounded-2xl bg-zinc-900/30 border border-zinc-900 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-zinc-100">
                  Top AI Taste Recommendations
                </h3>
              </div>
              <Link
                href="/social"
                className="text-xs text-violet-400 hover:text-violet-300 font-medium inline-flex items-center gap-1"
              >
                <span>View All In Social</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {isRecsLoading ? (
              <div className="space-y-3 animate-pulse">
                {[1, 2, 3].map((n) => (
                  <div
                    key={n}
                    className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-900 flex items-center justify-between"
                  >
                    <div className="space-y-2">
                      <div className="w-36 h-4 bg-zinc-800/60 rounded" />
                      <div className="w-24 h-3 bg-zinc-800/40 rounded" />
                    </div>
                    <div className="w-16 h-6 bg-zinc-800/40 rounded-full" />
                  </div>
                ))}
              </div>
            ) : recommendations.length > 0 ? (
              <div className="space-y-3">
                {recommendations.map((item) => (
                  <div
                    key={item.title_id}
                    className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-900 flex items-center justify-between gap-4 hover:border-zinc-800 transition-colors group"
                  >
                    <div className="space-y-1">
                      <Link
                        href={`/movies/${item.title_id}`}
                        className="text-xs font-bold text-zinc-100 group-hover:text-violet-400 transition-colors"
                      >
                        {item.canonical_title}
                      </Link>
                      <p className="text-[11px] text-zinc-400">
                        {item.genres?.slice(0, 2).join(" • ") || "Cinema"}
                        {item.directors?.length
                          ? ` • ${item.directors.join(", ")}`
                          : ""}
                      </p>
                      {item.explanation?.explanation_text && (
                        <p className="text-[11px] text-zinc-500 italic line-clamp-1">
                          &ldquo;{item.explanation.explanation_text}&rdquo;
                        </p>
                      )}
                    </div>

                    <div className="shrink-0 flex items-center gap-3">
                      <span className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full text-xs font-semibold">
                        <Sparkles className="w-3 h-3" />
                        {Math.round(item.recommendation_score)}%
                      </span>
                      <Link
                        href={`/movies/${item.title_id}`}
                        className="text-zinc-500 hover:text-violet-400 p-1"
                      >
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
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
                      <h4 className="text-xs font-bold text-zinc-100">
                        {item.title}
                      </h4>
                      <p className="text-[11px] text-zinc-400">{item.genre}</p>
                      <p className="text-[11px] text-zinc-500 italic">
                        &ldquo;{item.note}&rdquo;
                      </p>
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
            )}
          </div>

          {/* Right Column: Quick Navigation & Actions */}
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

                <Link
                  href="/history"
                  className="flex items-center justify-between p-3 rounded-xl bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300 hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <History className="w-4 h-4 text-cyan-400" />
                    <span>View Watch History</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-500" />
                </Link>

                <Link
                  href="/collections"
                  className="flex items-center justify-between p-3 rounded-xl bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300 hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <Layers className="w-4 h-4 text-pink-400" />
                    <span>Curated Collections</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-500" />
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Analytics Breakdown Grid: Genres, Creators, & Monthly Trends */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Top 5 Genres Breakdown */}
          <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-900 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-violet-400" />
                <h3 className="text-sm font-bold text-zinc-100">
                  Top 5 Genre Affinities
                </h3>
              </div>
              <span className="text-[11px] text-zinc-400">Based on History</span>
            </div>

            <div className="space-y-3.5">
              {topGenres.map((g, index) => {
                const colors = [
                  "bg-violet-500",
                  "bg-indigo-500",
                  "bg-emerald-500",
                  "bg-cyan-500",
                  "bg-amber-500",
                ];
                const barColor = colors[index % colors.length];

                return (
                  <div key={g.genre} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-zinc-200">{g.genre}</span>
                      <span className="text-zinc-400">
                        {g.percentage.toFixed(1)}% ({g.count} titles)
                      </span>
                    </div>
                    <div className="h-2 w-full bg-zinc-950 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${barColor} rounded-full transition-all duration-500`}
                        style={{ width: `${Math.min(g.percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Directors & Actors Breakdown */}
          <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-900 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-zinc-100">
                  Top Creators & Cast
                </h3>
              </div>
              <span className="text-[11px] text-zinc-400">Affinities</span>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-[11px] font-semibold uppercase text-zinc-400 tracking-wider mb-2">
                  Directors
                </p>
                <div className="flex flex-wrap gap-2">
                  {topDirectors.map((d) => (
                    <span
                      key={d.name}
                      className="px-2.5 py-1 rounded-xl text-xs bg-zinc-950 border border-zinc-800 text-zinc-300 flex items-center gap-1.5"
                    >
                      <UserCheck className="w-3 h-3 text-violet-400" />
                      <span>{d.name}</span>
                      <span className="text-[10px] text-zinc-400 font-mono">
                        ({d.count})
                      </span>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-[11px] font-semibold uppercase text-zinc-400 tracking-wider mb-2">
                  Actors
                </p>
                <div className="flex flex-wrap gap-2">
                  {topActors.map((a) => (
                    <span
                      key={a.name}
                      className="px-2.5 py-1 rounded-xl text-xs bg-zinc-950 border border-zinc-800 text-zinc-300 flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3 h-3 text-emerald-400" />
                      <span>{a.name}</span>
                      <span className="text-[10px] text-zinc-400 font-mono">
                        ({a.count})
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Monthly Watch Activity Trend */}
          <div className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-900 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-zinc-100">
                  Monthly Watch Trend
                </h3>
              </div>
              <span className="text-[11px] text-zinc-400">Hours Logged</span>
            </div>

            <div className="flex items-end justify-between gap-2 h-44 pt-6">
              {monthlyTrend.map((m) => {
                const heightPercent = Math.max(
                  Math.round((m.hours / maxTrendHours) * 100),
                  12
                );

                return (
                  <div
                    key={m.month}
                    className="flex-1 flex flex-col items-center gap-2 group"
                  >
                    <div className="text-[10px] text-zinc-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                      {m.hours.toFixed(0)}h
                    </div>
                    <div className="w-full bg-zinc-950 rounded-t-lg overflow-hidden flex items-end h-28">
                      <div
                        className="w-full bg-gradient-to-t from-violet-600 to-indigo-500 rounded-t-lg group-hover:from-violet-500 group-hover:to-indigo-400 transition-all duration-300"
                        style={{ height: `${heightPercent}%` }}
                      />
                    </div>
                    <span className="text-[11px] text-zinc-400 font-medium">
                      {m.month}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
