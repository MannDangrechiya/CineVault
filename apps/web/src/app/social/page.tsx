"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  Sparkles,
  Inbox,
  Send,
  Check,
  X,
  Calendar,
  BookmarkPlus,
  Share2,
  SlidersHorizontal,
  Bot,
} from "lucide-react";
import { getRecommendations, updateRecommendationStatus } from "@/lib/api/personal";
import { LoadingState } from "@/components/ui/States";

export default function SocialRecommendationsPage() {
  const [activeTab, setActiveTab] = useState<"inbox" | "ai" | "sent">("inbox");
  const [filterScore, setFilterScore] = useState<number>(0);
  const queryClient = useQueryClient();

  const { data: rawRecommendations = [], isLoading } = useQuery({
    queryKey: ["recommendations"],
    queryFn: getRecommendations,
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "accepted" | "dismissed" }) =>
      updateRecommendationStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["watchlist"] }); // Accepting adds to watchlist
    },
  });

  const handleAction = (id: string, newStatus: "accepted" | "dismissed") => {
    updateStatusMutation.mutate({ id, status: newStatus });
  };

  // Map API models to UI models
  const recommendations = rawRecommendations.map((rec) => ({
    id: rec.id,
    movieTitle: rec.title?.canonical_title || "Unknown Title",
    movieId: rec.title_id,
    posterUrl: rec.title?.poster_url || "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80",
    year: rec.title?.production_year || 2024,
    sender: {
      name: rec.sender_name || "Anonymous",
      username: `@${rec.sender_name?.toLowerCase().replace(/\s/g, "_") || "user"}`,
      avatarBg: rec.sender_id === "ai" ? "from-emerald-600 to-teal-500" : "from-violet-600 to-indigo-500",
      isAI: rec.sender_id === "ai",
    },
    note: rec.message || "No message attached.",
    tasteMatch: 95, // hardcoded match score fallback
    timestamp: new Date(rec.sent_at).toLocaleString(),
    status: rec.status,
  }));

  const filteredItems = recommendations.filter((rec) => {
    if (rec.tasteMatch < filterScore) return false;
    if (activeTab === "ai") return rec.sender.isAI;
    if (activeTab === "sent") return false; // Demo sent view
    return true;
  });

  const pendingCount = recommendations.filter((r) => r.status === "pending").length;

  if (isLoading) {
    return (
      <PageContainer title="Social Inbox & AI Taste Match" subtitle="Loading your network insights...">
        <div className="p-8">
          <LoadingState message="Fetching recommendations..." />
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title="Social Inbox & AI Taste Match"
      subtitle="Curated peer recommendations, social circle exchange, and neural taste vector scores."
      action={
        <Link
          href="/movies"
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/30 transition-all"
        >
          <Share2 className="w-3.5 h-3.5" />
          <span>New Recommendation</span>
        </Link>
      }
    >
      <div className="space-y-6">
        {/* Navigation Tabs & Filter Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-zinc-900">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("inbox")}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                activeTab === "inbox"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              <Inbox className="w-3.5 h-3.5" />
              <span>Incoming Inbox</span>
              {pendingCount > 0 && (
                <span className="px-1.5 py-0.2 text-[10px] font-bold bg-violet-600 text-white rounded-full">
                  {pendingCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("ai")}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                activeTab === "ai"
                  ? "bg-emerald-500/15 text-emerald-300 font-semibold border border-emerald-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              <span>AI Taste Matches</span>
            </button>

            <button
              onClick={() => setActiveTab("sent")}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                activeTab === "sent"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              <Send className="w-3.5 h-3.5" />
              <span>Sent by You</span>
            </button>
          </div>

          {/* Quick Filter Control */}
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <SlidersHorizontal className="w-3.5 h-3.5 text-zinc-500" />
            <span>Min Match:</span>
            <select
              value={filterScore}
              onChange={(e) => setFilterScore(Number(e.target.value))}
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-1 text-xs text-zinc-200 focus:outline-none focus:border-violet-500"
            >
              <option value={0}>All Scores</option>
              <option value={90}>90%+ Match</option>
              <option value={95}>95%+ Match</option>
            </select>
          </div>
        </div>

        {/* REVEAL GRID FOR INCOMING RECOMMENDATIONS */}
        {activeTab === "sent" ? (
          <div className="p-12 text-center rounded-2xl bg-zinc-900/40 border border-zinc-900 text-zinc-400 space-y-3">
            <Send className="w-8 h-8 text-zinc-600 mx-auto" />
            <h3 className="text-sm font-semibold text-zinc-200">No Sent Recommendations History</h3>
            <p className="text-xs text-zinc-500 max-w-sm mx-auto">
              Recommendations you dispatch to peers from movie detail pages will be tracked here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredItems.map((rec) => {
              const isAccepted = rec.status === "accepted";
              const isRejected = rec.status === "dismissed";

              return (
                <div
                  key={rec.id}
                  className={`group relative p-5 rounded-2xl border transition-all duration-300 bg-zinc-900/40 backdrop-blur-md flex flex-col justify-between ${
                    isAccepted
                      ? "border-emerald-500/30 bg-emerald-950/10"
                      : isRejected
                      ? "border-zinc-900 opacity-50 bg-zinc-950/50"
                      : "border-zinc-800/80 hover:border-zinc-700 hover:shadow-xl hover:shadow-violet-950/20"
                  } ${updateStatusMutation.isPending && updateStatusMutation.variables?.id === rec.id ? 'opacity-50' : ''}`}
                >
                  {/* Sender Header + AI Taste Match Badge */}
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-9 h-9 rounded-xl bg-gradient-to-tr ${rec.sender.avatarBg} flex items-center justify-center text-white shadow-md text-xs font-bold`}
                      >
                        {rec.sender.isAI ? (
                          <Bot className="w-4 h-4" />
                        ) : (
                          rec.sender.name.charAt(0).toUpperCase()
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <h4 className="text-xs font-bold text-zinc-100">{rec.sender.name}</h4>
                          {rec.sender.isAI && (
                            <span className="px-1.5 py-0.2 text-[9px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-md">
                              AI Engine
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] text-zinc-500">{rec.timestamp}</span>
                      </div>
                    </div>

                    {/* GLOWING AI TASTE Match Badge */}
                    <div className="inline-flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 backdrop-blur-md px-3 py-1 rounded-full text-xs font-semibold shadow-sm">
                      <Sparkles className="w-3 h-3 text-emerald-400" />
                      <span>{rec.tasteMatch}% Match</span>
                    </div>
                  </div>

                  {/* Movie Card Preview & Sender Note */}
                  <div className="flex gap-4 p-3 rounded-xl bg-zinc-950/60 border border-zinc-900 mb-4">
                    {/* Poster */}
                    <Link
                      href={`/movies/${rec.movieId}`}
                      className="shrink-0 w-16 sm:w-20 aspect-[2/3] rounded-lg overflow-hidden bg-zinc-900 block group/poster"
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={rec.posterUrl}
                        alt={rec.movieTitle}
                        className="w-full h-full object-cover group-hover/poster:scale-105 transition-transform duration-300"
                      />
                    </Link>

                    {/* Movie Info & Note */}
                    <div className="flex-1 flex flex-col justify-between min-w-0">
                      <div>
                        <Link
                          href={`/movies/${rec.movieId}`}
                          className="text-sm font-bold text-zinc-100 hover:text-violet-400 transition-colors line-clamp-1"
                        >
                          {rec.movieTitle}
                        </Link>
                        <div className="flex items-center gap-2 text-[11px] text-zinc-400 mt-0.5">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-zinc-500" />
                            {rec.year}
                          </span>
                          <span>•</span>
                          <span className="text-zinc-400">Feature Film</span>
                        </div>
                      </div>

                      {/* Sender Note */}
                      <p className="text-xs text-zinc-300/90 italic bg-zinc-900/60 p-2 rounded-lg border border-zinc-800/60 mt-2 line-clamp-2 leading-relaxed">
                        &ldquo;{rec.note}&rdquo;
                      </p>
                    </div>
                  </div>

                  {/* ACTION BUTTONS (ACCEPT / DISMISS) */}
                  <div className="flex items-center justify-between pt-1">
                    {isAccepted ? (
                      <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                        <Check className="w-4 h-4" />
                        <span>Accepted & Added to Watchlist</span>
                      </div>
                    ) : isRejected ? (
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <X className="w-4 h-4" />
                        <span>Recommendation Dismissed</span>
                      </div>
                    ) : (
                      <div className="w-full flex items-center justify-end gap-2.5">
                        <button
                          onClick={() => handleAction(rec.id, "dismissed")}
                          disabled={updateStatusMutation.isPending}
                          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-medium text-zinc-400 hover:text-red-400 bg-zinc-900/80 hover:bg-red-950/30 border border-zinc-800 hover:border-red-900/50 transition-all cursor-pointer"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Dismiss</span>
                        </button>

                        <button
                          onClick={() => handleAction(rec.id, "accepted")}
                          disabled={updateStatusMutation.isPending}
                          className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 border border-violet-500 shadow-md shadow-violet-600/30 transition-all hover:scale-105 active:scale-95 cursor-pointer"
                        >
                          <BookmarkPlus className="w-3.5 h-3.5" />
                          <span>Accept & Watchlist</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
