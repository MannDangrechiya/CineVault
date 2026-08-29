"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
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
  LibraryBig,
  FolderPlus,
} from "lucide-react";
import { getTitleById } from "@/lib/api/titles";
import { toggleWatchlistState, sendRecommendation, addToLibrary, logWatchEvent } from "@/lib/api/personal";
import { getFriendships, type FriendshipItem } from "@/lib/api/ai";
import { getCollections, addCollectionItem } from "@/lib/api/collections";
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
  const [isAddedToLibrary, setIsAddedToLibrary] = useState(false);
  const [isMarkedWatched, setIsMarkedWatched] = useState(false);
  const [isCollectionModalOpen, setIsCollectionModalOpen] = useState(false);
  const [addedCollectionIds, setAddedCollectionIds] = useState<string[]>([]);

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

  // Personal Media Library had a backend + a listing page, but no entry point
  // anywhere actually called POST /v1/personal/library (see WEB_FEATURE_AUDIT.md).
  const libraryMutation = useMutation({
    mutationFn: () => addToLibrary(titleId),
    onSuccess: () => {
      setIsAddedToLibrary(true);
      queryClient.invalidateQueries({ queryKey: ["library"] });
    },
  });

  // "Mark as Watched" heart button had no onClick at all -- a fully dead
  // button, even though POST /v1/me/watch-events already works and powers
  // the real Watch History page.
  const watchEventMutation = useMutation({
    mutationFn: () => logWatchEvent(titleId),
    onSuccess: () => {
      setIsMarkedWatched(true);
      queryClient.invalidateQueries({ queryKey: ["history"] });
      queryClient.invalidateQueries({ queryKey: ["personalAnalytics"] });
      queryClient.invalidateQueries({ queryKey: ["userBadges"] });
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

  // Add to Collection: a collection could previously be created but never
  // actually populated -- there was no add-item endpoint at all (see
  // WEB_FEATURE_AUDIT.md). Reuses the user's real collection list.
  const { data: myCollections = [] } = useQuery({
    queryKey: ["collections"],
    queryFn: getCollections,
    enabled: isCollectionModalOpen,
  });
  const addToCollectionMutation = useMutation({
    mutationFn: (collectionId: string) => addCollectionItem(collectionId, titleId),
    onSuccess: (_data, collectionId) => {
      setAddedCollectionIds((prev) => [...prev, collectionId]);
      queryClient.invalidateQueries({ queryKey: ["collection-detail"] });
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });

  const recommendMutation = useMutation({
    mutationFn: (msg: string) => sendRecommendation(titleId, friendId, msg),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });

  // Honest display values — real API data only. No fabricated placeholder
  // title/genres/country/synopsis: the catalog legitimately has null/empty
  // fields for most titles (see WEB_FEATURE_AUDIT.md), so these render
  // conditionally or with a plain "not available" note instead of inventing
  // Sacred Games metadata for whatever title happens to be missing data.
  const displayTitle = title?.canonical_title || "Untitled";
  const displayYear = title?.production_year;
  const displayCountry = title?.origin_country;
  const displaySynopsis = title?.synopsis;
  const displayGenres = title?.genres && title.genres.length > 0 ? title.genres : [];
  const displayBackdrop = title?.backdrop_url || null;
  const displayPoster = title?.poster_url || null;

  const seasonCount = title?.seasons?.length ?? 0;
  const episodeCount =
    title?.seasons?.reduce((total, season) => total + (season.episodes?.length ?? 0), 0) ?? 0;

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
        {/* Backdrop Image (honest placeholder when no real artwork has synced) */}
        {displayBackdrop ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={displayBackdrop}
            alt={displayTitle}
            className="w-full h-full object-cover object-center scale-105 filter brightness-[0.75] contrast-[1.05]"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-zinc-900 via-zinc-950 to-black flex items-center justify-center">
            <Tv className="w-16 h-16 text-zinc-800" />
          </div>
        )}

        {/* Flawless Gradient Overlays: Bottom fade to OLED Black + Left lateral shadow */}
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/80 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-zinc-950/90 via-zinc-950/40 to-transparent" />

        {/* Floating Content Over Hero Banner Gradient */}
        <div className="absolute bottom-0 left-0 right-0 max-w-7xl mx-auto px-6 sm:px-10 pb-8 flex flex-col md:flex-row items-end gap-8 z-20">
          {/* Floating Poster */}
          <div className="hidden sm:block shrink-0 w-44 md:w-52 aspect-[2/3] rounded-2xl overflow-hidden bg-zinc-900 shadow-2xl shadow-cyan-950/40 ring-1 ring-white/10 group">
            {displayPoster ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={displayPoster}
                alt={displayTitle}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-zinc-900 to-zinc-950">
                <Tv className="w-10 h-10 text-zinc-700" />
              </div>
            )}
          </div>

          {/* Title & Primary Actions Over Gradient */}
          <div className="flex-1 space-y-4">
            {/* Content Badges */}
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-zinc-900/80 text-zinc-300 border border-zinc-800 backdrop-blur-md">
                <Tv className="w-3.5 h-3.5 text-cyan-400" />
                {title?.content_type || "TV Series"}
              </span>

              {displayCountry && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono text-zinc-400 bg-zinc-900/60 border border-zinc-800">
                  <Globe className="w-3 h-3 text-zinc-500" />
                  {displayCountry}
                </span>
              )}
            </div>

            {/* Canonical Title */}
            <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-zinc-50 leading-tight drop-shadow-md">
              {displayTitle}
            </h1>

            {/* Quick Meta Row */}
            <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-zinc-400 font-medium">
              {displayYear && (
                <>
                  <span className="flex items-center gap-1.5 text-zinc-300">
                    <Calendar className="w-4 h-4 text-zinc-400" />
                    {displayYear}
                  </span>
                  <span className="text-zinc-600">•</span>
                </>
              )}
              {title?.primary_edition?.runtime_minutes ? (
                <>
                  <span className="flex items-center gap-1.5 text-zinc-300">
                    <Clock className="w-4 h-4 text-zinc-400" />
                    {title.primary_edition.runtime_minutes} mins / ep
                  </span>
                  <span className="text-zinc-600">•</span>
                </>
              ) : null}
              <span className="text-zinc-300">
                {title?.primary_edition?.edition_name ||
                  (title?.primary_edition?.runtime_minutes ? "" : "Runtime & edition not available")}
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

              {/* Add to Library Button */}
              <button
                onClick={() => libraryMutation.mutate()}
                disabled={libraryMutation.isPending || isAddedToLibrary}
                className={`inline-flex items-center gap-2 px-5 py-3 text-xs sm:text-sm font-medium rounded-full border backdrop-blur-md transition-all cursor-pointer ${
                  isAddedToLibrary
                    ? "bg-cyan-500/20 border-cyan-500/40 text-cyan-300"
                    : "bg-zinc-900/80 hover:bg-zinc-800 border-zinc-800 text-zinc-200"
                } ${libraryMutation.isPending ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                {isAddedToLibrary ? (
                  <>
                    <Check className="w-4 h-4 text-cyan-400" />
                    <span>In Library</span>
                  </>
                ) : (
                  <>
                    <LibraryBig className="w-4 h-4 text-zinc-400" />
                    <span>Add to Library</span>
                  </>
                )}
              </button>

              {/* Add to Collection Button */}
              <button
                onClick={() => setIsCollectionModalOpen(true)}
                title="Add to Collection"
                className="p-3 rounded-full bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-cyan-400 transition-colors"
              >
                <FolderPlus className="w-4 h-4" />
              </button>

              {/* Log / Mark Watched Button */}
              <button
                onClick={() => watchEventMutation.mutate()}
                disabled={watchEventMutation.isPending || isMarkedWatched}
                title={isMarkedWatched ? "Logged to Watch History" : "Mark as Watched"}
                className={`p-3 rounded-full border transition-colors disabled:cursor-not-allowed ${
                  isMarkedWatched
                    ? "bg-rose-500/20 border-rose-500/40 text-rose-400"
                    : "bg-zinc-900/80 hover:bg-zinc-800 border-zinc-800 text-zinc-400 hover:text-rose-400"
                }`}
              >
                <Heart className={`w-4 h-4 ${isMarkedWatched ? "fill-rose-400" : ""}`} />
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
          {displayGenres.length > 0 ? (
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
          ) : (
            <p className="text-xs text-zinc-500 italic">No genre data available for this title.</p>
          )}

          {/* Synopsis */}
          <div className="space-y-3">
            <h2 className="text-lg font-bold text-zinc-100 tracking-tight">Overview & Storyline</h2>
            <p className="text-sm sm:text-base text-zinc-300 leading-relaxed font-normal">
              {displaySynopsis || "No synopsis available for this title yet."}
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
                  {title?.display_id || titleId || "Unknown"}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Audio / Master</span>
                {title?.primary_edition?.sound_mix ? (
                  <span className="text-zinc-300 font-medium">{title.primary_edition.sound_mix}</span>
                ) : (
                  <span className="text-zinc-500 font-medium">Not available</span>
                )}
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Aspect Ratio</span>
                {title?.primary_edition?.aspect_ratio ? (
                  <span className="text-zinc-300 font-medium">{title.primary_edition.aspect_ratio}</span>
                ) : (
                  <span className="text-zinc-500 font-medium">Not available</span>
                )}
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Color Grading</span>
                {title?.primary_edition?.color_format ? (
                  <span className="text-zinc-300 font-medium">{title.primary_edition.color_format}</span>
                ) : (
                  <span className="text-zinc-500 font-medium">Not available</span>
                )}
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Artwork Source</span>
                {title?.has_licensed_artwork ? (
                  <span className="text-emerald-400 font-medium">Licensed Artwork</span>
                ) : (
                  <span className="text-zinc-500 font-medium">Artwork Pending Sync</span>
                )}
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Episodic Structure</span>
                {seasonCount > 0 ? (
                  <span className="text-cyan-400 font-mono">
                    {seasonCount} Season{seasonCount !== 1 ? "s" : ""} • {episodeCount} Episode
                    {episodeCount !== 1 ? "s" : ""}
                  </span>
                ) : (
                  <span className="text-zinc-500 font-medium">Not available</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Friend Recommendations Widget */}
        <div className="space-y-6">
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

      {/* ADD TO COLLECTION MODAL */}
      {isCollectionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity"
            onClick={() => setIsCollectionModalOpen(false)}
          />
          <div className="relative w-full max-w-md p-6 rounded-3xl bg-zinc-950 border border-zinc-800 shadow-2xl space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <FolderPlus className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-zinc-100">Add to Collection</h3>
              </div>
              <button
                onClick={() => setIsCollectionModalOpen(false)}
                className="p-1 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {myCollections.length === 0 ? (
              <p className="text-xs text-zinc-500 text-center py-6">
                You don&apos;t have any collections yet.{" "}
                <Link href="/collections" className="text-cyan-400 hover:underline">
                  Create one first
                </Link>
                .
              </p>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {myCollections.map((c) => {
                  const isAdded = addedCollectionIds.includes(c.id);
                  const isThisPending =
                    addToCollectionMutation.isPending && addToCollectionMutation.variables === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => addToCollectionMutation.mutate(c.id)}
                      disabled={isAdded || isThisPending}
                      className={`w-full flex items-center justify-between gap-3 p-3 rounded-xl border text-left transition-all cursor-pointer disabled:cursor-not-allowed ${
                        isAdded
                          ? "bg-cyan-600/10 border-cyan-500/30"
                          : "bg-zinc-900/60 border-zinc-800 hover:border-zinc-700"
                      }`}
                    >
                      <div>
                        <p className="text-xs font-bold text-zinc-100">{c.name}</p>
                        <p className="text-[10px] text-zinc-500">{c.item_count} titles</p>
                      </div>
                      {isAdded ? (
                        <Check className="w-4 h-4 text-cyan-400 shrink-0" />
                      ) : (
                        <FolderPlus className="w-4 h-4 text-zinc-500 shrink-0" />
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
