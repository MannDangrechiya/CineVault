"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Film,
  Tv,
  Bookmark,
  History,
  FolderKanban,
  Settings,
  Library,
  Sparkles,
  Clapperboard,
  Bot,
  UploadCloud,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const navigationItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "AI Oracle", href: "/oracle", icon: Bot, badge: "Oracle" },
  { name: "Movies", href: "/movies", icon: Film },
  { name: "Series", href: "/series", icon: Tv },
  { name: "Social & Match", href: "/social", icon: Sparkles, badge: "AI" },
  { name: "Library", href: "/library", icon: Library },
  { name: "Watchlist", href: "/watchlist", icon: Bookmark },
  { name: "History", href: "/history", icon: History },
  { name: "Collections", href: "/collections", icon: FolderKanban },
  { name: "Import", href: "/import", icon: UploadCloud },
  { name: "Settings", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  // Hide sidebar on login route
  if (pathname === "/login") return null;

  return (
    <aside className="hidden md:flex flex-col w-64 border-r border-zinc-900 bg-zinc-950/70 backdrop-blur-xl shrink-0 h-screen sticky top-0 z-20">
      {/* Brand Header */}
      <div className="flex items-center gap-3 px-6 h-16 border-b border-zinc-900">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-600/20">
          <Clapperboard className="w-4 h-4 text-white" />
        </div>
        <div className="flex items-center gap-2">
          <span className="font-bold text-sm tracking-wider text-zinc-50 uppercase">
            Cine<span className="text-violet-400">Vault</span>
          </span>
          <span className="px-1.5 py-0.5 text-[9px] font-semibold tracking-wider text-violet-400 bg-violet-500/10 border border-violet-500/20 rounded-md">
            v2.0
          </span>
        </div>
      </div>

      {/* Main Navigation List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 mb-2">
          <span className="text-[10px] font-medium tracking-wider text-zinc-500 uppercase">
            Navigation
          </span>
        </div>
        {navigationItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(`${item.href}/`));
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all group relative",
                isActive
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/20 shadow-sm shadow-violet-500/10"
                  : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/60"
              )}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isActive ? "text-violet-400" : "text-zinc-500 group-hover:text-zinc-300"
                  )}
                />
                <span>{item.name}</span>
              </div>
              <div className="flex items-center gap-1.5">
                {item.badge && (
                  <span className="px-1.5 py-0.2 text-[9px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
                    {item.badge}
                  </span>
                )}
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-400 shadow-sm shadow-violet-400" />
                )}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Footer Status Badge */}
      <div className="p-3 m-3 rounded-xl bg-zinc-900/40 border border-zinc-900 text-xs">
        <div className="flex items-center gap-2 text-zinc-300 font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] text-zinc-300">CineVault Engine Active</span>
        </div>
        <p className="text-[10px] text-zinc-500 mt-1">OLED Cinematic Edition</p>
      </div>
    </aside>
  );
};
