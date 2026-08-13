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
  Download,
  Settings,
  Library,
  ShieldCheck,
  Clapperboard,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const navigationItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Library", href: "/library", icon: Library },
  { name: "Movies", href: "/movies", icon: Film },
  { name: "Series", href: "/series", icon: Tv },
  { name: "Watchlist", href: "/watchlist", icon: Bookmark },
  { name: "History", href: "/history", icon: History },
  { name: "Collections", href: "/collections", icon: FolderKanban },
  { name: "Import", href: "/import", icon: Download },
  { name: "Settings", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  // Hide sidebar on login route
  if (pathname === "/login") return null;

  return (
    <aside className="hidden md:flex flex-col w-64 border-r border-slate-800/80 bg-slate-950/80 backdrop-blur-md shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="flex items-center gap-3 px-6 h-16 border-b border-slate-800/80">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 via-purple-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-900/30 ring-1 ring-white/20">
          <Clapperboard className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-extrabold text-base tracking-wider text-slate-100 uppercase">
              Cine<span className="text-violet-400">Vault</span>
            </span>
            <span className="px-1.5 py-0.5 text-[9px] font-semibold tracking-wider text-violet-300 bg-violet-900/40 border border-violet-700/50 rounded uppercase">
              OS
            </span>
          </div>
          <p className="text-[10px] text-slate-400 font-mono">Web Edition v1.0</p>
        </div>
      </div>

      {/* Main Navigation List */}
      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 mb-2">
          <span className="text-[10px] font-bold tracking-wider text-slate-500 uppercase">
            Menu
          </span>
        </div>
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all group relative",
                isActive
                  ? "bg-violet-600/20 text-violet-300 border border-violet-500/30 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
              )}
            >
              <Icon
                className={cn(
                  "w-4 h-4 transition-colors",
                  isActive ? "text-violet-400" : "text-slate-500 group-hover:text-slate-300"
                )}
              />
              <span>{item.name}</span>
              {isActive && (
                <span className="absolute right-2 w-1.5 h-1.5 rounded-full bg-violet-400 shadow-sm shadow-violet-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer Info / Self-Host Status */}
      <div className="p-4 m-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center gap-2 mb-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-[11px] font-semibold text-slate-200">
            Open-Source Self-Hosted
          </span>
        </div>
        <p className="text-[10px] text-slate-400 leading-relaxed">
          Zero paid API dependencies. Fast & private.
        </p>
      </div>
    </aside>
  );
};
