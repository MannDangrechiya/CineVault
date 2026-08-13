"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Film,
  Tv,
  Bookmark,
  Menu,
  X,
  History,
  FolderKanban,
  Download,
  Settings,
  Library,
  Clapperboard,
} from "lucide-react";
import { cn } from "@/lib/utils";

const mainMobileTabs = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Library", href: "/library", icon: Library },
  { name: "Movies", href: "/movies", icon: Film },
  { name: "Series", href: "/series", icon: Tv },
  { name: "Watchlist", href: "/watchlist", icon: Bookmark },
];

const allMobileRoutes = [
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

export const MobileNav: React.FC = () => {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  if (pathname === "/login") return null;

  return (
    <>
      {/* Mobile Bottom Navigation Bar (Visible < 768px) */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-slate-950/95 border-t border-slate-800/80 backdrop-blur-lg z-40 px-2 flex items-center justify-around">
        {mainMobileTabs.map((tab) => {
          const isActive = pathname === tab.href;
          const Icon = tab.icon;
          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={cn(
                "flex flex-col items-center justify-center w-14 py-1 rounded-lg transition-colors text-[10px] font-medium gap-0.5",
                isActive ? "text-violet-400 font-semibold" : "text-slate-400 hover:text-slate-200"
              )}
            >
              <Icon className={cn("w-4 h-4", isActive ? "text-violet-400" : "text-slate-400")} />
              <span>{tab.name}</span>
            </Link>
          );
        })}

        {/* More Menu Trigger */}
        <button
          onClick={() => setIsOpen(true)}
          className="flex flex-col items-center justify-center w-14 py-1 rounded-lg text-[10px] font-medium text-slate-400 hover:text-slate-200"
        >
          <Menu className="w-4 h-4" />
          <span>More</span>
        </button>
      </div>

      {/* Slide-over Full Drawer Menu */}
      {isOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={() => setIsOpen(false)}
          />

          {/* Drawer Panel */}
          <div className="relative w-4/5 max-w-xs bg-slate-950 h-full border-r border-slate-800 p-6 flex flex-col z-10 animate-in slide-in-from-left duration-200">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Clapperboard className="w-5 h-5 text-violet-400" />
                <span className="font-bold text-slate-100 tracking-wider">CineVault</span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <nav className="flex-1 space-y-1 overflow-y-auto">
              {allMobileRoutes.map((route) => {
                const isActive = pathname === route.href;
                const Icon = route.icon;
                return (
                  <Link
                    key={route.name}
                    href={route.href}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-colors",
                      isActive
                        ? "bg-violet-600/20 text-violet-300 font-semibold border border-violet-500/30"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                    )}
                  >
                    <Icon className={cn("w-4 h-4", isActive ? "text-violet-400" : "text-slate-500")} />
                    <span>{route.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      )}
    </>
  );
};
