"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Film, Sparkles, Bookmark, Menu, X, Clapperboard, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { navigationItems as allMobileRoutes } from "./navigation";

const mainMobileTabs = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Oracle", href: "/oracle", icon: Bot },
  { name: "Movies", href: "/movies", icon: Film },
  { name: "Social", href: "/social", icon: Sparkles },
  { name: "Watchlist", href: "/watchlist", icon: Bookmark },
];

export const MobileNav: React.FC = () => {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      // Focus first element or close button
      const closeBtn = drawerRef.current?.querySelector('button');
      closeBtn?.focus();
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
      if (document.activeElement === document.body) {
        // Only return focus if focus was lost to the body
        triggerRef.current?.focus();
      }
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (pathname === "/login") return null;

  return (
    <>
      {/* Mobile Bottom Navigation Bar (Visible < 768px) */}
      <nav aria-label="Mobile Bottom Navigation" className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-zinc-950/80 border-t border-zinc-900 backdrop-blur-xl z-40 px-2 flex items-center justify-around">
        {mainMobileTabs.map((tab) => {
          const isActive =
            pathname === tab.href ||
            (tab.href !== "/" && pathname.startsWith(`${tab.href}/`));
          const Icon = tab.icon;
          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={cn(
                "flex flex-col items-center justify-center w-14 py-1 rounded-xl transition-colors text-[10px] font-medium gap-0.5",
                isActive ? "text-violet-400 font-semibold" : "text-zinc-400 hover:text-zinc-200"
              )}
            >
              <Icon className={cn("w-4 h-4", isActive ? "text-violet-400" : "text-zinc-400")} aria-hidden="true" />
              <span>{tab.name}</span>
            </Link>
          );
        })}

        {/* More Menu Trigger */}
        <button
          ref={triggerRef}
          onClick={() => setIsOpen(true)}
          aria-expanded={isOpen}
          aria-haspopup="dialog"
          aria-label="Open more menu"
          className="flex flex-col items-center justify-center w-14 py-1 rounded-xl text-[10px] font-medium text-zinc-400 hover:text-zinc-200"
        >
          <Menu className="w-4 h-4" aria-hidden="true" />
          <span>More</span>
        </button>
      </nav>

      {/* Slide-over Full Drawer Menu */}
      {isOpen && (
        <div 
          className="md:hidden fixed inset-0 z-50 flex" 
          role="dialog" 
          aria-modal="true" 
          aria-label="Mobile Menu"
        >
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer Panel */}
          <div 
            ref={drawerRef}
            className="relative w-4/5 max-w-xs bg-zinc-950 h-full border-r border-zinc-900 p-6 flex flex-col z-10 animate-in slide-in-from-left duration-200"
          >
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <Clapperboard className="w-5 h-5 text-violet-400" aria-hidden="true" />
                <span className="font-bold text-zinc-50 tracking-wider">CineVault OS</span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                aria-label="Close menu"
                className="p-1.5 rounded-xl text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              >
                <X className="w-5 h-5" aria-hidden="true" />
              </button>
            </div>

            <nav aria-label="Main Navigation" className="flex-1 space-y-1 overflow-y-auto">
              {allMobileRoutes.map((route) => {
                const isActive =
                  pathname === route.href ||
                  (route.href !== "/" && pathname.startsWith(`${route.href}/`));
                const Icon = route.icon;
                return (
                  <Link
                    key={route.name}
                    href={route.href}
                    onClick={() => setIsOpen(false)}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-colors",
                      isActive
                        ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/20"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
                    )}
                  >
                    <Icon className={cn("w-4 h-4", isActive ? "text-violet-400" : "text-zinc-500")} aria-hidden="true" />
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
