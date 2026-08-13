"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { SearchPlaceholder } from "@/components/ui/SearchPlaceholder";
import { Bell, User, Server, LogOut } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";

interface HeaderProps {
  onOpenMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = () => {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();

  if (pathname === "/login") return null;

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between gap-4 sticky top-0 z-30">
      {/* Search Input Placeholder */}
      <div className="flex-1 max-w-md">
        <SearchPlaceholder />
      </div>

      {/* Action / Status Controls */}
      <div className="flex items-center gap-3">
        {/* Backend Status Indicator */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/50 text-[11px] font-medium text-emerald-300">
          <Server className="w-3 h-3 text-emerald-400" />
          <span>FastAPI Ready</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        </div>

        {/* Notification Placeholder */}
        <button
          disabled
          aria-label="Notifications"
          className="p-2 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-900 transition-colors cursor-not-allowed opacity-70"
        >
          <Bell className="w-4 h-4" />
        </button>

        {/* User Profile / Auth Control */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-medium text-slate-200">
              <div className="w-5 h-5 rounded-full bg-violet-600/40 border border-violet-500/50 flex items-center justify-center text-violet-300 font-bold text-[10px]">
                {user.username ? user.username.charAt(0).toUpperCase() : "U"}
              </div>
              <span className="max-w-[100px] truncate">{user.username || user.email}</span>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-2 text-slate-400 hover:text-red-400 rounded-lg hover:bg-slate-900 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-2 p-1.5 pl-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-medium text-slate-300 hover:border-slate-700 transition-colors"
          >
            <span>Sign In</span>
            <div className="w-6 h-6 rounded-full bg-violet-600/30 border border-violet-500/40 flex items-center justify-center text-violet-300">
              <User className="w-3.5 h-3.5" />
            </div>
          </Link>
        )}
      </div>
    </header>
  );
};
