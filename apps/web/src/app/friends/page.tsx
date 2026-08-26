"use client";

import React from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import { Users, Inbox, Send, Check, X, ShieldCheck, UserPlus } from "lucide-react";
import { getFriendships, updateFriendshipStatus, type FriendshipItem } from "@/lib/api/ai";
import { useAuth } from "@/components/auth/AuthProvider";
import { LoadingState } from "@/components/ui/States";

function getTrustTier(trustScore: number) {
  if (trustScore >= 76) return { label: "Oracle", badgeClass: "text-amber-400 bg-amber-500/10 border-amber-500/30" };
  if (trustScore >= 51) return { label: "Critic", badgeClass: "text-purple-400 bg-purple-500/10 border-purple-500/30" };
  if (trustScore >= 26) return { label: "Regular", badgeClass: "text-blue-400 bg-blue-500/10 border-blue-500/30" };
  return { label: "Curious", badgeClass: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30" };
}

function FriendRow({ friend }: { friend: FriendshipItem }) {
  const tier = getTrustTier(friend.trust_score ?? 50);
  return (
    <div className="p-4 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 flex items-center justify-between gap-3">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shadow-md text-xs font-bold shrink-0">
          {(friend.friend_name || "?").charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0">
          <p className="text-xs font-bold text-zinc-100 truncate">
            {friend.friend_name || "Community Member"}
          </p>
          <p className="text-[10px] text-zinc-500">
            {friend.friend_username ? `@${friend.friend_username}` : "Member"}
          </p>
        </div>
      </div>
      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium border shrink-0 ${tier.badgeClass}`}>
        {tier.label}
      </span>
    </div>
  );
}

export default function FriendsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: friendships = [], isLoading } = useQuery({
    queryKey: ["friendships"],
    queryFn: getFriendships,
  });

  const respondMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "ACCEPTED" | "BLOCKED" }) =>
      updateFriendshipStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["friendships"] });
    },
  });

  const accepted = friendships.filter((f) => f.status === "ACCEPTED");
  const pendingReceived = friendships.filter(
    (f) => f.status === "PENDING" && user?.sub && f.requester_id !== user.sub
  );
  const pendingSent = friendships.filter(
    (f) => f.status === "PENDING" && user?.sub && f.requester_id === user.sub
  );

  if (isLoading) {
    return (
      <PageContainer title="Manage Friends" subtitle="Loading your cinephile circle...">
        <div className="p-8">
          <LoadingState message="Fetching friendships..." />
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title="Manage Friends"
      subtitle="Accepted connections, pending requests, and how to grow your circle"
      action={
        <Link
          href="/social"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 shadow-md shadow-violet-600/30 transition-all"
        >
          <UserPlus className="w-3.5 h-3.5" />
          <span>Invite Friends</span>
        </Link>
      }
    >
      <div className="space-y-8">
        {/* How friends are added: no user-search/directory endpoint exists in
            this backend, so the invite-link flow (Social page) is the only
            real path to a new ACCEPTED friendship -- this page manages what
            already exists rather than pretending there's a "find people"
            search box that doesn't work. */}
        <div className="p-4 rounded-2xl bg-zinc-900/30 border border-zinc-900 text-xs text-zinc-400 flex items-center gap-2.5">
          <ShieldCheck className="w-4 h-4 text-violet-400 shrink-0" />
          <span>
            New friendships are made by sharing your invite link from the{" "}
            <Link href="/social" className="text-violet-400 hover:underline font-medium">
              Social Hub
            </Link>
            . Requests that reach you any other way show up below to accept or decline.
          </span>
        </div>

        {/* Pending Received */}
        {pendingReceived.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Inbox className="w-3.5 h-3.5 text-amber-400" />
              <span>Pending Requests ({pendingReceived.length})</span>
            </h3>
            <div className="space-y-2.5">
              {pendingReceived.map((f) => (
                <div
                  key={f.friendship_id}
                  className="p-4 rounded-2xl bg-amber-950/10 border border-amber-500/20 flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-600 to-orange-500 flex items-center justify-center text-white shadow-md text-xs font-bold shrink-0">
                      {(f.friend_name || "?").charAt(0).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-zinc-100 truncate">
                        {f.friend_name || "Community Member"} wants to connect
                      </p>
                      <p className="text-[10px] text-zinc-500">
                        {f.friend_username ? `@${f.friend_username}` : "Member"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => respondMutation.mutate({ id: f.friendship_id, status: "BLOCKED" })}
                      disabled={respondMutation.isPending}
                      className="p-2 rounded-xl text-zinc-400 hover:text-red-400 bg-zinc-900/80 hover:bg-red-950/30 border border-zinc-800 hover:border-red-900/50 transition-all cursor-pointer disabled:opacity-50"
                      title="Decline"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => respondMutation.mutate({ id: f.friendship_id, status: "ACCEPTED" })}
                      disabled={respondMutation.isPending}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 transition-all cursor-pointer disabled:opacity-50"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Accept</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pending Sent */}
        {pendingSent.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Send className="w-3.5 h-3.5 text-zinc-400" />
              <span>Awaiting Response ({pendingSent.length})</span>
            </h3>
            <div className="space-y-2.5">
              {pendingSent.map((f) => (
                <div
                  key={f.friendship_id}
                  className="p-4 rounded-2xl bg-zinc-900/30 border border-zinc-900 flex items-center gap-3 opacity-70"
                >
                  <div className="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center text-zinc-400 shadow-md text-xs font-bold shrink-0">
                    {(f.friend_name || "?").charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-zinc-300 truncate">
                      {f.friend_name || "Community Member"}
                    </p>
                    <p className="text-[10px] text-zinc-500">Request sent, waiting on them</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Accepted Friends */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
            <Users className="w-3.5 h-3.5 text-violet-400" />
            <span>Your Circle ({accepted.length})</span>
          </h3>
          {accepted.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-zinc-900/40 border border-zinc-900 text-zinc-400 space-y-3">
              <Users className="w-8 h-8 text-zinc-600 mx-auto" />
              <h3 className="text-sm font-semibold text-zinc-200">No Friends Yet</h3>
              <p className="text-xs text-zinc-500 max-w-sm mx-auto">
                Share your invite link from the Social Hub to build your circle.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {accepted.map((f) => (
                <FriendRow key={f.friendship_id} friend={f} />
              ))}
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  );
}
