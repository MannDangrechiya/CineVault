"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Bell, User, LogOut, Sparkles } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { getRecommendations } from "@/lib/api/personal";
import { getFriendships } from "@/lib/api/ai";

export const Header: React.FC = () => {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();

  // The notification dot used to be a hardcoded <span>, permanently visible
  // whether or not there was actually anything pending -- an "you have a
  // notification" claim shown to every user on every page regardless of
  // real state. Shares its queryKey/cache with the Social and Friends pages
  // (same underlying data), so this adds no extra request on pages that
  // already loaded them.
  const { data: receivedRecs = [] } = useQuery({
    queryKey: ["recommendations", "received"],
    queryFn: () => getRecommendations({ role: "received" }),
    enabled: isAuthenticated,
  });
  const { data: friendships = [] } = useQuery({
    queryKey: ["friendships"],
    queryFn: getFriendships,
    enabled: isAuthenticated,
  });
  const pendingRecCount = receivedRecs.filter((r) => r.status === "SENT").length;
  const pendingFriendCount = friendships.filter(
    (f) => f.status === "PENDING" && user?.sub && f.requester_id !== user.sub
  ).length;
  const hasPendingNotifications = pendingRecCount + pendingFriendCount > 0;

  if (pathname === "/login") return null;

  return (
    <header className="h-16 border-b border-zinc-900 bg-zinc-950/70 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-end gap-4 sticky top-0 z-30">
      {/* Action / Status Controls */}
      <div className="flex items-center gap-3">
        {/* AI Vector Match Ready Badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[11px] font-medium text-emerald-400">
          <Sparkles className="w-3 h-3 text-emerald-400" aria-hidden="true" />
          <span>Vector AI Ready</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" aria-hidden="true" />
        </div>

        {/* Notification Bell */}
        <Link
          href="/social"
          aria-label={hasPendingNotifications ? `Notifications (${pendingRecCount + pendingFriendCount} pending)` : "Notifications"}
          className="relative p-2 text-zinc-400 hover:text-zinc-100 rounded-xl hover:bg-zinc-900/80 transition-colors"
        >
          <Bell className="w-4 h-4" aria-hidden="true" />
          {hasPendingNotifications && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-violet-500 shadow-sm shadow-violet-500" aria-hidden="true" />
          )}
        </Link>

        {/* User Profile / Auth Control */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-900/80 border border-zinc-800 text-xs font-medium text-zinc-200">
              <div className="w-5 h-5 rounded-full bg-violet-600/30 border border-violet-500/40 flex items-center justify-center text-violet-300 font-bold text-[10px]" aria-hidden="true">
                {user.username ? user.username.charAt(0).toUpperCase() : "U"}
              </div>
              <span className="max-w-[100px] truncate">{user.username || user.email}</span>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              aria-label="Sign Out"
              className="p-2 text-zinc-400 hover:text-red-400 rounded-xl hover:bg-zinc-900/80 transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-2 p-1.5 pl-3 rounded-xl bg-zinc-900/80 border border-zinc-800 text-xs font-medium text-zinc-300 hover:border-zinc-700 hover:text-zinc-100 transition-colors"
          >
            <span>Sign In</span>
            <div className="w-6 h-6 rounded-full bg-violet-600/30 border border-violet-500/40 flex items-center justify-center text-violet-300" aria-hidden="true">
              <User className="w-3.5 h-3.5" aria-hidden="true" />
            </div>
          </Link>
        )}
      </div>
    </header>
  );
};
