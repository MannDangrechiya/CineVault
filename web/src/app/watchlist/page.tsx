"use client";

import React from "react";
import Link from "next/link";
import { PageContainer } from "@/components/ui/PageContainer";
import { Bookmark, Film } from "lucide-react";

export default function WatchlistPage() {
  return (
    <PageContainer
      title="Watchlist"
      subtitle="Saved titles queued for future viewing"
    >
      <div className="space-y-6">
        <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-zinc-900/30 border border-zinc-900 backdrop-blur-md min-h-[280px]">
          <div className="w-12 h-12 rounded-2xl bg-zinc-900 flex items-center justify-center mb-4 border border-zinc-800">
            <Bookmark className="w-6 h-6 text-zinc-500" />
          </div>
          <h3 className="text-base font-bold text-zinc-100 mb-1">Watchlist is Empty</h3>
          <p className="text-xs sm:text-sm text-zinc-400 max-w-md mb-6 leading-relaxed">
            Explore the catalog or accept incoming friend recommendations to build your personal watchlist.
          </p>
          <Link
            href="/movies"
            className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/20 transition-all"
          >
            <Film className="w-3.5 h-3.5" />
            <span>Browse Movies Catalog</span>
          </Link>
        </div>
      </div>
    </PageContainer>
  );
}
