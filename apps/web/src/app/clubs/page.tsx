"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import { LoadingState } from "@/components/ui/States";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import {
  Users,
  Trophy,
  Plus,
  Compass,
  Activity,
  Dna,
  ShieldCheck,
  Clapperboard,
  X,
  ArrowRight,
  Share2,
  CheckCheck,
} from "lucide-react";
import {
  listMyClubs,
  getWatchClub,
  createWatchClub,
  joinWatchClub,
  getClubFeed,
  listActiveChallenges,
  joinChallenge,
  updateChallengeProgress,
  createChallenge,
  type WatchClubResponse,
  type ClubDetailResponse,
  type ClubActivityResponse,
  type ChallengeResponse,
  type WatchClubCreate,
  type ChallengeCreate,
} from "@/lib/api/personal";

export default function WatchClubsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"clubs" | "challenges">("clubs");
  const [selectedClubSlug, setSelectedClubSlug] = useState<string | null>(null);
  const [copiedClubLink, setCopiedClubLink] = useState(false);

  // Modal States
  const [isCreateClubOpen, setIsCreateClubOpen] = useState(false);
  const [isCreateChallengeOpen, setIsCreateChallengeOpen] = useState(false);
  const createClubModalRef = React.useRef<HTMLDivElement>(null);
  const createChallengeModalRef = React.useRef<HTMLDivElement>(null);

  useFocusTrap(isCreateClubOpen, () => setIsCreateClubOpen(false), createClubModalRef);
  useFocusTrap(isCreateChallengeOpen, () => setIsCreateChallengeOpen(false), createChallengeModalRef);

  // Form States for Create Club
  const [clubName, setClubName] = useState("");
  const [clubDescription, setClubDescription] = useState("");
  const [clubAvatarUrl, setClubAvatarUrl] = useState("");

  // Form States for Create Challenge
  const [challengeTitle, setChallengeTitle] = useState("");
  const [challengeDescription, setChallengeDescription] = useState("");
  const [challengeType, setChallengeType] = useState("GENRE_COUNT");
  const [challengeGoal, setChallengeGoal] = useState(5);
  const [challengeDays, setChallengeDays] = useState(30);

  // ── Queries ─────────────────────────────────────────────────────────────────
  const { data: clubs = [], isLoading: isLoadingClubs } = useQuery<WatchClubResponse[]>({
    queryKey: ["watch-clubs"],
    queryFn: listMyClubs,
  });

  const { data: selectedClub, isLoading: isLoadingClubDetail } = useQuery<ClubDetailResponse | null>({
    queryKey: ["watch-club-detail", selectedClubSlug],
    queryFn: () => (selectedClubSlug ? getWatchClub(selectedClubSlug) : Promise.resolve(null)),
    enabled: Boolean(selectedClubSlug),
  });

  const { data: clubFeed = [], isLoading: isLoadingClubFeed } = useQuery<ClubActivityResponse[]>({
    queryKey: ["watch-club-feed", selectedClubSlug],
    queryFn: () => (selectedClubSlug ? getClubFeed(selectedClubSlug, 20) : Promise.resolve([])),
    enabled: Boolean(selectedClubSlug),
  });

  const { data: challenges = [], isLoading: isLoadingChallenges } = useQuery<ChallengeResponse[]>({
    queryKey: ["challenges"],
    queryFn: listActiveChallenges,
  });

  // ── Mutations ───────────────────────────────────────────────────────────────
  const createClubMutation = useMutation({
    mutationFn: (data: WatchClubCreate) => createWatchClub(data),
    onSuccess: (newClub) => {
      queryClient.invalidateQueries({ queryKey: ["watch-clubs"] });
      setIsCreateClubOpen(false);
      setClubName("");
      setClubDescription("");
      setClubAvatarUrl("");
      setSelectedClubSlug(newClub.slug);
    },
  });

  const joinClubMutation = useMutation({
    mutationFn: (slug: string) => joinWatchClub(slug),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watch-clubs"] });
      queryClient.invalidateQueries({ queryKey: ["watch-club-detail", selectedClubSlug] });
    },
  });

  const createChallengeMutation = useMutation({
    mutationFn: (data: ChallengeCreate) => createChallenge(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["challenges"] });
      setIsCreateChallengeOpen(false);
      setChallengeTitle("");
      setChallengeDescription("");
      setChallengeGoal(5);
    },
  });

  const joinChallengeMutation = useMutation({
    mutationFn: (challengeId: string) => joinChallenge(challengeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["challenges"] });
    },
  });

  const progressChallengeMutation = useMutation({
    mutationFn: ({ challengeId, increment }: { challengeId: string; increment: number }) =>
      updateChallengeProgress(challengeId, increment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["challenges"] });
    },
  });

  // Handlers
  const handleCreateClubSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!clubName.trim()) return;
    createClubMutation.mutate({
      name: clubName.trim(),
      description: clubDescription.trim() || undefined,
      avatar_url: clubAvatarUrl.trim() || undefined,
    });
  };

  const handleCreateChallengeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!challengeTitle.trim()) return;
    const now = new Date();
    const endsAt = new Date(now.getTime() + challengeDays * 24 * 60 * 60 * 1000);

    // The "Challenge Type" dropdown (challengeType state) picks a scoring
    // metric — Genre Exploration, Director Retrospective, etc. — which the
    // backend expects under criteria_json, not challenge_type. challenge_type
    // is a different field entirely: it's the challenge's *scope*, GLOBAL
    // (personal, any user can join) or CLUB (tied to the currently open club).
    createChallengeMutation.mutate({
      title: challengeTitle.trim(),
      description: challengeDescription.trim() || undefined,
      challenge_type: selectedClubSlug && selectedClub ? "CLUB" : "GLOBAL",
      criteria_json: { metric: challengeType },
      goal_count: Number(challengeGoal) || 5,
      starts_at: now.toISOString(),
      ends_at: endsAt.toISOString(),
      club_id: selectedClubSlug && selectedClub ? selectedClub.club.club_id : undefined,
    });
  };

  return (
    <PageContainer
      title="Watch Clubs & Cinema Challenges"
      subtitle="Assemble film collectives, fuse community Taste DNA, and complete collaborative viewing milestones"
    >
      <div className="space-y-8">
        {/* Navigation & Action Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-3xl bg-zinc-900/40 border border-zinc-900 backdrop-blur-md">
          {/* Tabs */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setActiveTab("clubs");
                setSelectedClubSlug(null);
              }}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === "clubs" && !selectedClubSlug
                  ? "bg-violet-600 text-white shadow-lg shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60"
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Watch Clubs ({clubs.length})</span>
            </button>

            <button
              onClick={() => {
                setActiveTab("challenges");
                setSelectedClubSlug(null);
              }}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === "challenges"
                  ? "bg-violet-600 text-white shadow-lg shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60"
              }`}
            >
              <Trophy className="w-3.5 h-3.5" />
              <span>Monthly Challenges ({challenges.length})</span>
            </button>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {activeTab === "clubs" ? (
              <button
                onClick={() => setIsCreateClubOpen(true)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 transition-all flex items-center gap-1.5 shadow-lg shadow-violet-600/30 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Watch Club</span>
              </button>
            ) : (
              <button
                onClick={() => setIsCreateChallengeOpen(true)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-amber-600 hover:bg-amber-500 transition-all flex items-center gap-1.5 shadow-lg shadow-amber-600/30 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Launch Challenge</span>
              </button>
            )}
          </div>
        </div>

        {/* ── TAB 1: WATCH CLUBS ───────────────────────────────────────────── */}
        {activeTab === "clubs" && !selectedClubSlug && (
          <div className="space-y-6">
            {isLoadingClubs ? (
              <div className="py-12">
                <LoadingState message="Discovering CineVault Watch Clubs..." />
              </div>
            ) : clubs.length === 0 ? (
              <div className="text-center py-16 p-8 rounded-3xl bg-zinc-900/30 border border-zinc-900 space-y-4">
                <div className="w-16 h-16 rounded-3xl bg-violet-600/10 text-violet-400 flex items-center justify-center mx-auto border border-violet-500/20">
                  <Compass className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-base font-bold text-zinc-100">No Watch Clubs Yet</h3>
                  <p className="text-xs text-zinc-400 max-w-md mx-auto">
                    Start a film society with your inner circle. Watch clubs aggregate joint Taste DNA, curate shared queues, and track collective film achievements.
                  </p>
                </div>
                <button
                  onClick={() => setIsCreateClubOpen(true)}
                  className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 transition-all shadow-lg shadow-violet-600/30 cursor-pointer inline-flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create Your First Watch Club</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {clubs.map((club) => (
                  <div
                    key={club.club_id}
                    onClick={() => setSelectedClubSlug(club.slug)}
                    className="p-5 rounded-3xl bg-zinc-900/40 border border-zinc-850 hover:border-violet-500/40 transition-all cursor-pointer group flex flex-col justify-between space-y-4 hover:shadow-xl hover:shadow-violet-950/20"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white text-lg font-bold shadow-md shadow-violet-600/20 shrink-0 overflow-hidden">
                            {club.avatar_url ? (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img src={club.avatar_url} alt={club.name} className="w-full h-full object-cover" />
                            ) : (
                              club.name.charAt(0).toUpperCase()
                            )}
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-zinc-100 group-hover:text-violet-300 transition-colors">
                              {club.name}
                            </h4>
                            <p className="text-[10px] text-zinc-500 font-mono">@{club.slug}</p>
                          </div>
                        </div>

                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-violet-500/10 text-violet-400 border border-violet-500/20 shrink-0">
                          {club.member_count} {club.member_count === 1 ? "member" : "members"}
                        </span>
                      </div>

                      <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">
                        {club.description || "A dedicated cinematic collective curating and exploring essential cinema."}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-zinc-900 flex items-center justify-between text-xs text-zinc-500">
                      <div className="flex items-center gap-1 text-[11px]">
                        <ShieldCheck className="w-3 h-3 text-violet-400" />
                        <span>Curated by {club.creator_name || "CineVault Member"}</span>
                      </div>

                      <span className="text-violet-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-1 font-semibold text-[11px]">
                        Explore <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── SELECTED CLUB DETAIL VIEW ────────────────────────────────────── */}
        {activeTab === "clubs" && selectedClubSlug && (
          <div className="space-y-6">
            {/* Back to Clubs button */}
            <button
              onClick={() => setSelectedClubSlug(null)}
              className="text-xs font-semibold text-zinc-400 hover:text-zinc-100 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <span>← Back to All Watch Clubs</span>
            </button>

            {isLoadingClubDetail ? (
              <div className="py-12">
                <LoadingState message="Loading club taste DNA & live feed..." />
              </div>
            ) : selectedClub ? (
              <div className="space-y-6">
                {/* Hero Club Banner */}
                <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-violet-950/40 via-zinc-900/60 to-zinc-900/30 border border-violet-800/30 space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white text-2xl font-bold shadow-xl shadow-violet-600/30 overflow-hidden">
                        {selectedClub.club.avatar_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={selectedClub.club.avatar_url}
                            alt={selectedClub.club.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          selectedClub.club.name.charAt(0).toUpperCase()
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h2 className="text-xl font-bold text-zinc-100">{selectedClub.club.name}</h2>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-violet-500/20 text-violet-300 border border-violet-500/30">
                            Watch Club
                          </span>
                        </div>
                        <p className="text-xs text-zinc-400 mt-1">
                          Curated by <span className="text-zinc-200 font-semibold">{selectedClub.club.creator_name || "Founder"}</span> • {selectedClub.club.member_count} active members
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          if (typeof window !== "undefined") {
                            navigator.clipboard.writeText(
                              `${window.location.origin}/clubs/${selectedClub.club.slug}`
                            );
                            setCopiedClubLink(true);
                            setTimeout(() => setCopiedClubLink(false), 2500);
                          }
                        }}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 transition-all cursor-pointer shadow-sm"
                      >
                        {copiedClubLink ? (
                          <>
                            <CheckCheck className="w-3.5 h-3.5 text-emerald-400" />
                            <span>Link Copied!</span>
                          </>
                        ) : (
                          <>
                            <Share2 className="w-3.5 h-3.5 text-violet-400" />
                            <span>Share Club</span>
                          </>
                        )}
                      </button>

                      <button
                        onClick={() => joinClubMutation.mutate(selectedClub.club.slug)}
                        disabled={joinClubMutation.isPending}
                        className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 transition-all shadow-lg shadow-violet-600/30 flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                      >
                        <Users className="w-3.5 h-3.5" />
                        <span>{joinClubMutation.isPending ? "Joining..." : "Join Watch Club"}</span>
                      </button>
                    </div>
                  </div>

                  {selectedClub.club.description && (
                    <p className="text-xs text-zinc-300 leading-relaxed max-w-3xl">
                      {selectedClub.club.description}
                    </p>
                  )}
                </div>

                {/* Grid: Taste DNA + Live Feed */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left Column: Taste DNA & Members */}
                  <div className="space-y-6 lg:col-span-1">
                    {/* Taste DNA Panel */}
                    <div className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-4">
                      <div className="flex items-center gap-2 pb-2 border-b border-zinc-900">
                        <Dna className="w-4 h-4 text-violet-400" />
                        <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">
                          Collective Taste DNA
                        </h4>
                      </div>

                      <div className="space-y-3">
                        <div className="p-3.5 rounded-2xl bg-zinc-950/60 border border-zinc-850 flex items-center justify-between">
                          <div>
                            <p className="text-[10px] text-zinc-500 uppercase tracking-wider font-semibold">Total Watches</p>
                            <h5 className="text-lg font-bold text-zinc-100">
                              {(selectedClub.taste_profile?.total_watches as number) || 0} Logged
                            </h5>
                          </div>
                          <div className="p-2.5 rounded-xl bg-violet-600/10 text-violet-400">
                            <Clapperboard className="w-4 h-4" />
                          </div>
                        </div>

                        {/* Club Affinity Breakdown: no real per-club genre-affinity
                            computation exists yet (would need to aggregate members'
                            watch history against canonical genres), so there is
                            nothing honest to show here until members actually log
                            watches. Matches the "no activity yet" tone of the
                            LIVE CLUB ACTIVITY STREAM panel below. */}
                        <p className="text-[11px] text-zinc-500 text-center py-2">
                          Taste affinity will appear once members start logging watches.
                        </p>
                      </div>
                    </div>

                    {/* Members Roster */}
                    <div className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-4">
                      <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
                        <div className="flex items-center gap-2">
                          <Users className="w-4 h-4 text-violet-400" />
                          <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">
                            Members ({selectedClub.members.length})
                          </h4>
                        </div>
                      </div>

                      <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                        {selectedClub.members.map((m) => (
                          <div
                            key={m.user_id}
                            className="p-2.5 rounded-2xl bg-zinc-950/60 border border-zinc-850 flex items-center justify-between gap-3"
                          >
                            <div className="flex items-center gap-2.5">
                              <div className="w-7 h-7 rounded-xl bg-violet-600/20 text-violet-300 flex items-center justify-center text-xs font-bold">
                                {(m.user_name || "M").charAt(0).toUpperCase()}
                              </div>
                              <div>
                                <p className="text-xs font-bold text-zinc-200">{m.user_name || "Club Member"}</p>
                                <p className="text-[10px] text-zinc-500 font-mono">
                                  {m.user_username ? `@${m.user_username}` : "Member"}
                                </p>
                              </div>
                            </div>
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-zinc-900 text-zinc-400 border border-zinc-800 uppercase">
                              {m.role}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Live Activity Feed */}
                  <div className="space-y-6 lg:col-span-2">
                    <div className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-4">
                      <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
                        <div className="flex items-center gap-2">
                          <Activity className="w-4 h-4 text-emerald-400" />
                          <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">
                            Live Club Activity Stream
                          </h4>
                        </div>
                        <span className="text-[10px] text-zinc-500 font-mono">Real-time sync</span>
                      </div>

                      {isLoadingClubFeed ? (
                        <div className="py-8">
                          <LoadingState message="Syncing club viewing logs..." />
                        </div>
                      ) : clubFeed.length === 0 ? (
                        <div className="text-center py-10 space-y-2">
                          <p className="text-xs text-zinc-400">No activity logged in this club yet.</p>
                          <p className="text-[11px] text-zinc-500">
                            When members log watches, ratings, or reviews, they will appear here in the collective feed.
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                          {clubFeed.map((act) => (
                            <div
                              key={act.activity_id}
                              className="p-3.5 rounded-2xl bg-zinc-950/80 border border-zinc-850 hover:border-zinc-700 flex items-start gap-3 transition-all"
                            >
                              <div className="w-8 h-8 rounded-xl bg-violet-600/10 text-violet-400 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                                {act.activity_type === "WATCH" ? "🎬" : act.activity_type === "RATING" ? "★" : "💬"}
                              </div>
                              <div className="space-y-1 flex-1">
                                <div className="flex items-center justify-between">
                                  <p className="text-xs font-bold text-zinc-200">
                                    {act.user_name || "A member"}{" "}
                                    <span className="font-normal text-zinc-400">
                                      {act.activity_type === "WATCH"
                                        ? "completed a screening"
                                        : act.activity_type === "RATING"
                                        ? "rated a title"
                                        : "posted a review"}
                                    </span>
                                  </p>
                                  <span className="text-[10px] text-zinc-500 font-mono">
                                    {new Date(act.created_at).toLocaleDateString()}
                                  </span>
                                </div>
                                {act.metadata_json && (
                                  <p className="text-xs text-zinc-400 font-medium">
                                    {String(act.metadata_json.title || act.metadata_json.canonical_title || "Film event")}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* ── TAB 2: MONTHLY CHALLENGES ───────────────────────────────────── */}
        {activeTab === "challenges" && (
          <div className="space-y-6">
            {isLoadingChallenges ? (
              <div className="py-12">
                <LoadingState message="Fetching active cinema challenges..." />
              </div>
            ) : challenges.length === 0 ? (
              <div className="text-center py-16 p-8 rounded-3xl bg-zinc-900/30 border border-zinc-900 space-y-4">
                <div className="w-16 h-16 rounded-3xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto border border-amber-500/20">
                  <Trophy className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-base font-bold text-zinc-100">No Active Challenges</h3>
                  <p className="text-xs text-zinc-400 max-w-md mx-auto">
                    Launch monthly viewing challenges for yourself or your watch club to explore new genres, directors, and cinema eras.
                  </p>
                </div>
                <button
                  onClick={() => setIsCreateChallengeOpen(true)}
                  className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-amber-600 hover:bg-amber-500 transition-all shadow-lg shadow-amber-600/30 cursor-pointer inline-flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Launch First Challenge</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {challenges.map((ch) => {
                  const daysLeft = Math.max(
                    0,
                    Math.ceil((new Date(ch.ends_at).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
                  );
                  const hasJoined = ch.my_progress !== null && ch.my_progress !== undefined;
                  const progressPct = hasJoined
                    ? Math.min(100, Math.round(((ch.my_progress || 0) / Math.max(1, ch.goal_count)) * 100))
                    : 0;

                  return (
                    <div
                      key={ch.challenge_id}
                      className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-850 hover:border-amber-500/40 transition-all flex flex-col justify-between space-y-5"
                    >
                      <div className="space-y-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                            <Trophy className="w-6 h-6" />
                          </div>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            {daysLeft} days left
                          </span>
                        </div>

                        <div>
                          <h4 className="text-sm font-bold text-zinc-100">{ch.title}</h4>
                          <p className="text-xs text-zinc-400 mt-1 leading-relaxed line-clamp-2">
                            {ch.description || `Watch ${ch.goal_count} qualifying titles before the challenge concludes.`}
                          </p>
                        </div>

                        {/* Real per-user progress -- was a hardcoded 40%-width
                            bar for every challenge/user regardless of anyone's
                            actual progress; now driven by the caller's real
                            my_progress from GET /social/challenges. */}
                        <div className="space-y-1.5 pt-2">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="text-zinc-400">
                              {hasJoined ? `${ch.my_progress} / ${ch.goal_count} Logged` : "Not Joined Yet"}
                            </span>
                            <span className="font-bold text-amber-400">{ch.goal_count} Films</span>
                          </div>
                          <div className="h-2 w-full bg-zinc-950 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-amber-500 rounded-full transition-all"
                              style={{ width: `${progressPct}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      <div className="pt-4 border-t border-zinc-900 flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 text-[11px] text-zinc-500">
                          <Users className="w-3.5 h-3.5 text-zinc-400" />
                          <span>{ch.participant_count} Cinephiles</span>
                        </div>

                        <div className="flex items-center gap-2">
                          {hasJoined ? (
                            <>
                              <button
                                onClick={() => progressChallengeMutation.mutate({ challengeId: ch.challenge_id, increment: 1 })}
                                disabled={ch.my_completed}
                                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-800 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                +1 Log
                              </button>
                              <span className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-emerald-300 bg-emerald-500/10 border border-emerald-500/20">
                                {ch.my_completed ? "Completed!" : "Joined"}
                              </span>
                            </>
                          ) : (
                            <button
                              onClick={() => joinChallengeMutation.mutate(ch.challenge_id)}
                              className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-amber-600 hover:bg-amber-500 transition-all shadow-md shadow-amber-600/20 cursor-pointer"
                            >
                              Join
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ── MODAL: CREATE WATCH CLUB ────────────────────────────────────── */}
        {isCreateClubOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200" role="dialog" aria-modal="true" aria-labelledby="create-club-modal-title">
            <div ref={createClubModalRef} className="relative w-full max-w-md p-6 rounded-3xl bg-zinc-950 border border-violet-500/30 shadow-2xl space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-zinc-900">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-violet-400" aria-hidden="true" />
                  <h3 id="create-club-modal-title" className="text-sm font-bold text-zinc-100">Create Watch Club</h3>
                </div>
                <button
                  onClick={() => setIsCreateClubOpen(false)}
                  aria-label="Close modal"
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
                >
                  <X className="w-4 h-4" aria-hidden="true" />
                </button>
              </div>

              <form onSubmit={handleCreateClubSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-300">Club Name</label>
                  <input
                    type="text"
                    required
                    value={clubName}
                    onChange={(e) => setClubName(e.target.value)}
                    placeholder="e.g. Midnight Cyberpunk Collective"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-300">Description</label>
                  <textarea
                    rows={3}
                    value={clubDescription}
                    onChange={(e) => setClubDescription(e.target.value)}
                    placeholder="What films does your club explore and discuss?"
                    className="w-full px-3.5 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500 resize-none"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-300">Avatar / Poster Image URL (Optional)</label>
                  <input
                    type="url"
                    value={clubAvatarUrl}
                    onChange={(e) => setClubAvatarUrl(e.target.value)}
                    placeholder="https://images.unsplash.com/..."
                    className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsCreateClubOpen(false)}
                    className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-zinc-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createClubMutation.isPending || !clubName.trim()}
                    className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 transition-all shadow-lg shadow-violet-600/30 disabled:opacity-50 cursor-pointer"
                  >
                    {createClubMutation.isPending ? "Creating..." : "Establish Club"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ── MODAL: CREATE CHALLENGE ─────────────────────────────────────── */}
        {isCreateChallengeOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200" role="dialog" aria-modal="true" aria-labelledby="create-challenge-modal-title">
            <div ref={createChallengeModalRef} className="relative w-full max-w-md p-6 rounded-3xl bg-zinc-950 border border-amber-500/30 shadow-2xl space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-zinc-900">
                <div className="flex items-center gap-2">
                  <Trophy className="w-4 h-4 text-amber-400" aria-hidden="true" />
                  <h3 id="create-challenge-modal-title" className="text-sm font-bold text-zinc-100">Launch Viewing Challenge</h3>
                </div>
                <button
                  onClick={() => setIsCreateChallengeOpen(false)}
                  aria-label="Close modal"
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
                >
                  <X className="w-4 h-4" aria-hidden="true" />
                </button>
              </div>

              <form onSubmit={handleCreateChallengeSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-300">Challenge Title</label>
                  <input
                    type="text"
                    required
                    value={challengeTitle}
                    onChange={(e) => setChallengeTitle(e.target.value)}
                    placeholder="e.g. October Horror Marathon 2026"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-300">Description</label>
                  <textarea
                    rows={2}
                    value={challengeDescription}
                    onChange={(e) => setChallengeDescription(e.target.value)}
                    placeholder="Rules and criteria for this challenge..."
                    className="w-full px-3.5 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-amber-500 resize-none"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-zinc-300">Challenge Type</label>
                  <select
                    value={challengeType}
                    onChange={(e) => setChallengeType(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 focus:outline-none focus:border-amber-500"
                  >
                    <option value="GENRE_COUNT">Genre Exploration Marathon</option>
                    <option value="DIRECTOR_COUNT">Director Filmography Retrospective</option>
                    <option value="TOTAL_WATCHES">Volume Screening Sprint</option>
                    <option value="THEMATIC">Thematic Collective Quest</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-zinc-300">Target Films</label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={challengeGoal}
                      onChange={(e) => setChallengeGoal(Number(e.target.value))}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-zinc-300">Duration (Days)</label>
                    <input
                      type="number"
                      min={1}
                      max={365}
                      value={challengeDays}
                      onChange={(e) => setChallengeDays(Number(e.target.value))}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsCreateChallengeOpen(false)}
                    className="px-4 py-2 rounded-xl text-xs text-zinc-400 hover:text-zinc-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createChallengeMutation.isPending || !challengeTitle.trim()}
                    className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-amber-600 hover:bg-amber-500 transition-all shadow-lg shadow-amber-600/30 disabled:opacity-50 cursor-pointer"
                  >
                    {createChallengeMutation.isPending ? "Launching..." : "Launch Challenge"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
}
