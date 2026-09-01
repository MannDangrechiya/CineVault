"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getInvitePreview, acceptInviteToken } from "@/lib/api/personal";
import { PageContainer } from "@/components/ui/PageContainer";
import { Film, Sparkles, UserPlus, Users, Clapperboard, AlertCircle } from "lucide-react";
import Link from "next/link";

export default function InvitePreviewPage() {
  const params = useParams();
  const router = useRouter();
  const token = typeof params.token === "string" ? params.token : "";

  const {
    data: preview,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["invitePreview", token],
    queryFn: () => getInvitePreview(token),
    enabled: Boolean(token),
  });

  const acceptMutation = useMutation({
    mutationFn: () => acceptInviteToken(token),
    onSuccess: () => {
      router.push("/social");
    },
  });

  if (isLoading) {
    return (
      <PageContainer title="CineVault Invite" subtitle="Loading cinephile taste profile...">
        <div className="flex items-center justify-center p-16">
          <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </PageContainer>
    );
  }

  if (isError || !preview) {
    return (
      <PageContainer title="Invitation Not Found" subtitle="This invite link may have expired or is invalid.">
        <div className="p-8 rounded-2xl bg-zinc-900/30 border border-zinc-900 text-center max-w-md mx-auto space-y-4">
          <AlertCircle className="w-12 h-12 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold text-zinc-100">Invalid Invite Link</h2>
          <p className="text-xs text-zinc-400">
            We couldn&apos;t locate this invitation. It may have expired or already been converted.
          </p>
          <Link
            href="/login"
            className="inline-block px-4 py-2 text-xs font-semibold rounded-xl bg-violet-600 hover:bg-violet-500 text-white"
          >
            Go to CineVault
          </Link>
        </div>
      </PageContainer>
    );
  }

  const hostName = preview.inviter_name || preview.inviter_username || "A fellow cinephile";

  return (
    <PageContainer
      title="CineVault Cinema Invitation"
      subtitle={`${hostName} has invited you to connect on CineVault`}
    >
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Hero Card */}
        <div className="p-8 rounded-3xl bg-gradient-to-br from-violet-950/40 via-zinc-900/60 to-zinc-950 border border-violet-500/20 shadow-2xl relative overflow-hidden text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center mx-auto shadow-lg shadow-violet-600/30 text-white text-2xl font-black">
            🎬
          </div>

          <div className="space-y-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-violet-400">
              Taste Preview Invitation
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-zinc-100">
              Join {hostName}&apos;s Film Circle
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 max-w-lg mx-auto">
              Compare your cinema taste vectors, exchange calibrated recommendations, and discover films together.
            </p>
          </div>

          {/* Baked Taste Snapshot */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 text-left">
            <div className="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                <Sparkles className="w-3.5 h-3.5 text-violet-400" />
                <span className="font-medium">Top Genres</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {preview.top_genres.length > 0 ? (
                  preview.top_genres.map((g) => (
                    <span
                      key={g}
                      className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-violet-500/10 text-violet-300 border border-violet-500/20"
                    >
                      {g}
                    </span>
                  ))
                ) : (
                  <span className="text-[11px] text-zinc-400">General Cinema</span>
                )}
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                <Clapperboard className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-medium">Recent Watches</span>
              </div>
              <div className="space-y-1">
                {preview.recent_watched_titles.length > 0 ? (
                  preview.recent_watched_titles.slice(0, 2).map((t) => (
                    <p key={t} className="text-[11px] text-zinc-300 font-medium truncate">
                      • {t}
                    </p>
                  ))
                ) : (
                  <span className="text-[11px] text-zinc-400">Catalog explorer</span>
                )}
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 space-y-2">
              <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                <Film className="w-3.5 h-3.5 text-amber-400" />
                <span className="font-medium">Logged Titles</span>
              </div>
              <p className="text-lg font-bold text-amber-300 font-mono">
                {preview.total_watched_count} films
              </p>
            </div>
          </div>

          {/* Action CTAs */}
          <div className="pt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => acceptMutation.mutate()}
              disabled={acceptMutation.isPending}
              className="w-full sm:w-auto px-6 py-3 rounded-full text-xs font-bold text-white bg-violet-600 hover:bg-violet-500 shadow-lg shadow-violet-600/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              <UserPlus className="w-4 h-4" />
              <span>
                {acceptMutation.isPending ? "Connecting Circle..." : `Accept & Connect with ${hostName}`}
              </span>
            </button>

            <Link
              href="/login"
              className="w-full sm:w-auto px-6 py-3 rounded-full text-xs font-semibold text-zinc-300 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 flex items-center justify-center gap-2 transition-all"
            >
              <Users className="w-4 h-4 text-zinc-400" />
              <span>Log In to CineVault</span>
            </Link>
          </div>

          {acceptMutation.isError && (
            <p className="text-xs text-rose-400 pt-2">
              Failed to accept invitation. You might already be friends or need to sign in first.
            </p>
          )}
        </div>
      </div>
    </PageContainer>
  );
}
