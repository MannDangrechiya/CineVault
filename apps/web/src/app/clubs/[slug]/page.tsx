"use client";

import React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { Users, ShieldCheck, Dna, Clapperboard, Activity, ArrowLeft } from "lucide-react";
import { getWatchClub, joinWatchClub, getClubFeed } from "@/lib/api/personal";

export default function WatchClubDetailPage() {
  const params = useParams();
  const slug = typeof params.slug === "string" ? params.slug : "";
  const queryClient = useQueryClient();

  // Standalone, URL-addressable club page — previously a shared club link
  // (e.g. from an invite) had nowhere to land: GET /social/clubs only ever
  // lists clubs the caller already belongs to, so a club could only be
  // viewed via that list, meaning "join a club a friend shared with you"
  // was unreachable even though the backend (GET /social/clubs/{slug},
  // POST /social/clubs/{slug}/join) has always supported it — same shape
  // as the Pick Rooms create gap fixed elsewhere this session.
  const {
    data: club,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["watch-club-detail", slug],
    queryFn: () => getWatchClub(slug),
    enabled: Boolean(slug),
  });

  const { data: feed = [], isLoading: isLoadingFeed } = useQuery({
    queryKey: ["watch-club-feed", slug],
    queryFn: () => getClubFeed(slug, 20),
    enabled: Boolean(slug),
  });

  const joinMutation = useMutation({
    mutationFn: () => joinWatchClub(slug),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watch-club-detail", slug] });
      queryClient.invalidateQueries({ queryKey: ["watch-clubs"] });
    },
  });

  if (isLoading) {
    return (
      <PageContainer title="Watch Club" subtitle="Loading club taste DNA & live feed...">
        <div className="p-8">
          <LoadingState message="Loading club..." />
        </div>
      </PageContainer>
    );
  }

  if (isError || !club) {
    return (
      <PageContainer title="Club Not Found" subtitle="This watch club does not exist.">
        <ErrorState
          title="Watch Club Not Found"
          description="Please check the link or ask the club host for a fresh invite."
          onAction={() => refetch()}
        />
        <div className="text-center mt-4">
          <Link href="/clubs" className="text-xs text-violet-400 hover:underline">
            ← Back to Watch Clubs
          </Link>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title={club.club.name}
      subtitle={`Curated by ${club.club.creator_name || "CineVault Member"} • ${club.club.member_count} active members`}
      action={
        <div className="flex items-center gap-2">
          <Link
            href="/clubs"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 transition-all"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>All Clubs</span>
          </Link>
          <button
            onClick={() => joinMutation.mutate()}
            disabled={joinMutation.isPending}
            className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 transition-all shadow-lg shadow-violet-600/30 flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <Users className="w-3.5 h-3.5" />
            <span>{joinMutation.isPending ? "Joining..." : "Join Watch Club"}</span>
          </button>
        </div>
      }
    >
      <div className="space-y-6">
        {club.club.description && (
          <p className="text-xs text-zinc-300 leading-relaxed max-w-3xl p-4 rounded-2xl bg-zinc-900/40 border border-zinc-900">
            {club.club.description}
          </p>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Taste DNA + Members */}
          <div className="space-y-6 lg:col-span-1">
            <div className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-zinc-900">
                <Dna className="w-4 h-4 text-violet-400" />
                <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">
                  Collective Taste DNA
                </h4>
              </div>
              <div className="p-3.5 rounded-2xl bg-zinc-950/60 border border-zinc-850 flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold">Total Watches</p>
                  <h5 className="text-lg font-bold text-zinc-100">
                    {(club.taste_profile?.total_watches as number) || 0} Logged
                  </h5>
                </div>
                <div className="p-2.5 rounded-xl bg-violet-600/10 text-violet-400">
                  <Clapperboard className="w-4 h-4" />
                </div>
              </div>
              <p className="text-[11px] text-zinc-400 text-center py-2">
                Taste affinity will appear once members start logging watches.
              </p>
            </div>

            <div className="p-6 rounded-3xl bg-zinc-900/40 border border-zinc-900 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-violet-400" />
                  <h4 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">
                    Members ({club.members.length})
                  </h4>
                </div>
              </div>
              <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                {club.members.map((m) => (
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
                        <p className="text-[10px] text-zinc-400 font-mono">
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
                <span className="text-[10px] text-zinc-400 font-mono">Real-time sync</span>
              </div>

              {isLoadingFeed ? (
                <div className="py-8">
                  <LoadingState message="Syncing club viewing logs..." />
                </div>
              ) : feed.length === 0 ? (
                <div className="text-center py-10 space-y-2">
                  <p className="text-xs text-zinc-400">No activity logged in this club yet.</p>
                  <p className="text-[11px] text-zinc-400">
                    When members log watches, ratings, or reviews, they will appear here in the collective feed.
                  </p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                  {feed.map((act) => (
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
                          <span className="text-[10px] text-zinc-400 font-mono">
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

        <div className="flex items-center gap-1.5 text-[11px] text-zinc-400 justify-center">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>@{club.club.slug}</span>
        </div>
      </div>
    </PageContainer>
  );
}
