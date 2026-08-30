"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  Bookmark,
  Film,
  Tv,
  Trash2,
  Calendar,
  ArrowRight,
} from "lucide-react";
import { getWatchlist, removeFromWatchlist } from "@/lib/api/personal";
import { LoadingState } from "@/components/ui/States";

export default function WatchlistPage() {
  const [filter, setFilter] = useState<"ALL" | "MOVIE" | "TV_SERIES">("ALL");
  const queryClient = useQueryClient();

  const { data: rawItems = [], isLoading } = useQuery({
    queryKey: ["watchlist"],
    queryFn: getWatchlist,
  });

  const removeMutation = useMutation({
    mutationFn: removeFromWatchlist,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });

  // Map API data to UI format
  const items = rawItems.map((item) => ({
    id: item.id,
    titleId: item.title_id,
    title: item.canonical_title || "Unknown Title",
    year: item.production_year || undefined,
    type: item.content_type || "MOVIE",
    posterUrl: item.poster_url || null,
    addedAt: new Date(item.added_at).toLocaleDateString(),
  }));

  const removeItem = (titleId: string) => {
    removeMutation.mutate(titleId);
  };

  const filteredItems = items.filter((item) => {
    if (filter === "ALL") return true;
    return item.type === filter;
  });

  if (isLoading) {
    return (
      <PageContainer title="Personal Watchlist" subtitle="Loading your watchlist...">
        <div className="p-8">
          <LoadingState message="Fetching watchlist..." />
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title="Personal Watchlist"
      subtitle="Saved canonical titles queued for your future viewing sessions"
      action={
        <Link
          href="/movies"
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/30 transition-all"
        >
          <Film className="w-3.5 h-3.5" />
          <span>Explore Catalog</span>
        </Link>
      }
    >
      <div className="space-y-6">
        {/* Filter Controls */}
        <div className="flex items-center justify-between gap-4 pb-2 border-b border-zinc-900">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFilter("ALL")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                filter === "ALL"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              All Items ({items.length})
            </button>
            <button
              onClick={() => setFilter("MOVIE")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                filter === "MOVIE"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              Feature Films
            </button>
            <button
              onClick={() => setFilter("TV_SERIES")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                filter === "TV_SERIES"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              TV Series
            </button>
          </div>
        </div>

        {/* Watchlist Grid */}
        {filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl bg-zinc-900/30 border border-zinc-900 backdrop-blur-md min-h-[280px]">
            <div className="w-12 h-12 rounded-2xl bg-zinc-900 flex items-center justify-center mb-4 border border-zinc-800">
              <Bookmark className="w-6 h-6 text-zinc-500" />
            </div>
            <h3 className="text-base font-bold text-zinc-100 mb-1">No Titles in Watchlist</h3>
            <p className="text-xs sm:text-sm text-zinc-400 max-w-md mb-6 leading-relaxed">
              Explore the catalog or accept incoming friend recommendations to build your queue.
            </p>
            <Link
              href="/movies"
              className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/20 transition-all"
            >
              <Film className="w-3.5 h-3.5" />
              <span>Browse Movies Catalog</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {filteredItems.map((item) => {
              const isMovie = !item.type || item.type.toUpperCase() === "MOVIE";
              const detailUrl = isMovie ? `/movies/${item.titleId}` : `/series/${item.titleId}`;

              return (
                <div
                  key={item.id}
                  className={`group relative p-3 rounded-2xl bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all duration-300 flex flex-col justify-between ${
                    removeMutation.isPending && removeMutation.variables === item.titleId ? "opacity-50" : ""
                  }`}
                >
                  <div>
                    {/* Poster Link */}
                    <Link
                      href={detailUrl}
                      className="relative aspect-[2/3] w-full bg-zinc-950 rounded-xl overflow-hidden block mb-3"
                    >
                      {item.posterUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={item.posterUrl}
                          alt={item.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-zinc-900 to-zinc-950 text-zinc-700">
                          {isMovie ? <Film className="w-8 h-8" /> : <Tv className="w-8 h-8" />}
                        </div>
                      )}

                      {/* Floating Badge */}
                      <div className="absolute top-2 left-2 right-2 flex items-center justify-between">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-zinc-950/80 backdrop-blur-md text-zinc-300 border border-zinc-800">
                          {isMovie ? <Film className="w-2.5 h-2.5" /> : <Tv className="w-2.5 h-2.5" />}
                          {isMovie ? "Movie" : "Series"}
                        </span>
                      </div>
                    </Link>

                    {/* Title & Year */}
                    <Link
                      href={detailUrl}
                      className="text-xs font-bold text-zinc-100 hover:text-violet-400 transition-colors line-clamp-1 block"
                    >
                      {item.title}
                    </Link>

                    <div className="flex items-center justify-between text-[11px] text-zinc-500 mt-1">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-zinc-600" />
                        {item.year ?? "—"}
                      </span>
                      <span>{item.addedAt}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-3 mt-3 border-t border-zinc-900/80">
                    <Link
                      href={detailUrl}
                      className="text-[11px] text-violet-400 hover:text-violet-300 font-medium inline-flex items-center gap-1"
                    >
                      <span>View Details</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>

                    <button
                      onClick={() => removeItem(item.titleId)}
                      disabled={removeMutation.isPending}
                      title="Remove from Watchlist"
                      className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-zinc-800/80 transition-colors cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
