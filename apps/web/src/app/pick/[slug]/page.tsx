"use client";

import React, { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getPickRoom,
  castPickVote,
  closePickRoom,
} from "@/lib/api/personal";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  ThumbsUp,
  Share2,
  Lock,
  Users,
  CheckCheck,
  AlertCircle,
  Film,
} from "lucide-react";
import Link from "next/link";
import { MediaPoster } from "@/components/media/MediaPoster";

export default function GroupPickRoomPage() {
  const params = useParams();
  const slug = typeof params.slug === "string" ? params.slug : "";
  const queryClient = useQueryClient();

  const [guestName, setGuestName] = useState("");
  const [copied, setCopied] = useState(false);
  const [votedTitleIds, setVotedTitleIds] = useState<string[]>([]);

  const {
    data: room,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["pickRoom", slug],
    queryFn: () => getPickRoom(slug),
    enabled: Boolean(slug),
    refetchInterval: 5000, // Poll every 5s for live party votes
  });

  const voteMutation = useMutation({
    mutationFn: (titleId: string) =>
      castPickVote(slug, {
        title_id: titleId,
        guest_name: guestName.trim() || undefined,
        vote_type: "UPVOTE",
      }),
    onSuccess: (_, titleId) => {
      setVotedTitleIds((prev) => [...prev, titleId]);
      queryClient.invalidateQueries({ queryKey: ["pickRoom", slug] });
    },
  });

  const closeMutation = useMutation({
    mutationFn: () => closePickRoom(slug),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pickRoom", slug] });
    },
  });

  const copyRoomLink = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const highestVotes = useMemo(() => {
    if (!room?.candidates.length) return 1;
    return Math.max(...room.candidates.map((c) => c.upvotes), 1);
  }, [room]);

  if (isLoading) {
    return (
      <PageContainer title="Movie Night Ballot" subtitle="Connecting to voting room...">
        <div className="flex items-center justify-center p-16">
          <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </PageContainer>
    );
  }

  if (isError || !room) {
    return (
      <PageContainer title="Ballot Not Found" subtitle="This movie night room does not exist or has expired.">
        <div className="p-8 rounded-2xl bg-zinc-900/30 border border-zinc-900 text-center max-w-md mx-auto space-y-4">
          <AlertCircle className="w-12 h-12 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold text-zinc-100">Ballot Room Not Found</h2>
          <p className="text-xs text-zinc-400">
            Please check the link or ask your party host for a fresh invite.
          </p>
          <Link
            href="/social"
            className="inline-block px-4 py-2 text-xs font-semibold rounded-xl bg-violet-600 hover:bg-violet-500 text-white"
          >
            Back to Social Hub
          </Link>
        </div>
      </PageContainer>
    );
  }

  const isResolved = room.status === "RESOLVED";
  const hostLabel = room.host_name || room.host_username || "Party Host";

  return (
    <PageContainer
      title={room.title}
      subtitle={`Hosted by ${hostLabel} • ${room.total_votes} total votes cast`}
      action={
        <div className="flex items-center gap-2">
          <button
            onClick={copyRoomLink}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 transition-all cursor-pointer shadow-sm"
          >
            {copied ? (
              <>
                <CheckCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Link Copied!</span>
              </>
            ) : (
              <>
                <Share2 className="w-3.5 h-3.5 text-violet-400" />
                <span>Share Ballot</span>
              </>
            )}
          </button>

          {!isResolved && (
            <button
              onClick={() => closeMutation.mutate()}
              disabled={closeMutation.isPending}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-amber-600 hover:bg-amber-500 shadow-md shadow-amber-600/30 transition-all cursor-pointer disabled:opacity-50"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>{closeMutation.isPending ? "Locking..." : "Finalize Winner"}</span>
            </button>
          )}
        </div>
      }
    >
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Winner Banner (if RESOLVED) */}
        {isResolved && (
          <div className="p-8 rounded-3xl bg-gradient-to-br from-amber-500/20 via-zinc-900/80 to-zinc-950 border border-amber-500/30 shadow-2xl relative overflow-hidden text-center space-y-3 animate-in zoom-in-95 duration-300">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center mx-auto text-amber-300 text-2xl shadow-lg shadow-amber-500/20">
              🏆
            </div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
              Winning Choice
            </span>
            <h2 className="text-2xl sm:text-3xl font-black text-zinc-100">
              {room.winning_title_name || "Community Favorite"}
            </h2>
            <p className="text-xs text-zinc-400 max-w-md mx-auto">
              Voting has officially closed. Grab the popcorn and start the stream!
            </p>
            {room.winning_title_id && (
              <div className="pt-3">
                <Link
                  href={`/movies/${room.winning_title_id}`}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-bold bg-amber-500 hover:bg-amber-400 text-black shadow-lg shadow-amber-500/30 transition-all"
                >
                  <Film className="w-4 h-4" />
                  <span>View Title & Log Watch</span>
                </Link>
              </div>
            )}
          </div>
        )}

        {/* Guest Name input bar (if OPEN) */}
        {!isResolved && (
          <div className="p-4 rounded-2xl bg-zinc-900/50 border border-zinc-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs text-zinc-300">
              <Users className="w-4 h-4 text-violet-400" />
              <span className="font-semibold">Voter Name (Optional):</span>
            </div>
            <input
              type="text"
              placeholder="e.g. Alex (Guest)"
              value={guestName}
              onChange={(e) => setGuestName(e.target.value)}
              className="w-full sm:w-64 px-3 py-1.5 rounded-xl bg-zinc-950 border border-zinc-800 text-xs text-zinc-200 placeholder:text-zinc-400 focus:outline-none focus:border-violet-500"
            />
          </div>
        )}

        {/* Ballot Candidates Grid */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
            <span>Nominated Titles ({room.candidates.length})</span>
            <span className="text-[10px] lowercase text-zinc-400 font-normal">
              (click upvote on all you want to watch)
            </span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {room.candidates.map((cand) => {
              const pct = Math.round((cand.upvotes / (room.total_votes || 1)) * 100);
              const isWinning = isResolved && cand.title_id === room.winning_title_id;
              const hasVoted = votedTitleIds.includes(cand.title_id);

              return (
                <div
                  key={cand.title_id}
                  className={`p-4 rounded-2xl border transition-all flex gap-4 ${
                    isWinning
                      ? "bg-amber-500/10 border-amber-500/40 shadow-lg shadow-amber-500/10"
                      : "bg-zinc-900/40 border-zinc-800/80 hover:border-zinc-700"
                  }`}
                >
                  {/* Poster Thumbnail */}
                  <div className="w-20 h-28 rounded-xl overflow-hidden bg-zinc-950 border border-zinc-800 shrink-0 relative">
                    <MediaPoster
                      src={cand.poster_url}
                      alt={cand.canonical_title}
                      imgClassName="w-full h-full object-cover"
                    />
                    {isWinning && (
                      <div className="absolute top-1 right-1 p-1 rounded-md bg-amber-500 text-black text-xs font-bold">
                        ★
                      </div>
                    )}
                  </div>

                  {/* Details & Vote Bar */}
                  <div className="flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="text-sm font-bold text-zinc-100 line-clamp-1">
                            {cand.canonical_title}
                          </h4>
                          <p className="text-[11px] text-zinc-400">
                            {cand.production_year || "Feature Film"}
                          </p>
                        </div>

                        {!isResolved && (
                          <button
                            onClick={() => voteMutation.mutate(cand.title_id)}
                            disabled={voteMutation.isPending}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer shrink-0 ${
                              hasVoted
                                ? "bg-violet-600/30 text-violet-300 border border-violet-500/40"
                                : "bg-violet-600 hover:bg-violet-500 text-white shadow-md shadow-violet-600/20"
                            }`}
                          >
                            <ThumbsUp className="w-3.5 h-3.5" />
                            <span>{cand.upvotes}</span>
                          </button>
                        )}
                      </div>

                      {/* Vote Progress Bar */}
                      <div className="mt-3 space-y-1">
                        <div className="flex items-center justify-between text-[10px] text-zinc-400">
                          <span>{cand.upvotes} votes</span>
                          <span className="font-mono">{pct}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-zinc-950 rounded-full overflow-hidden border border-zinc-800">
                          <div
                            className={`h-full transition-all duration-500 ${
                              isWinning ? "bg-amber-400" : "bg-violet-500"
                            }`}
                            style={{
                              width: `${(cand.upvotes / highestVotes) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Voters list */}
                    {cand.voter_names.length > 0 && (
                      <div className="pt-2 text-[10px] text-zinc-400 truncate">
                        Voted by: {cand.voter_names.join(", ")}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
