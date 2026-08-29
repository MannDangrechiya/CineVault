"use client";

import React, { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
  SlidersHorizontal,
  Users,
  ShieldCheck,
  Clapperboard,
  Film,
  Award,
  Trophy,
  Clock,
  UserPlus,
  Copy,
  CheckCheck,
  Vote,
  Search,
  Plus,
  Eye,
  Star,
} from "lucide-react";
import {
  getRecommendations,
  updateRecommendationStatus,
  toggleWatchlistState,
  getFriendCompatibility,
  getSocialLeaderboard,
  createInviteToken,
  getReferralStats,
  createPickRoom,
  type RecommendationItem,
  type RecommendationStatus,
  type CompatibilityResponse,
  type LeaderboardResponse,
} from "@/lib/api/personal";
import { getFriendships, getTasteMatches, type FriendshipItem } from "@/lib/api/ai";
import { getCatalogPage } from "@/lib/api/titles";
import type { TitleSummary } from "@/lib/api/types";
import { useDebounce } from "@/lib/use-debounce";
import { LoadingState } from "@/components/ui/States";

const FALLBACK_POSTER =
  "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80";

function getTrustTier(trustScore: number) {
  if (trustScore >= 76) return { label: "Oracle", badgeClass: "text-amber-400 bg-amber-500/10 border-amber-500/30", barClass: "bg-amber-400" };
  if (trustScore >= 51) return { label: "Critic", badgeClass: "text-purple-400 bg-purple-500/10 border-purple-500/30", barClass: "bg-purple-400" };
  if (trustScore >= 26) return { label: "Regular", badgeClass: "text-blue-400 bg-blue-500/10 border-blue-500/30", barClass: "bg-blue-400" };
  return { label: "Curious", badgeClass: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30", barClass: "bg-zinc-500" };
}

function CompatibilityModal({
  friend,
  onClose,
}: {
  friend: FriendshipItem;
  onClose: () => void;
}) {
  const { data: compat, isLoading } = useQuery<CompatibilityResponse>({
    queryKey: ["compatibility", friend.friend_id],
    queryFn: () => getFriendCompatibility(friend.friend_id),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-2xl bg-zinc-950 border border-zinc-800 p-6 shadow-2xl space-y-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-zinc-400 hover:text-zinc-100 p-1.5 rounded-lg hover:bg-zinc-900 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shadow-lg text-base font-bold">
            {(friend.friend_name || "?").charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="text-base font-bold text-zinc-100">
              {friend.friend_name || "Community Member"}
            </h3>
            <p className="text-xs text-zinc-400">
              {friend.friend_username ? `@${friend.friend_username}` : "Taste Match Profile"}
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="py-8">
            <LoadingState message="Analyzing neural taste overlap..." />
          </div>
        ) : compat ? (
          <div className="space-y-5">
            {/* Compatibility Hero Score */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-violet-950/40 via-zinc-900/60 to-zinc-900/40 border border-violet-800/30 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-xs uppercase tracking-wider font-semibold text-zinc-400">
                  Head-to-Head Compatibility
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-white">
                    {compat.compatibility_score.toFixed(1)}%
                  </span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-medium border text-violet-300 bg-violet-500/10 border-violet-500/20">
                    {compat.taste_tier} Tier
                  </span>
                </div>
              </div>
              <Sparkles className="w-10 h-10 text-violet-400/60" />
            </div>

            {/* Shared Top Genres */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Clapperboard className="w-3.5 h-3.5 text-violet-400" />
                Shared Top Genres
              </span>
              <div className="flex flex-wrap gap-1.5">
                {compat.shared_genres.length > 0 ? (
                  compat.shared_genres.map((genre) => (
                    <span
                      key={genre}
                      className="text-xs px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-200 font-medium"
                    >
                      {genre}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-zinc-500 italic">No common genres watched yet</span>
                )}
              </div>
            </div>

            {/* Shared Directors */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Film className="w-3.5 h-3.5 text-indigo-400" />
                Shared Directors
              </span>
              <div className="flex flex-wrap gap-1.5">
                {compat.shared_directors.length > 0 ? (
                  compat.shared_directors.map((dir) => (
                    <span
                      key={dir}
                      className="text-xs px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-200 font-medium"
                    >
                      {dir}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-zinc-500 italic">No common directors in watch history</span>
                )}
              </div>
            </div>

            {/* Mutually Loved Titles */}
            {compat.shared_favorite_titles.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-amber-400" />
                  Mutually Loved Titles
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {compat.shared_favorite_titles.map((title) => (
                    <span
                      key={title}
                      className="text-xs px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 font-medium"
                    >
                      {title}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-zinc-500 text-center py-4">Unable to compute compatibility profile.</p>
        )}
      </div>
    </div>
  );
}

function InviteFriendsModal({ onClose }: { onClose: () => void }) {
  const [copied, setCopied] = useState(false);
  const { data: invite, isLoading } = useQuery({
    queryKey: ["myInviteToken"],
    queryFn: () => createInviteToken(),
  });

  const { data: stats } = useQuery({
    queryKey: ["referralStats"],
    queryFn: () => getReferralStats(),
  });

  const copyToClipboard = () => {
    if (!invite?.token) return;
    const url = typeof window !== "undefined"
      ? `${window.location.origin}/invite/${invite.token}`
      : invite.invite_url;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-3xl bg-zinc-950 border border-violet-500/30 p-6 shadow-2xl space-y-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-zinc-400 hover:text-zinc-100 p-1.5 rounded-lg hover:bg-zinc-900 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-violet-600/30">
            ✉️
          </div>
          <div>
            <h3 className="text-base font-bold text-zinc-100">
              Invite Cinephile Friends
            </h3>
            <p className="text-xs text-zinc-400">
              Share your personal taste preview link & unlock referral badges
            </p>
          </div>
        </div>

        {/* Link box */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-zinc-300">
            Your Shareable Invite Link
          </label>
          <div className="flex items-center gap-2 p-2 rounded-xl bg-zinc-900 border border-zinc-800">
            <input
              type="text"
              readOnly
              value={
                invite
                  ? typeof window !== "undefined"
                    ? `${window.location.origin}/invite/${invite.token}`
                    : invite.invite_url
                  : "Generating token..."
              }
              className="flex-1 bg-transparent text-xs text-zinc-300 outline-none truncate font-mono px-2"
            />
            <button
              onClick={copyToClipboard}
              disabled={isLoading || !invite}
              className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white flex items-center gap-1.5 transition-all cursor-pointer shrink-0 disabled:opacity-50"
            >
              {copied ? (
                <>
                  <CheckCheck className="w-3.5 h-3.5" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Snapshot Summary */}
        {invite && (
          <div className="p-4 rounded-2xl bg-zinc-900/40 border border-zinc-800/60 space-y-2 text-xs">
            <span className="font-semibold text-zinc-300">Baked Taste Preview</span>
            <div className="flex flex-wrap gap-1.5">
              {(invite.preview_data.top_genres || []).map((g) => (
                <span
                  key={g}
                  className="px-2 py-0.5 rounded text-[10px] bg-violet-500/10 text-violet-300 border border-violet-500/20"
                >
                  {g}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Referral Milestone Stats */}
        {stats && (
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-zinc-900 text-center">
            <div className="p-2.5 rounded-xl bg-zinc-900/30">
              <span className="text-[10px] text-zinc-400 block">Invites Sent</span>
              <span className="text-sm font-bold text-zinc-100">{stats.total_invites_sent}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-zinc-900/30">
              <span className="text-[10px] text-zinc-400 block">Joined</span>
              <span className="text-sm font-bold text-violet-400">{stats.total_conversions}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-zinc-900/30">
              <span className="text-[10px] text-zinc-400 block">Milestones</span>
              <span className="text-sm font-bold text-amber-400">{stats.qualified_referrals}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function CreatePickRoomModal({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const [title, setTitle] = useState("Movie Night Ballot");
  const [expiresInHours, setExpiresInHours] = useState(48);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<TitleSummary[]>([]);
  const debouncedQuery = useDebounce(query, 400);

  const { data: searchResults, isFetching: isSearching } = useQuery({
    queryKey: ["pickRoomTitleSearch", debouncedQuery],
    queryFn: () => getCatalogPage({ query: debouncedQuery, limit: 8 }),
    enabled: debouncedQuery.trim().length >= 2,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createPickRoom({
        title: title.trim() || "Movie Night Ballot",
        candidate_title_ids: selected.map((t) => t.id),
        expires_in_hours: expiresInHours,
      }),
    onSuccess: (room) => {
      onClose();
      router.push(`/pick/${room.slug}`);
    },
  });

  const toggleCandidate = (t: TitleSummary) => {
    setSelected((prev) =>
      prev.some((c) => c.id === t.id)
        ? prev.filter((c) => c.id !== t.id)
        : prev.length >= 12
        ? prev
        : [...prev, t]
    );
  };

  const canSubmit = title.trim().length > 0 && selected.length >= 2 && selected.length <= 12;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-3xl bg-zinc-950 border border-violet-500/30 p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-zinc-400 hover:text-zinc-100 p-1.5 rounded-lg hover:bg-zinc-900 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white text-xl shadow-lg shadow-violet-600/30">
            🗳️
          </div>
          <div>
            <h3 className="text-base font-bold text-zinc-100">Create Pick Room</h3>
            <p className="text-xs text-zinc-400">
              Nominate 2–12 titles and let your party vote on movie night
            </p>
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-zinc-300">Ballot Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Friday Movie Night"
            className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-zinc-300">Voting Window (Hours)</label>
          <input
            type="number"
            min={1}
            max={168}
            value={expiresInHours}
            onChange={(e) => setExpiresInHours(Number(e.target.value))}
            className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 focus:outline-none focus:border-violet-500"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-zinc-300">
            Nominate Titles ({selected.length}/12, min 2)
          </label>
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search the catalog..."
              className="w-full pl-9 pr-3.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500"
            />
          </div>

          {debouncedQuery.trim().length >= 2 && (
            <div className="max-h-40 overflow-y-auto rounded-xl border border-zinc-800/80 divide-y divide-zinc-900">
              {isSearching ? (
                <div className="p-3 text-xs text-zinc-500 text-center">Searching...</div>
              ) : searchResults && searchResults.items.length > 0 ? (
                searchResults.items.map((t) => {
                  const isSelected = selected.some((c) => c.id === t.id);
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => toggleCandidate(t)}
                      disabled={!isSelected && selected.length >= 12}
                      className={`w-full flex items-center justify-between gap-2 px-3 py-2 text-left text-xs transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
                        isSelected ? "bg-violet-600/20 text-violet-200" : "hover:bg-zinc-900 text-zinc-200"
                      }`}
                    >
                      <span className="truncate">
                        {t.canonical_title}
                        {t.production_year ? ` (${t.production_year})` : ""}
                      </span>
                      {isSelected ? <Check className="w-3.5 h-3.5 shrink-0" /> : <Plus className="w-3.5 h-3.5 shrink-0 text-zinc-500" />}
                    </button>
                  );
                })
              ) : (
                <div className="p-3 text-xs text-zinc-500 text-center">No matches found</div>
              )}
            </div>
          )}

          {selected.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {selected.map((t) => (
                <span
                  key={t.id}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] bg-violet-500/10 text-violet-300 border border-violet-500/20"
                >
                  {t.canonical_title}
                  <button
                    type="button"
                    onClick={() => toggleCandidate(t)}
                    className="hover:text-violet-100 cursor-pointer"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {createMutation.isError && (
          <p className="text-xs text-rose-400">
            Couldn&apos;t create the pick room. Check your selections and try again.
          </p>
        )}

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-900">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-zinc-200"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => createMutation.mutate()}
            disabled={!canSubmit || createMutation.isPending}
            className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 transition-all shadow-lg shadow-violet-600/30 disabled:opacity-50 cursor-pointer"
          >
            {createMutation.isPending ? "Creating..." : "Create & Share Ballot"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SocialRecommendationsPage() {
  const [activeTab, setActiveTab] = useState<"inbox" | "ai" | "sent" | "leaderboard">("inbox");
  const [filterScore, setFilterScore] = useState<number>(0);
  const [leaderboardPeriod, setLeaderboardPeriod] = useState<"weekly" | "monthly" | "all_time">("weekly");
  const [selectedFriendForCompat, setSelectedFriendForCompat] = useState<FriendshipItem | null>(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showPickRoomModal, setShowPickRoomModal] = useState(false);
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

  const { data: leaderboard, isLoading: isLoadingLeaderboard } = useQuery<LeaderboardResponse>({
    queryKey: ["social-leaderboard", leaderboardPeriod],
    queryFn: () => getSocialLeaderboard(leaderboardPeriod),
  });

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
    mutationFn: ({
      id,
      status,
      rating,
    }: {
      id: string;
      status: RecommendationStatus;
      titleId: string;
      rating?: number;
    }) => updateRecommendationStatus(id, status, rating),
    onSuccess: async (_result, variables) => {
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

  const handleAction = (rec: RecommendationItem, newStatus: RecommendationStatus, rating?: number) => {
    updateStatusMutation.mutate({ id: rec.recommendation_id, status: newStatus, titleId: rec.title_id, rating });
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
  // Ranked shelf: show only the top 10 matches for a clean, uncluttered grid.
  const friendMatches = acceptedFriends
    .map((f) => ({ friend: f, score: tasteMatchMap.get(f.friend_id) }))
    .sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
    .slice(0, 10);

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
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPickRoomModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-amber-600 hover:bg-amber-500 shadow-md shadow-amber-600/30 transition-all cursor-pointer"
          >
            <Vote className="w-3.5 h-3.5" />
            <span>Create Pick Room</span>
          </button>
          <button
            onClick={() => setShowInviteModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 shadow-md shadow-violet-600/30 transition-all cursor-pointer"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Invite Friends</span>
          </button>
          <Link
            href="/friends"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-zinc-200 hover:text-white bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 transition-all shadow-sm"
          >
            <Users className="w-3.5 h-3.5 text-violet-400" />
            <span>Manage ({acceptedFriends.length})</span>
          </Link>
        </div>
      }
    >
      {showInviteModal && (
        <InviteFriendsModal onClose={() => setShowInviteModal(false)} />
      )}

      {showPickRoomModal && (
        <CreatePickRoomModal onClose={() => setShowPickRoomModal(false)} />
      )}

      {selectedFriendForCompat && (
        <CompatibilityModal
          friend={selectedFriendForCompat}
          onClose={() => setSelectedFriendForCompat(null)}
        />
      )}

      <div className="space-y-6">
        {/* Navigation Tabs */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-zinc-800/80 pb-4">
          <div className="flex items-center gap-2 p-1 bg-zinc-900/80 border border-zinc-800 rounded-2xl w-full sm:w-auto">
            <button
              onClick={() => setActiveTab("inbox")}
              className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "inbox"
                  ? "bg-violet-600 text-white shadow-md shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
              }`}
            >
              <Inbox className="w-3.5 h-3.5" />
              <span>Inbox</span>
              {pendingCount > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-violet-400/20 text-violet-200 border border-violet-300/30">
                  {pendingCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("sent")}
              className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "sent"
                  ? "bg-violet-600 text-white shadow-md shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
              }`}
            >
              <Send className="w-3.5 h-3.5" />
              <span>Sent</span>
              {sent.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-zinc-700/50 text-zinc-300">
                  {sent.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("ai")}
              className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "ai"
                  ? "bg-violet-600 text-white shadow-md shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-violet-300" />
              <span>AI Taste Matches</span>
              {friendMatches.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-violet-400/20 text-violet-200 border border-violet-300/30">
                  {friendMatches.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("leaderboard")}
              className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "leaderboard"
                  ? "bg-violet-600 text-white shadow-md shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
              }`}
            >
              <Trophy className="w-3.5 h-3.5 text-amber-400" />
              <span>Leaderboard</span>
              {leaderboard && leaderboard.entries.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-amber-400/20 text-amber-200 border border-amber-300/30">
                  {leaderboard.entries.length}
                </span>
              )}
            </button>
          </div>

          {/* Optional Filter by Score Slider (Inbox & Sent only) */}
          {(activeTab === "inbox" || activeTab === "sent") && (
            <div className="flex items-center gap-3 w-full sm:w-auto bg-zinc-900/40 px-3 py-1.5 rounded-xl border border-zinc-800/60">
              <SlidersHorizontal className="w-3.5 h-3.5 text-zinc-400" />
              <span className="text-xs text-zinc-400 whitespace-nowrap">
                Min Match: <strong className="text-zinc-200">{filterScore}%</strong>
              </span>
              <input
                type="range"
                min="0"
                max="95"
                step="5"
                value={filterScore}
                onChange={(e) => setFilterScore(Number(e.target.value))}
                className="w-24 accent-violet-500 cursor-pointer h-1.5 bg-zinc-800 rounded-lg"
              />
            </div>
          )}
        </div>

        {/* Tab Content */}
        {activeTab === "leaderboard" ? (
          <div className="space-y-4">
            {/* Period Switcher */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3 rounded-2xl bg-zinc-900/50 border border-zinc-800">
              <div className="flex items-center gap-2">
                <Trophy className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-bold text-zinc-200">Viewing Activity Ranking</span>
              </div>
              <div className="flex items-center gap-1 bg-zinc-950 p-1 rounded-xl border border-zinc-800">
                {(["weekly", "monthly", "all_time"] as const).map((p) => (
                  <button
                    key={p}
                    onClick={() => setLeaderboardPeriod(p)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      leaderboardPeriod === p
                        ? "bg-violet-600 text-white shadow-sm"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                    }`}
                  >
                    {p === "weekly" ? "This Week" : p === "monthly" ? "This Month" : "All Time"}
                  </button>
                ))}
              </div>
            </div>

            {isLoadingLeaderboard ? (
              <div className="py-12">
                <LoadingState message="Ranking circle viewing activity..." />
              </div>
            ) : !leaderboard || leaderboard.entries.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-zinc-900/40 border border-zinc-900 text-zinc-400 space-y-3">
                <Trophy className="w-8 h-8 text-zinc-600 mx-auto" />
                <h3 className="text-sm font-semibold text-zinc-200">No Activity Recorded</h3>
                <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                  Watch movies and log watch events to climb the circle leaderboard!
                </p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {/* Top 10 ranked shelf -- the tab badge above still shows the true total. */}
                {leaderboard.entries.slice(0, 10).map((entry) => {
                  const isTop1 = entry.rank === 1;
                  const isTop2 = entry.rank === 2;
                  const isTop3 = entry.rank === 3;
                  const rankBadge = isTop1
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : isTop2
                    ? "bg-slate-300/20 text-slate-200 border-slate-300/40"
                    : isTop3
                    ? "bg-amber-700/20 text-amber-600 border-amber-700/40"
                    : "bg-zinc-800 text-zinc-400 border-zinc-700";

                  return (
                    <div
                      key={entry.user_id}
                      className={`p-4 rounded-2xl border transition-all flex items-center justify-between gap-4 ${
                        entry.is_current_user
                          ? "bg-violet-950/20 border-violet-500/40 shadow-lg shadow-violet-950/30"
                          : "bg-zinc-900/40 border-zinc-800/80 hover:border-zinc-700"
                      }`}
                    >
                      {/* Rank & User Info */}
                      <div className="flex items-center gap-4 min-w-0">
                        <div
                          className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-extrabold border shrink-0 ${rankBadge}`}
                        >
                          #{entry.rank}
                        </div>

                        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shadow-md text-xs font-bold shrink-0">
                          {(entry.name || "?").charAt(0).toUpperCase()}
                        </div>

                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-zinc-100 truncate">
                              {entry.name || "Community Member"}
                            </span>
                            {entry.is_current_user && (
                              <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-violet-500/20 text-violet-300 border border-violet-500/30">
                                You
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] text-zinc-500">
                            {entry.username ? `@${entry.username}` : "Member"}
                          </span>
                        </div>
                      </div>

                      {/* Viewing Metrics */}
                      <div className="flex items-center gap-4 shrink-0 text-right">
                        <div>
                          <div className="text-sm font-extrabold text-zinc-100 flex items-center justify-end gap-1">
                            <Film className="w-3.5 h-3.5 text-violet-400" />
                            <span>{entry.watch_count}</span>
                          </div>
                          <span className="text-[10px] text-zinc-500">
                            {entry.watch_count === 1 ? "title" : "titles"}
                          </span>
                        </div>

                        <div className="border-l border-zinc-800 pl-4">
                          <div className="text-sm font-extrabold text-zinc-100 flex items-center justify-end gap-1">
                            <Clock className="w-3.5 h-3.5 text-emerald-400" />
                            <span>{entry.watch_hours.toFixed(1)}h</span>
                          </div>
                          <span className="text-[10px] text-zinc-500">viewing</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : activeTab === "ai" ? (
          friendMatches.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-zinc-900/40 border border-zinc-900 text-zinc-400 space-y-3">
              <Users className="w-8 h-8 text-zinc-600 mx-auto" />
              <h3 className="text-sm font-semibold text-zinc-200">No Friends Connected Yet</h3>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                Add friends to CineVault to see your vector-based taste compatibility scores here.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {friendMatches.map(({ friend, score }) => {
                const tier = getTrustTier(friend.trust_score ?? 50);
                return (
                  <div
                    key={friend.friend_id}
                    onClick={() => setSelectedFriendForCompat(friend)}
                    className="group p-4 rounded-2xl border border-zinc-800/80 bg-zinc-900/40 backdrop-blur-md hover:border-violet-600/50 hover:bg-zinc-900/70 transition-all duration-300 flex flex-col justify-between gap-3 cursor-pointer shadow-sm hover:shadow-lg hover:shadow-violet-950/20"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shadow-md text-xs font-bold shrink-0">
                        {(friend.friend_name || "?").charAt(0).toUpperCase()}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-bold text-zinc-100 truncate group-hover:text-violet-300 transition-colors">
                          {friend.friend_name || "Unknown Member"}
                        </p>
                        <p className="text-[10px] text-zinc-500">
                          {friend.friend_username ? `@${friend.friend_username}` : "Member"}
                        </p>
                      </div>
                      {score !== undefined ? (
                        <div className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full text-[11px] font-semibold shrink-0">
                          <Sparkles className="w-3 h-3" />
                          {score.toFixed(1)}%
                        </div>
                      ) : (
                        <span className="text-[10px] text-zinc-600 shrink-0">No vector</span>
                      )}
                    </div>

                    {/* Trust Tier & Progress Display */}
                    <div className="pt-2 border-t border-zinc-800/60 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-zinc-400" />
                        <span className="text-[10px] text-zinc-400">Trust:</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${tier.badgeClass}`}>
                          {tier.label}
                        </span>
                      </div>
                      <span className="text-[10px] text-violet-400 font-medium group-hover:underline">
                        Compare Taste →
                      </span>
                    </div>
                  </div>
                );
              })}
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

                  {/* ACTION BUTTONS -- state machine: SENT -> ACCEPTED -> WATCHED -> RATED.
                      Only the recipient (inbox tab) drives transitions; sent-tab items are read-only. */}
                  <div className="flex items-center justify-between pt-1">
                    {rec.status === "REJECTED" ? (
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <X className="w-4 h-4" />
                        <span>Recommendation Dismissed</span>
                      </div>
                    ) : rec.status === "RATED" ? (
                      <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
                        <Star className="w-4 h-4 fill-amber-400" />
                        <span>
                          {isSent
                            ? `Rated ${rec.recipient_actual_rating ?? "?"}/10 by ${otherPartyName || "your friend"}`
                            : `You Rated It ${rec.recipient_actual_rating ?? "?"}/10`}
                        </span>
                      </div>
                    ) : rec.status === "WATCHED" && isSent ? (
                      <div className="flex items-center gap-2 text-xs text-zinc-400">
                        <Eye className="w-4 h-4" />
                        <span>{otherPartyName || "Your friend"} watched it</span>
                      </div>
                    ) : rec.status === "WATCHED" ? (
                      <div className="w-full space-y-2">
                        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                          <Eye className="w-4 h-4" />
                          <span>Watched — Rate It</span>
                        </div>
                        <div className="flex flex-wrap items-center gap-1">
                          {Array.from({ length: 10 }, (_, i) => i + 1).map((value) => (
                            <button
                              key={value}
                              onClick={() => handleAction(rec, "RATED", value)}
                              disabled={updateStatusMutation.isPending}
                              title={`Rate ${value}/10`}
                              className="w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold text-zinc-400 bg-zinc-900/80 hover:bg-amber-500/20 hover:text-amber-300 border border-zinc-800 hover:border-amber-500/40 transition-all cursor-pointer"
                            >
                              {value}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : rec.status === "ACCEPTED" && isSent ? (
                      <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                        <Check className="w-4 h-4" />
                        <span>Accepted</span>
                      </div>
                    ) : rec.status === "ACCEPTED" ? (
                      <div className="w-full flex items-center justify-between gap-2.5">
                        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                          <Check className="w-4 h-4" />
                          <span>Accepted & Watchlisted</span>
                        </div>
                        <button
                          onClick={() => handleAction(rec, "WATCHED")}
                          disabled={updateStatusMutation.isPending}
                          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 border border-violet-500 shadow-md shadow-violet-600/30 transition-all hover:scale-105 active:scale-95 cursor-pointer"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Mark as Watched</span>
                        </button>
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
