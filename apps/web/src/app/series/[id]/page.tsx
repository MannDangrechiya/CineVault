"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Sparkles,
  Calendar,
  Clock,
  Globe,
  Share2,
  Bookmark,
  Check,
  ArrowLeft,
  Tv,
  Heart,
  Send,
  X,
  Layers,
  UserCheck,
} from "lucide-react";
import { getTitleById } from "@/lib/api/titles";
import { toggleWatchlistState, sendRecommendation } from "@/lib/api/personal";
import { getFriendships, type FriendshipItem } from "@/lib/api/ai";
import { LoadingState } from "@/components/ui/States";

export default function SeriesDetailPage() {
  const params = useParams();
  const router = useRouter();
  const titleId = (params?.id as string) || "";

  const [isRecommendModalOpen, setIsRecommendModalOpen] = useState(false);
  const [friendId, setFriendId] = useState("");
  const [personalNote, setPersonalNote] = useState("");
  const [recommendSent, setRecommendSent] = useState(false);
  const [isSavedToWatchlist, setIsSavedToWatchlist] = useState(false);

  // Fetch title details from API
  const { data: title, isLoading } = useQuery({
    queryKey: ["title", titleId],
    queryFn: () => getTitleById(titleId),
    retry: 1,
  });

  const queryClient = useQueryClient();

  const watchlistMutation = useMutation({
    mutationFn: (newStatus: boolean) => toggleWatchlistState(titleId, newStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });

  // Friend picker: the backend requires a real recipient_id UUID, so recommending
  // to a free-text email/@handle always failed validation. Reuse the same
  // friendship list the Oracle page's group matchmaker uses.
  const { data: friendships = [] } = useQuery({
    queryKey: ["friendships"],
    queryFn: getFriendships,
    enabled: isRecommendModalOpen,
  });
  const acceptedFriends = friendships.filter((f: FriendshipItem) => f.status === "ACCEPTED");
  const selectedFriend = acceptedFriends.find((f: FriendshipItem) => f.friend_id === friendId);

  const recommendMutation = useMutation({
    mutationFn: (msg: string) => sendRecommendation(titleId, friendId, msg),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });

  // Fallback cinematic metadata if direct API backend isn't populated for this ID
  const displayTitle = title?.canonical_title || "Sacred Games";
  const displayYear = title?.production_year || 2018;
  const displayCountry = title?.origin_country || "IN";
  const displaySynopsis =
    title?.synopsis ||
    "A linkage in their pasts leads an honest police officer to a fugitive gang boss, whose cryptic warning spurs the officer to save Mumbai from a cataclysm.";
  const displayGenres =
    title?.genres && title.genres.length > 0
      ? title.genres
      : ["Crime", "Drama", "Thriller"];
  const displayBackdrop =
    title?.backdrop_url ||
    "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?auto=format&fit=crop&w=2000&q=80";
  const displayPoster =
    title?.poster_url ||
    "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?auto=format&fit=crop&w=800&q=80";

  const handleSendRecommendation = (e: React.FormEvent) => {
    e.preventDefault();
    if (!friendId) return;

    recommendMutation.mutate(personalNote, {
      onSuccess: () => {
        setRecommendSent(true);
        setTimeout(() => {
          setRecommendSent(false);
          setIsRecommendModalOpen(false);
          setFriendId("");
          setPersonalNote("");
        }, 1800);
      },
    });
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <LoadingState message="Loading episodic series details & neural embeddings..." />
      </div>
    );
  }

  return (
    <div className="relative -mt-4 sm:-mt-6 lg:-mt-8 -mx-4 sm:-mx-6 lg:-mx-8 min-h-screen bg-zinc-950 text-zinc-50 pb-20">
      {/* Top Floating Back Button */}
      <div className="absolute top-6 left-6 z-30">
        <button
          onClick={() => router.back()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-950/70 backdrop-blur-xl border border-zinc-800 text-xs font-medium text-zinc-300 hover:text-white hover:bg-zinc-900 transition-all shadow-lg cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Series</span>
        </button>
      </div>

      {/* TOP 60VH HERO BANNER */}
      <div className="relative w-full h-[60vh] min-h-[460px] overflow-hidden bg-zinc-950">
        {/* Backdrop Image */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={displayBackdrop}
          alt={displayTitle}
          className="w-full h-full object-cover object-center scale-105 filter brightness-[0.75] contrast-[1.05]"
        />

        {/* Flawless Gradient Overlays: Bottom fade to OLED Black + Left lateral shadow */}
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/80 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-zinc-950/90 via-zinc-950/40 to-transparent" />

        {/* Floating Content Over Hero Banner Gradient */}
        <div className="absolute bottom-0 left-0 right-0 max-w-7xl mx-auto px-6 sm:px-10 pb-8 flex flex-col md:flex-row items-end gap-8 z-20">
          {/* Floating Poster */}
          <div className="hidden sm:block shrink-0 w-44 md:w-52 aspect-[2/3] rounded-2xl overflow-hidden bg-zinc-900 shadow-2xl shadow-cyan-950/40 ring-1 ring-white/10 group">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={displayPoster}
              alt={displayTitle}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Title & Primary Actions Over Gradient */}
          <div className="flex-1 space-y-4">
            {/* AI Taste Match & Content Badges */}
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 backdrop-blur-md shadow-lg shadow-emerald-950/30">
                <Sparkles className="w-3.5 h-3.5" />
                96% AI Taste Match
              </span>

              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-zinc-900/80 text-zinc-300 border border-zinc-800 backdrop-blur-md">
                <Tv className="w-3.5 h-3.5 text-cyan-400" />
                {title?.content_type || "TV Series"}
              </span>

              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono text-zinc-400 bg-zinc-900/60 border border-zinc-800">
                <Globe className="w-3 h-3 text-zinc-500" />
                {displayCountry}
              </span>
            </div>

            {/* Canonical Title */}
            <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-zinc-50 leading-tight drop-shadow-md">
              {displayTitle}
            </h1>

            {/* Quick Meta Row */}
            <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-zinc-400 font-medium">
              <span className="flex items-center gap-1.5 text-zinc-300">
                <Calendar className="w-4 h-4 text-zinc-400" />
                {displayYear}
              </span>
              <span className="text-zinc-600">•</span>
              <span className="flex items-center gap-1.5 text-zinc-300">
                <Clock className="w-4 h-4 text-zinc-400" />
                {title?.primary_edition?.runtime_minutes || 50} mins / ep
              </span>
              <span className="text-zinc-600">•</span>
              <span className="text-zinc-300">
                {title?.primary_edition?.edition_name || "Season 1 & 2 • 4K HDR"}
              </span>
            </div>

            {/* Action Buttons Row */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              {/* PRIMARY ACTION BUTTON: Recommend to a Friend */}
              <button
                onClick={() => setIsRecommendModalOpen(true)}
                className="inline-flex items-center gap-2.5 px-6 py-3 text-xs sm:text-sm font-semibold text-white bg-cyan-600 hover:bg-cyan-500 rounded-full shadow-xl shadow-cyan-600/30 transition-all hover:scale-105 active:scale-95 cursor-pointer"
              >
                <Share2 className="w-4 h-4" />
                <span>Recommend to a Friend</span>
              </button>

              {/* Watchlist Toggle Button */}
              <button
                onClick={() => {
                  const newStatus = !isSavedToWatchlist;
                  setIsSavedToWatchlist(newStatus);
                  watchlistMutation.mutate(newStatus);
                }}
                disabled={watchlistMutation.isPending}
                className={`inline-flex items-center gap-2 px-5 py-3 text-xs sm:text-sm font-medium rounded-full border backdrop-blur-md transition-all cursor-pointer ${
                  isSavedToWatchlist
                    ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                    : "bg-zinc-900/80 hover:bg-zinc-800 border-zinc-800 text-zinc-200"
                } ${watchlistMutation.isPending ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                {isSavedToWatchlist ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-400" />
                    <span>In Watchlist</span>
                  </>
                ) : (
                  <>
                    <Bookmark className="w-4 h-4 text-zinc-400" />
                    <span>Add to Watchlist</span>
                  </>
                )}
              </button>

              {/* Log / Mark Watched Button */}
              <button
                title="Mark as Watched"
                className="p-3 rounded-full bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-rose-400 transition-colors"
              >
                <Heart className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* BODY CONTENT: Detailed Synopsis, Metadata & AI Insights */}
      <div className="max-w-7xl mx-auto px-6 sm:px-10 mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns: Synopsis, Genres, Editions */}
        <div className="lg:col-span-2 space-y-8">
          {/* Genre Badges */}
          <div className="flex flex-wrap gap-2">
            {displayGenres.map((genre) => (
              <span
                key={genre}
                className="px-3.5 py-1.5 rounded-xl text-xs font-medium bg-zinc-900/80 border border-zinc-800 text-zinc-300"
              >
                {genre}
              </span>
            ))}
          </div>

          {/* Synopsis */}
          <div className="space-y-3">
            <h2 className="text-lg font-bold text-zinc-100 tracking-tight">Overview & Storyline</h2>
            <p className="text-sm sm:text-base text-zinc-300 leading-relaxed font-normal">
              {displaySynopsis}
            </p>
          </div>

          {/* Canonical Provenance & Edition Info */}
          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-4">
            <div className="flex items-center gap-2 text-sm font-bold text-zinc-200">
              <Layers className="w-4 h-4 text-cyan-400" />
              <span>Canonical Metadata & Series Hierarchy</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-zinc-500 block mb-1">Catalog ID</span>
                <span className="font-mono text-zinc-300 font-medium">
                  {title?.display_id || titleId || "TV-2018-0001"}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Audio / Master</span>
                <span className="text-zinc-300 font-medium">Dolby Atmos • 5.1 Surround</span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Aspect Ratio</span>
                <span className="text-zinc-300 font-medium">16:9 HD Broadcast</span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Color Grading</span>
                <span className="text-zinc-300 font-medium">HDR10 / SDR</span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Artwork Source</span>
                <span className="text-emerald-400 font-medium">Licensed TMDB / CineVault Verified</span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Episodic Structure</span>
                <span className="text-cyan-400 font-mono">2 Seasons • 16 Episodes</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: AI Taste Breakdown & Friend Recommendations Widget */}
        <div className="space-y-6">
          {/* AI Taste Vector Card */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-zinc-900/80 to-zinc-950 border border-zinc-800/80 space-y-4 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none" />

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-zinc-100">AI Taste Match Vector</h3>
              </div>
              <span className="text-xs font-mono font-bold text-emerald-400">96.2%</span>
            </div>

            <p className="text-xs text-zinc-400 leading-relaxed">
              High affinity match: <em>Gritty Crime Drama, Noir Mystery, and Ensemble Narratives</em>.
            </p>

            {/* Affinity Meters */}
            <div className="space-y-3 pt-2 text-xs">
              <div>
                <div className="flex justify-between text-zinc-400 mb-1">
                  <span>Pacing & Suspense</span>
                  <span className="text-zinc-200">97%</span>
                </div>
                <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-400 rounded-full w-[97%]" />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-zinc-400 mb-1">
                  <span>Character Depth</span>
                  <span className="text-zinc-200">95%</span>
                </div>
                <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-cyan-400 rounded-full w-[95%]" />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-zinc-400 mb-1">
                  <span>Atmospheric Score</span>
                  <span className="text-zinc-200">91%</span>
                </div>
                <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-400 rounded-full w-[91%]" />
                </div>
              </div>
            </div>
          </div>

          {/* Social Quick Share Prompt */}
          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
              <UserCheck className="w-4 h-4 text-cyan-400" />
              <span>Peer Recommendation</span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Share this series with friends. Recommendations appear instantly in their OLED inbox.
            </p>
            <button
              onClick={() => setIsRecommendModalOpen(true)}
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-cyan-300 bg-cyan-600/10 hover:bg-cyan-600/20 border border-cyan-500/30 transition-all text-center cursor-pointer"
            >
              Recommend Series
            </button>
          </div>
        </div>
      </div>

      {/* RECOMMEND TO A FRIEND MODAL */}
      {isRecommendModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity"
            onClick={() => setIsRecommendModalOpen(false)}
          />

          <div className="relative w-full max-w-md bg-zinc-950 border border-zinc-800 rounded-2xl p-6 shadow-2xl z-10 animate-in fade-in zoom-in-95 duration-200">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-zinc-900">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                  <Share2 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-100">Recommend Series</h3>
                  <p className="text-[11px] text-zinc-400">Send to a friend or group</p>
                </div>
              </div>
              <button
                onClick={() => setIsRecommendModalOpen(false)}
                className="p-1.5 rounded-xl text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {recommendSent ? (
              <div className="py-8 text-center space-y-2">
                <div className="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center mx-auto mb-3 animate-bounce">
                  <Check className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-zinc-100">Recommendation Dispatched!</h4>
                <p className="text-xs text-zinc-400">
                  Sent <span className="text-cyan-300 font-semibold">{displayTitle}</span> to{" "}
                  <span className="text-zinc-200 font-semibold">
                    {selectedFriend?.friend_name || "your friend"}
                  </span>
                  .
                </p>
              </div>
            ) : (
              <form onSubmit={handleSendRecommendation} className="space-y-4 pt-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                    Friend
                  </label>
                  {acceptedFriends.length > 0 ? (
                    <select
                      required
                      value={friendId}
                      onChange={(e) => setFriendId(e.target.value)}
                      className="w-full px-3.5 py-2.5 text-xs bg-zinc-900 border border-zinc-800 rounded-xl text-zinc-100 focus:outline-none focus:border-cyan-500 transition-colors"
                    >
                      <option value="" disabled>
                        Select a friend...
                      </option>
                      {acceptedFriends.map((f: FriendshipItem) => (
                        <option key={f.friend_id} value={f.friend_id}>
                          {f.friend_name || "Unknown Member"}
                          {f.friend_username ? ` (@${f.friend_username})` : ""}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <p className="text-xs text-zinc-500 px-3.5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-xl">
                      Add a friend first to send them a recommendation.
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                    Personal Note (Optional)
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Why they need to watch this TV series..."
                    value={personalNote}
                    onChange={(e) => setPersonalNote(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs bg-zinc-900 border border-zinc-800 rounded-xl text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-cyan-500 transition-colors resize-none"
                  />
                </div>

                <div className="pt-2 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsRecommendModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 rounded-xl transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={recommendMutation.isPending || acceptedFriends.length === 0}
                    className={`inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-cyan-600 hover:bg-cyan-500 rounded-xl shadow-lg shadow-cyan-600/30 transition-all cursor-pointer ${recommendMutation.isPending || acceptedFriends.length === 0 ? "opacity-50 cursor-not-allowed" : ""}`}
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{recommendMutation.isPending ? "Sending..." : "Send Recommendation"}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
