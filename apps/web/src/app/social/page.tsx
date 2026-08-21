"use client";

import React, { useMemo, useState } from "react";
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
  Users,
} from "lucide-react";
import {
  getRecommendations,
  updateRecommendationStatus,
  toggleWatchlistState,
  type RecommendationItem,
} from "@/lib/api/personal";
import { getFriendships, getTasteMatches } from "@/lib/api/ai";
import { LoadingState } from "@/components/ui/States";

const FALLBACK_POSTER =
  "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80";

export default function SocialRecommendationsPage() {
  const [activeTab, setActiveTab] = useState<"inbox" | "ai" | "sent">("inbox");
  const [filterScore, setFilterScore] = useState<number>(0);
  const queryClient = useQueryClient();

  const { data: received = [], isLoading: isLoadingReceived } = useQuery({
    queryKey: ["recommendations", "received"],
    queryFn: () => getRecommendations({ role: "received" }),
  });

  const { data: sent = [], isLoading: isLoadingSent } = useQuery({
    queryKey: ["recommendations", "sent"],
    queryFn: () => getRecommendations({ role: "sent" }),
  });

  const { data: friendships = [] } = useQuery({
    queryKey: ["friendships"],
    queryFn: getFriendships,
  });

  // Real cosine-similarity taste compatibility (services/api/repositories/social.py's
  // get_taste_compatibility) -- replaces the old hardcoded 95%/98.4% badges.
  // Symmetric, so "my score with friend X" also answers "sender X's score with me".
  const { data: tasteMatches = [] } = useQuery({
    queryKey: ["taste-matches"],
    queryFn: () => getTasteMatches(50),
  });
  const tasteMatchMap = useMemo(() => {
    const map = new Map<string, number>();
    tasteMatches.forEach((m) => map.set(m.friend_id, m.compatibility_score));
    return map;
  }, [tasteMatches]);

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "ACCEPTED" | "REJECTED"; titleId: string }) =>
      updateRecommendationStatus(id, status),
    onSuccess: async (_result, variables) => {
      // Backend doesn't add accepted recommendations to the watchlist as a
      // side effect -- do it explicitly so "Accept & Watchlist" is true.
      // Isolated in try/catch: the recommendation status update already
      // succeeded server-side by this point, so a transient watchlist-toggle
      // failure must not prevent the UI from refreshing to reflect that.
      if (variables.status === "ACCEPTED") {
        try {
          await toggleWatchlistState(variables.titleId, true);
        } catch (err) {
          console.error("Failed to add accepted recommendation to watchlist", err);
        }
      }
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });

  const handleAction = (rec: RecommendationItem, newStatus: "ACCEPTED" | "REJECTED") => {
    updateStatusMutation.mutate({ id: rec.recommendation_id, status: newStatus, titleId: rec.title_id });
  };

  const isLoading = isLoadingReceived || isLoadingSent;
  const pendingCount = received.filter((r) => r.status === "SENT").length;

  const visibleRecommendations = activeTab === "sent" ? sent : received;
  const filteredItems = visibleRecommendations.filter((rec) => {
    const otherPartyId = activeTab === "sent" ? rec.recipient_id : rec.sender_id;
    const score = tasteMatchMap.get(otherPartyId);
    if (filterScore > 0 && (score ?? -1) < filterScore) return false;
    return true;
  });

  const acceptedFriends = friendships.filter((f) => f.status === "ACCEPTED");
  const friendMatches = acceptedFriends
    .map((f) => ({ friend: f, score: tasteMatchMap.get(f.friend_id) }))
    .sort((a, b) => (b.score ?? -1) - (a.score ?? -1));

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

          {activeTab !== "ai" && (
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
          )}
        </div>

        {activeTab === "ai" ? (
          /* AI TASTE MATCH LEADERBOARD -- real cosine similarity across accepted friends */
          friendMatches.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-zinc-900/40 border border-zinc-900 text-zinc-400 space-y-3">
              <Sparkles className="w-8 h-8 text-zinc-600 mx-auto" />
              <h3 className="text-sm font-semibold text-zinc-200">No Taste Matches Yet</h3>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                Add accepted friends and build up your watch history to see real taste
                compatibility scores here.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {friendMatches.map(({ friend, score }) => (
                <div
                  key={friend.friend_id}
                  className="p-4 rounded-2xl border border-zinc-800/80 bg-zinc-900/40 backdrop-blur-md flex items-center gap-3"
                >
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shadow-md text-xs font-bold shrink-0">
                    {(friend.friend_name || "?").charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-zinc-100 truncate">
                      {friend.friend_name || "Unknown Member"}
                    </p>
                    <p className="text-[10px] text-zinc-500">
                      {friend.friend_username ? `@${friend.friend_username}` : "No taste vector yet"}
                    </p>
                  </div>
                  {score !== undefined ? (
                    <div className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full text-[11px] font-semibold shrink-0">
                      <Sparkles className="w-3 h-3" />
                      {score.toFixed(1)}%
                    </div>
                  ) : (
                    <span className="text-[10px] text-zinc-600 shrink-0">No score yet</span>
                  )}
                </div>
              ))}
            </div>
          )
        ) : filteredItems.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-zinc-900/40 border border-zinc-900 text-zinc-400 space-y-3">
            {activeTab === "sent" ? (
              <Send className="w-8 h-8 text-zinc-600 mx-auto" />
            ) : (
              <Inbox className="w-8 h-8 text-zinc-600 mx-auto" />
            )}
            <h3 className="text-sm font-semibold text-zinc-200">
              {activeTab === "sent" ? "No Sent Recommendations Yet" : "Your Inbox Is Empty"}
            </h3>
            <p className="text-xs text-zinc-500 max-w-sm mx-auto">
              {activeTab === "sent"
                ? "Recommendations you dispatch to friends from movie detail pages will be tracked here."
                : "Recommendations friends send you will show up here."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredItems.map((rec) => {
              const isSent = activeTab === "sent";
              const otherPartyId = isSent ? rec.recipient_id : rec.sender_id;
              const otherPartyName = isSent ? rec.recipient_name : rec.sender_name;
              const score = tasteMatchMap.get(otherPartyId);
              const isAccepted = rec.status === "ACCEPTED" || rec.status === "WATCHED" || rec.status === "RATED";
              const isRejected = rec.status === "REJECTED";
              const movieTitle = rec.canonical_title || "Unknown Title";

              return (
                <div
                  key={rec.recommendation_id}
                  className={`group relative p-5 rounded-2xl border transition-all duration-300 bg-zinc-900/40 backdrop-blur-md flex flex-col justify-between ${
                    isAccepted
                      ? "border-emerald-500/30 bg-emerald-950/10"
                      : isRejected
                      ? "border-zinc-900 opacity-50 bg-zinc-950/50"
                      : "border-zinc-800/80 hover:border-zinc-700 hover:shadow-xl hover:shadow-violet-950/20"
                  } ${
                    updateStatusMutation.isPending && updateStatusMutation.variables?.id === rec.recommendation_id
                      ? "opacity-50"
                      : ""
                  }`}
                >
                  {/* Peer Header + Real Taste Match Badge */}
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shadow-md text-xs font-bold">
                        {(otherPartyName || "?").charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-zinc-100">
                          {isSent ? "To " : ""}
                          {otherPartyName || "Unknown Member"}
                        </h4>
                        <span className="text-[11px] text-zinc-500">
                          {new Date(rec.sent_at).toLocaleString()}
                        </span>
                      </div>
                    </div>

                    {score !== undefined && (
                      <div className="inline-flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 backdrop-blur-md px-3 py-1 rounded-full text-xs font-semibold shadow-sm">
                        <Sparkles className="w-3 h-3 text-emerald-400" />
                        <span>{score.toFixed(1)}% Match</span>
                      </div>
                    )}
                  </div>

                  {/* Movie Card Preview & Note */}
                  <div className="flex gap-4 p-3 rounded-xl bg-zinc-950/60 border border-zinc-900 mb-4">
                    <Link
                      href={`/movies/${rec.title_id}`}
                      className="shrink-0 w-16 sm:w-20 aspect-[2/3] rounded-lg overflow-hidden bg-zinc-900 block group/poster"
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={rec.poster_url || FALLBACK_POSTER}
                        alt={movieTitle}
                        className="w-full h-full object-cover group-hover/poster:scale-105 transition-transform duration-300"
                      />
                    </Link>

                    <div className="flex-1 flex flex-col justify-between min-w-0">
                      <div>
                        <Link
                          href={`/movies/${rec.title_id}`}
                          className="text-sm font-bold text-zinc-100 hover:text-violet-400 transition-colors line-clamp-1"
                        >
                          {movieTitle}
                        </Link>
                        {rec.production_year && (
                          <div className="flex items-center gap-2 text-[11px] text-zinc-400 mt-0.5">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3 text-zinc-500" />
                              {rec.production_year}
                            </span>
                          </div>
                        )}
                      </div>

                      {rec.context_note && (
                        <p className="text-xs text-zinc-300/90 italic bg-zinc-900/60 p-2 rounded-lg border border-zinc-800/60 mt-2 line-clamp-2 leading-relaxed">
                          &ldquo;{rec.context_note}&rdquo;
                        </p>
                      )}
                    </div>
                  </div>

                  {/* ACTION BUTTONS (ACCEPT / DISMISS) -- inbox only, sent items are read-only */}
                  <div className="flex items-center justify-between pt-1">
                    {isAccepted ? (
                      <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                        <Check className="w-4 h-4" />
                        <span>{isSent ? "Accepted" : "Accepted & Added to Watchlist"}</span>
                      </div>
                    ) : isRejected ? (
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <X className="w-4 h-4" />
                        <span>Recommendation Dismissed</span>
                      </div>
                    ) : isSent ? (
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <Users className="w-4 h-4" />
                        <span>Waiting on {otherPartyName || "your friend"}</span>
                      </div>
                    ) : (
                      <div className="w-full flex items-center justify-end gap-2.5">
                        <button
                          onClick={() => handleAction(rec, "REJECTED")}
                          disabled={updateStatusMutation.isPending}
                          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-medium text-zinc-400 hover:text-red-400 bg-zinc-900/80 hover:bg-red-950/30 border border-zinc-800 hover:border-red-900/50 transition-all cursor-pointer"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Dismiss</span>
                        </button>

                        <button
                          onClick={() => handleAction(rec, "ACCEPTED")}
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
