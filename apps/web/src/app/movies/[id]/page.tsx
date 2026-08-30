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
  Film,
  Heart,
  Send,
  X,
  Layers,
  UserCheck,
  LibraryBig,
  FolderPlus,
  Star,
  Trash2,
  ExternalLink,
  Users,
  Eye,
  Plus,
} from "lucide-react";
import { getTitleById } from "@/lib/api/titles";
import {
  toggleWatchlistState,
  sendRecommendation,
  addToLibrary,
  removeFromLibrary,
  getLibrary,
  logWatchEvent,
  getHistory,
  getUserTitleState,
  toggleFavoriteState,
  getUserRatings,
  setUserRating,
  deleteUserRating,
  getUserNotes,
  createUserNote,
  deleteUserNote,
  getUserReviews,
  createUserReview,
  deleteUserReview,
} from "@/lib/api/personal";
import { getFriendships, type FriendshipItem } from "@/lib/api/ai";
import { getCollections, addCollectionItem } from "@/lib/api/collections";
import { LoadingState } from "@/components/ui/States";

export default function MovieDetailPage() {
  const params = useParams();
  const router = useRouter();
  const titleId = (params?.id as string) || "";
  const queryClient = useQueryClient();

  // Modals & form state
  const [isRecommendModalOpen, setIsRecommendModalOpen] = useState(false);
  const [friendId, setFriendId] = useState("");
  const [recommendNote, setRecommendNote] = useState("");
  const [recommendSent, setRecommendSent] = useState(false);
  const [isCollectionModalOpen, setIsCollectionModalOpen] = useState(false);
  const [addedCollectionIds, setAddedCollectionIds] = useState<string[]>([]);

  // Note form state
  const [noteInput, setNoteInput] = useState("");
  const [isAddingNote, setIsAddingNote] = useState(false);

  // Review form state
  const [reviewTitle, setReviewTitle] = useState("");
  const [reviewText, setReviewText] = useState("");
  const [reviewContainsSpoilers, setReviewContainsSpoilers] = useState(false);
  const [isAddingReview, setIsAddingReview] = useState(false);

  // Active personal tab
  const [activePersonalTab, setActivePersonalTab] = useState<"rating" | "notes" | "reviews">("rating");

  // 1. Fetch title details
  const { data: title, isLoading, isError } = useQuery({
    queryKey: ["title", titleId],
    queryFn: () => getTitleById(titleId),
    retry: 1,
  });

  // 2. Fetch User Title State (Watchlist & Favorite)
  const { data: userTitleState } = useQuery({
    queryKey: ["userTitleState", titleId],
    queryFn: () => getUserTitleState(titleId),
    enabled: Boolean(titleId),
  });

  const isSavedToWatchlist =
    userTitleState?.manual_status_override === "PLAN_TO_WATCH" ||
    userTitleState?.manual_status_override === "WATCHLIST";
  const isFavorite = Boolean(userTitleState?.is_favorite);

  // 3. Fetch User Library
  const { data: libraryData } = useQuery({
    queryKey: ["library"],
    queryFn: () => getLibrary({ limit: 100 }),
    enabled: Boolean(titleId),
  });
  const isAddedToLibrary = libraryData?.items.some((i) => i.title_id === titleId) ?? false;

  // 4. Fetch Watch History (to determine if watched)
  const { data: historyData } = useQuery({
    queryKey: ["history"],
    queryFn: () => getHistory({ limit: 100 }),
    enabled: Boolean(titleId),
  });
  const isMarkedWatched = historyData?.items.some((i) => i.title_id === titleId) ?? false;

  // 5. Fetch Personal Ratings
  const { data: userRatings = [] } = useQuery({
    queryKey: ["ratings", titleId],
    queryFn: () => getUserRatings(titleId),
    enabled: Boolean(titleId),
  });
  const currentRating = userRatings.find((r) => r.title_id === titleId)?.rating_value ?? null;

  // 6. Fetch Personal Notes
  const { data: userNotes = [] } = useQuery({
    queryKey: ["notes", titleId],
    queryFn: () => getUserNotes(titleId),
    enabled: Boolean(titleId),
  });

  // 7. Fetch Personal Reviews
  const { data: userReviews = [] } = useQuery({
    queryKey: ["reviews", titleId],
    queryFn: () => getUserReviews(titleId),
    enabled: Boolean(titleId),
  });

  // ── Mutations ────────────────────────────────────────────────────────────

  const watchlistMutation = useMutation({
    mutationFn: (newStatus: boolean) => toggleWatchlistState(titleId, newStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["userTitleState", titleId] });
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
      queryClient.invalidateQueries({ queryKey: ["personalAnalytics"] });
    },
  });

  const favoriteMutation = useMutation({
    mutationFn: (fav: boolean) => toggleFavoriteState(titleId, fav),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["userTitleState", titleId] });
      queryClient.invalidateQueries({ queryKey: ["personalAnalytics"] });
    },
  });

  const libraryMutation = useMutation({
    mutationFn: async (inLib: boolean) => {
      if (inLib) {
        await addToLibrary(titleId);
      } else {
        await removeFromLibrary(titleId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["library"] });
      queryClient.invalidateQueries({ queryKey: ["personalAnalytics"] });
    },
  });

  const watchEventMutation = useMutation({
    mutationFn: () => logWatchEvent(titleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["history"] });
      queryClient.invalidateQueries({ queryKey: ["personalAnalytics"] });
      queryClient.invalidateQueries({ queryKey: ["userStreak"] });
      queryClient.invalidateQueries({ queryKey: ["userBadges"] });
    },
  });

  const ratingMutation = useMutation({
    mutationFn: (val: number) => setUserRating(titleId, val),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ratings", titleId] });
      queryClient.invalidateQueries({ queryKey: ["personalAnalytics"] });
    },
  });

  const deleteRatingMutation = useMutation({
    mutationFn: () => deleteUserRating(titleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ratings", titleId] });
      queryClient.invalidateQueries({ queryKey: ["personalAnalytics"] });
    },
  });

  const noteMutation = useMutation({
    mutationFn: (text: string) => createUserNote(titleId, text),
    onSuccess: () => {
      setNoteInput("");
      setIsAddingNote(false);
      queryClient.invalidateQueries({ queryKey: ["notes", titleId] });
    },
  });

  const deleteNoteMutation = useMutation({
    mutationFn: (noteId: string) => deleteUserNote(noteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes", titleId] });
    },
  });

  const reviewMutation = useMutation({
    mutationFn: (payload: { title: string; text: string; isPublic: boolean }) =>
      createUserReview(titleId, payload.title, payload.text, payload.isPublic),
    onSuccess: () => {
      setReviewTitle("");
      setReviewText("");
      setIsAddingReview(false);
      queryClient.invalidateQueries({ queryKey: ["reviews", titleId] });
    },
  });

  const deleteReviewMutation = useMutation({
    mutationFn: (reviewId: string) => deleteUserReview(reviewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews", titleId] });
    },
  });

  // Friend recommendations
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

  // Collections
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

  const handleSendRecommendation = (e: React.FormEvent) => {
    e.preventDefault();
    if (!friendId) return;

    recommendMutation.mutate(recommendNote, {
      onSuccess: () => {
        setRecommendSent(true);
        setTimeout(() => {
          setRecommendSent(false);
          setIsRecommendModalOpen(false);
          setFriendId("");
          setRecommendNote("");
        }, 1800);
      },
    });
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <LoadingState message="Loading cinematic details & verified metadata..." />
      </div>
    );
  }

  // Honest 404 View
  if (isError || !title) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-8 space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500">
          <Film className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold text-zinc-100">Title Not Found</h1>
        <p className="text-sm text-zinc-400 max-w-md">
          The movie you requested does not exist in the canonical catalog or could not be found.
        </p>
        <Link
          href="/movies"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold shadow-lg shadow-violet-600/30 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Movies</span>
        </Link>
      </div>
    );
  }

  const displayTitle = title.canonical_title || "Untitled";
  const displayYear = title.production_year;
  const displayCountry = title.origin_country;
  const displaySynopsis = title.synopsis;
  const displayGenres = title.genres && title.genres.length > 0 ? title.genres : [];
  const displayBackdrop = title.backdrop_url || null;
  const displayPoster = title.poster_url || null;

  return (
    <div className="relative -mt-4 sm:-mt-6 lg:-mt-8 -mx-4 sm:-mx-6 lg:-mx-8 min-h-screen bg-zinc-950 text-zinc-50 pb-20">
      {/* Top Floating Back Button */}
      <div className="absolute top-6 left-6 z-30">
        <button
          onClick={() => router.back()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-950/70 backdrop-blur-xl border border-zinc-800 text-xs font-medium text-zinc-300 hover:text-white hover:bg-zinc-900 transition-all shadow-lg cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Catalog</span>
        </button>
      </div>

      {/* TOP 60VH HERO BANNER */}
      <div className="relative w-full h-[60vh] min-h-[460px] overflow-hidden bg-zinc-950">
        {displayBackdrop ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={displayBackdrop}
            alt={displayTitle}
            className="w-full h-full object-cover object-center scale-105 filter brightness-[0.75] contrast-[1.05]"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-zinc-900 via-zinc-950 to-black flex items-center justify-center">
            <Film className="w-16 h-16 text-zinc-800" />
          </div>
        )}

        <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/80 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-zinc-950/90 via-zinc-950/40 to-transparent" />

        <div className="absolute bottom-0 left-0 right-0 max-w-7xl mx-auto px-6 sm:px-10 pb-8 flex flex-col md:flex-row items-end gap-8 z-20">
          {/* Floating Poster */}
          <div className="hidden sm:block shrink-0 w-44 md:w-52 aspect-[2/3] rounded-2xl overflow-hidden bg-zinc-900 shadow-2xl shadow-violet-950/40 ring-1 ring-white/10 group">
            {displayPoster ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={displayPoster} alt={displayTitle} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-zinc-900 to-zinc-950">
                <Film className="w-10 h-10 text-zinc-700" />
              </div>
            )}
          </div>

          {/* Title & Primary Actions */}
          <div className="flex-1 space-y-4">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-zinc-900/80 text-zinc-300 border border-zinc-800 backdrop-blur-md">
                <Film className="w-3.5 h-3.5 text-zinc-400" />
                {title.content_type || "Feature Film"}
              </span>

              {displayCountry && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono text-zinc-400 bg-zinc-900/60 border border-zinc-800">
                  <Globe className="w-3 h-3 text-zinc-500" />
                  {displayCountry}
                </span>
              )}

              {title.tagline && (
                <span className="text-xs text-violet-300 font-medium italic hidden md:inline">
                  &ldquo;{title.tagline}&rdquo;
                </span>
              )}
            </div>

            <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-zinc-50 leading-tight drop-shadow-md">
              {displayTitle}
            </h1>

            {title.original_title && title.original_title !== displayTitle && (
              <p className="text-sm text-zinc-400 font-medium">{title.original_title}</p>
            )}

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
              {title.primary_edition?.runtime_minutes ? (
                <>
                  <span className="flex items-center gap-1.5 text-zinc-300">
                    <Clock className="w-4 h-4 text-zinc-400" />
                    {title.primary_edition.runtime_minutes} mins
                  </span>
                  <span className="text-zinc-600">•</span>
                </>
              ) : null}
              {currentRating && (
                <>
                  <span className="flex items-center gap-1.5 text-amber-400 font-bold">
                    <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                    {currentRating}/10 Rated
                  </span>
                  <span className="text-zinc-600">•</span>
                </>
              )}
              <span className="text-zinc-300">
                {title.primary_edition?.edition_name || "Standard Edition"}
              </span>
            </div>

            {/* Action Buttons Row */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              {/* Recommend */}
              <button
                onClick={() => setIsRecommendModalOpen(true)}
                className="inline-flex items-center gap-2.5 px-6 py-3 text-xs sm:text-sm font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-xl shadow-violet-600/30 transition-all hover:scale-105 active:scale-95 cursor-pointer"
              >
                <Share2 className="w-4 h-4" />
                <span>Recommend</span>
              </button>

              {/* Watchlist */}
              <button
                onClick={() => watchlistMutation.mutate(!isSavedToWatchlist)}
                disabled={watchlistMutation.isPending}
                className={`inline-flex items-center gap-2 px-5 py-3 text-xs sm:text-sm font-medium rounded-full border backdrop-blur-md transition-all cursor-pointer ${
                  isSavedToWatchlist
                    ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                    : "bg-zinc-900/80 hover:bg-zinc-800 border-zinc-800 text-zinc-200"
                }`}
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

              {/* Library */}
              <button
                onClick={() => libraryMutation.mutate(!isAddedToLibrary)}
                disabled={libraryMutation.isPending}
                className={`inline-flex items-center gap-2 px-5 py-3 text-xs sm:text-sm font-medium rounded-full border backdrop-blur-md transition-all cursor-pointer ${
                  isAddedToLibrary
                    ? "bg-violet-500/20 border-violet-500/40 text-violet-300"
                    : "bg-zinc-900/80 hover:bg-zinc-800 border-zinc-800 text-zinc-200"
                }`}
              >
                {isAddedToLibrary ? (
                  <>
                    <Check className="w-4 h-4 text-violet-400" />
                    <span>In Library</span>
                  </>
                ) : (
                  <>
                    <LibraryBig className="w-4 h-4 text-zinc-400" />
                    <span>Add to Library</span>
                  </>
                )}
              </button>

              {/* Favorite */}
              <button
                onClick={() => favoriteMutation.mutate(!isFavorite)}
                disabled={favoriteMutation.isPending}
                title={isFavorite ? "Favorited" : "Add to Favorites"}
                className={`p-3 rounded-full border transition-colors cursor-pointer ${
                  isFavorite
                    ? "bg-amber-500/20 border-amber-500/40 text-amber-400"
                    : "bg-zinc-900/80 hover:bg-zinc-800 border-zinc-800 text-zinc-400 hover:text-amber-400"
                }`}
              >
                <Star className={`w-4 h-4 ${isFavorite ? "fill-amber-400" : ""}`} />
              </button>

              {/* Add to Collection */}
              <button
                onClick={() => setIsCollectionModalOpen(true)}
                title="Add to Collection"
                className="p-3 rounded-full bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-violet-400 transition-colors cursor-pointer"
              >
                <FolderPlus className="w-4 h-4" />
              </button>

              {/* Mark Watched */}
              <button
                onClick={() => watchEventMutation.mutate()}
                disabled={watchEventMutation.isPending}
                title={isMarkedWatched ? "Watched (Click to log rewatch)" : "Mark as Watched"}
                className={`p-3 rounded-full border transition-colors cursor-pointer ${
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

      {/* BODY CONTENT */}
      <div className="max-w-7xl mx-auto px-6 sm:px-10 mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns: Overview, Personal Data, Metadata, Cast & Crew */}
        <div className="lg:col-span-2 space-y-8">
          {/* Genres */}
          {displayGenres.length > 0 && (
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
          )}

          {/* Synopsis */}
          <div className="space-y-3">
            <h2 className="text-lg font-bold text-zinc-100 tracking-tight">Overview & Storyline</h2>
            <p className="text-sm sm:text-base text-zinc-300 leading-relaxed font-normal">
              {displaySynopsis || "No synopsis available for this title yet."}
            </p>
          </div>

          {/* PERSONAL ENTERTAINMENT DATA PANEL (ADR-003) */}
          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-6">
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
              <div className="flex items-center gap-2 text-sm font-bold text-zinc-200">
                <Star className="w-4 h-4 text-amber-400" />
                <span>Personal Data & Journal (ADR-003)</span>
              </div>

              {/* Sub-tabs for Rating, Notes, Reviews */}
              <div className="flex items-center gap-1 bg-zinc-950 p-1 rounded-xl border border-zinc-800/80 text-xs">
                <button
                  onClick={() => setActivePersonalTab("rating")}
                  className={`px-3 py-1 rounded-lg font-medium transition-all ${
                    activePersonalTab === "rating"
                      ? "bg-violet-600/20 text-violet-300 border border-violet-500/30"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  Rating ({currentRating ? `${currentRating}/10` : "None"})
                </button>
                <button
                  onClick={() => setActivePersonalTab("notes")}
                  className={`px-3 py-1 rounded-lg font-medium transition-all ${
                    activePersonalTab === "notes"
                      ? "bg-violet-600/20 text-violet-300 border border-violet-500/30"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  Notes ({userNotes.length})
                </button>
                <button
                  onClick={() => setActivePersonalTab("reviews")}
                  className={`px-3 py-1 rounded-lg font-medium transition-all ${
                    activePersonalTab === "reviews"
                      ? "bg-violet-600/20 text-violet-300 border border-violet-500/30"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  Reviews ({userReviews.length})
                </button>
              </div>
            </div>

            {/* TAB 1: RATINGS */}
            {activePersonalTab === "rating" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-zinc-400">
                    Your personal rating (1-10 score). Isolated from public community rankings.
                  </p>
                  {currentRating && (
                    <button
                      onClick={() => deleteRatingMutation.mutate()}
                      className="text-xs text-rose-400 hover:text-rose-300 inline-flex items-center gap-1 cursor-pointer"
                    >
                      <Trash2 className="w-3 h-3" /> Clear Rating
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-5 sm:grid-cols-10 gap-2">
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((score) => {
                    const isSelected = currentRating === score;
                    return (
                      <button
                        key={score}
                        onClick={() => ratingMutation.mutate(score)}
                        className={`py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                          isSelected
                            ? "bg-amber-500 text-zinc-950 shadow-md shadow-amber-500/30 scale-105"
                            : "bg-zinc-950/80 border border-zinc-800 text-zinc-300 hover:border-amber-500/40 hover:text-amber-300"
                        }`}
                      >
                        {score}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* TAB 2: PRIVATE NOTES */}
            {activePersonalTab === "notes" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-zinc-400">
                    Private personal notes. Visible only to you.
                  </p>
                  {!isAddingNote && (
                    <button
                      onClick={() => setIsAddingNote(true)}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-violet-600/20 text-violet-300 border border-violet-500/30 text-xs font-medium hover:bg-violet-600/30 cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" /> Add Note
                    </button>
                  )}
                </div>

                {isAddingNote && (
                  <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 space-y-3">
                    <textarea
                      rows={3}
                      value={noteInput}
                      onChange={(e) => setNoteInput(e.target.value)}
                      placeholder="Write your private note or observation..."
                      className="w-full text-xs p-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500 resize-none"
                    />
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setIsAddingNote(false)}
                        className="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 cursor-pointer"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => noteInput.trim() && noteMutation.mutate(noteInput.trim())}
                        disabled={noteMutation.isPending || !noteInput.trim()}
                        className="px-4 py-1.5 text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white rounded-lg disabled:opacity-50 cursor-pointer"
                      >
                        {noteMutation.isPending ? "Saving..." : "Save Note"}
                      </button>
                    </div>
                  </div>
                )}

                {userNotes.length === 0 ? (
                  <p className="text-xs text-zinc-500 italic py-2">No private notes added yet.</p>
                ) : (
                  <div className="space-y-2">
                    {userNotes.map((n) => (
                      <div
                        key={n.id}
                        className="p-3 rounded-xl bg-zinc-950/60 border border-zinc-800/80 flex items-start justify-between gap-3"
                      >
                        <div className="space-y-1">
                          <p className="text-xs text-zinc-200">{n.note_text}</p>
                          <p className="text-[10px] text-zinc-500">
                            {new Date(n.updated_at).toLocaleDateString()}
                          </p>
                        </div>
                        <button
                          onClick={() => deleteNoteMutation.mutate(n.id)}
                          className="text-zinc-500 hover:text-rose-400 p-1 cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: REVIEWS */}
            {activePersonalTab === "reviews" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-zinc-400">
                    Your long-form reviews and critique entries.
                  </p>
                  {!isAddingReview && (
                    <button
                      onClick={() => setIsAddingReview(true)}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-violet-600/20 text-violet-300 border border-violet-500/30 text-xs font-medium hover:bg-violet-600/30 cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" /> Write Review
                    </button>
                  )}
                </div>

                {isAddingReview && (
                  <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 space-y-3">
                    <input
                      type="text"
                      placeholder="Review Headline / Summary..."
                      value={reviewTitle}
                      onChange={(e) => setReviewTitle(e.target.value)}
                      className="w-full text-xs p-2.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500"
                    />
                    <textarea
                      rows={4}
                      value={reviewText}
                      onChange={(e) => setReviewText(e.target.value)}
                      placeholder="Detailed critique, themes, cinematography analysis..."
                      className="w-full text-xs p-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500 resize-none"
                    />
                    <div className="flex items-center justify-between pt-1">
                      <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={reviewContainsSpoilers}
                          onChange={(e) => setReviewContainsSpoilers(e.target.checked)}
                          className="rounded border-zinc-700 bg-zinc-900 text-violet-600"
                        />
                        <span>Contains Spoilers</span>
                      </label>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setIsAddingReview(false)}
                          className="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 cursor-pointer"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() =>
                            reviewText.trim() &&
                            reviewMutation.mutate({
                              title: reviewTitle.trim(),
                              text: reviewText.trim(),
                              isPublic: !reviewContainsSpoilers,
                            })
                          }
                          disabled={reviewMutation.isPending || !reviewText.trim()}
                          className="px-4 py-1.5 text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white rounded-lg disabled:opacity-50 cursor-pointer"
                        >
                          {reviewMutation.isPending ? "Publishing..." : "Publish Review"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {userReviews.length === 0 ? (
                  <p className="text-xs text-zinc-500 italic py-2">No reviews written yet.</p>
                ) : (
                  <div className="space-y-3">
                    {userReviews.map((rev) => (
                      <div
                        key={rev.id}
                        className="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80 space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-zinc-100">
                            {rev.review_title || "Review"}
                          </h4>
                          <div className="flex items-center gap-2">
                            {!rev.is_public && (
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                                Spoilers
                              </span>
                            )}
                            <button
                              onClick={() => deleteReviewMutation.mutate(rev.id)}
                              className="text-zinc-500 hover:text-rose-400 p-1 cursor-pointer"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                        <p className="text-xs text-zinc-300 leading-relaxed">{rev.review_text}</p>
                        <p className="text-[10px] text-zinc-500">
                          {new Date(rev.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* CAST & CREW (CREDITS) */}
          {title.credits && title.credits.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-zinc-200">
                <Users className="w-4 h-4 text-violet-400" />
                <span>Cast & Crew</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {title.credits.map((c) => (
                  <div
                    key={c.credit_id}
                    className="p-3 rounded-xl bg-zinc-900/30 border border-zinc-900 space-y-1"
                  >
                    <p className="text-xs font-semibold text-zinc-200 truncate">{c.person_name}</p>
                    <p className="text-[11px] text-zinc-400 truncate">
                      {c.character_name ? `as ${c.character_name}` : c.role_name}
                    </p>
                    <span className="text-[9px] font-mono text-zinc-600 uppercase">
                      {c.role_category}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* EDITIONS & RELEASES */}
          {title.editions && title.editions.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-zinc-200">
                <Layers className="w-4 h-4 text-violet-400" />
                <span>Editions & Physical/Digital Releases</span>
              </div>
              <div className="space-y-2">
                {title.editions.map((ed) => (
                  <div
                    key={ed.id}
                    className="p-4 rounded-xl bg-zinc-900/30 border border-zinc-900 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-zinc-200">
                        {ed.edition_name}{" "}
                        {ed.is_primary && (
                          <span className="text-[10px] text-violet-400 font-normal">
                            (Primary Master)
                          </span>
                        )}
                      </h4>
                      {ed.runtime_minutes && (
                        <span className="text-xs text-zinc-400 font-mono">
                          {ed.runtime_minutes} mins
                        </span>
                      )}
                    </div>
                    {ed.releases && ed.releases.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {ed.releases.map((rel) => (
                          <span
                            key={rel.release_id}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-zinc-950 border border-zinc-800 text-[10px] text-zinc-400"
                          >
                            <span className="font-semibold text-zinc-300">{rel.release_type}</span>
                            {rel.country_code && ` (${rel.country_code})`}
                            {rel.release_date && ` • ${rel.release_date}`}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Canonical Provenance Spec Sheet */}
          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-4">
            <div className="flex items-center gap-2 text-sm font-bold text-zinc-200">
              <Layers className="w-4 h-4 text-violet-400" />
              <span>Technical Specs & Metadata Lineage</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-zinc-500 block mb-1">Catalog ID</span>
                <span className="font-mono text-zinc-300 font-medium">
                  {title.display_id || titleId}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Languages</span>
                <span className="text-zinc-300 font-medium">
                  {title.languages && title.languages.length > 0
                    ? title.languages.join(", ")
                    : "Not recorded"}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Aspect Ratio</span>
                <span className="text-zinc-300 font-medium">
                  {title.primary_edition?.aspect_ratio || "Not recorded"}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Audio Mix</span>
                <span className="text-zinc-300 font-medium">
                  {title.primary_edition?.sound_mix || "Not recorded"}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Color Format</span>
                <span className="text-zinc-300 font-medium">
                  {title.primary_edition?.color_format || "Not recorded"}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block mb-1">Artwork Status</span>
                <span
                  className={
                    title.has_licensed_artwork ? "text-emerald-400 font-medium" : "text-zinc-500"
                  }
                >
                  {title.has_licensed_artwork ? "Licensed Master" : "Default Poster"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Social, External Links, Themes */}
        <div className="space-y-6">
          {/* Peer Recommendation Prompt */}
          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
              <UserCheck className="w-4 h-4 text-violet-400" />
              <span>Peer Recommendation</span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Share your favorites directly with your friends. Zero social noise, direct to OLED inbox.
            </p>
            <button
              onClick={() => setIsRecommendModalOpen(true)}
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-violet-300 bg-violet-600/10 hover:bg-violet-600/20 border border-violet-500/30 transition-all text-center cursor-pointer"
            >
              Recommend to Circle
            </button>
          </div>

          {/* External Databases & Identifiers */}
          {title.external_ids && title.external_ids.length > 0 && (
            <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
                <ExternalLink className="w-4 h-4 text-violet-400" />
                <span>External Registries</span>
              </div>
              <div className="space-y-2">
                {title.external_ids.map((ext) => (
                  <div
                    key={`${ext.provider_name}-${ext.external_id}`}
                    className="flex items-center justify-between text-xs p-2.5 rounded-xl bg-zinc-950 border border-zinc-800"
                  >
                    <span className="font-semibold text-zinc-300">{ext.provider_name}</span>
                    <span className="font-mono text-zinc-500">{ext.external_id}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Themes & Keywords */}
          {((title.themes && title.themes.length > 0) ||
            (title.keywords && title.keywords.length > 0)) && (
            <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-900 space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
                <Eye className="w-4 h-4 text-violet-400" />
                <span>Themes & Motifs</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {title.themes?.map((th) => (
                  <span
                    key={th.theme_id}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-300"
                  >
                    #{th.name}
                  </span>
                ))}
                {title.keywords?.map((kw) => (
                  <span
                    key={kw.keyword_id}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-400"
                  >
                    {kw.name}
                  </span>
                ))}
              </div>
            </div>
          )}
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
            <div className="flex items-center justify-between pb-4 border-b border-zinc-900">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400">
                  <Share2 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-100">Recommend Movie</h3>
                  <p className="text-[11px] text-zinc-400">Send to a friend</p>
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
                  Sent <span className="text-violet-300 font-semibold">{displayTitle}</span> to{" "}
                  <span className="text-zinc-200 font-semibold">
                    {selectedFriend?.friend_name || "your friend"}
                  </span>
                  .
                </p>
              </div>
            ) : (
              <form onSubmit={handleSendRecommendation} className="space-y-4 pt-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-300 mb-1.5">Friend</label>
                  {acceptedFriends.length > 0 ? (
                    <select
                      required
                      value={friendId}
                      onChange={(e) => setFriendId(e.target.value)}
                      className="w-full px-3.5 py-2.5 text-xs bg-zinc-900 border border-zinc-800 rounded-xl text-zinc-100 focus:outline-none focus:border-violet-500 transition-colors"
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
                    placeholder="Why they need to watch this..."
                    value={recommendNote}
                    onChange={(e) => setRecommendNote(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs bg-zinc-900 border border-zinc-800 rounded-xl text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500 transition-colors resize-none"
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
                    className={`inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-xl shadow-lg shadow-violet-600/30 transition-all cursor-pointer ${
                      recommendMutation.isPending || acceptedFriends.length === 0
                        ? "opacity-50 cursor-not-allowed"
                        : ""
                    }`}
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
                <FolderPlus className="w-4 h-4 text-violet-400" />
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
                <Link href="/collections" className="text-violet-400 hover:underline">
                  Create one first
                </Link>
                .
              </p>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {myCollections.map((c) => {
                  const isAdded = addedCollectionIds.includes(c.id);
                  const isThisPending =
                    addToCollectionMutation.isPending &&
                    addToCollectionMutation.variables === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => addToCollectionMutation.mutate(c.id)}
                      disabled={isAdded || isThisPending}
                      className={`w-full flex items-center justify-between gap-3 p-3 rounded-xl border text-left transition-all cursor-pointer disabled:cursor-not-allowed ${
                        isAdded
                          ? "bg-violet-600/10 border-violet-500/30"
                          : "bg-zinc-900/60 border-zinc-800 hover:border-zinc-700"
                      }`}
                    >
                      <div>
                        <p className="text-xs font-bold text-zinc-100">{c.name}</p>
                        <p className="text-[10px] text-zinc-500">{c.item_count} titles</p>
                      </div>
                      {isAdded ? (
                        <Check className="w-4 h-4 text-violet-400 shrink-0" />
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
