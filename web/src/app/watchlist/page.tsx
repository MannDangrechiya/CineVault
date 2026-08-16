"use client";

import React, { useState } from "react";
import Link from "next/link";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  Bookmark,
  Film,
  Tv,
  Trash2,
  Calendar,
  Sparkles,
  ArrowRight,
} from "lucide-react";

interface WatchlistItem {
  id: string;
  movieId: string;
  title: string;
  year: number;
  type: "MOVIE" | "TV_SERIES";
  posterUrl: string;
  matchScore: number;
  addedAt: string;
}

const initialWatchlist: WatchlistItem[] = [
  {
    id: "wl-1",
    movieId: "dune-part-two-2024",
    title: "Dune: Part Two",
    year: 2024,
    type: "MOVIE",
    posterUrl: "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80",
    matchScore: 99,
    addedAt: "Added today",
  },
  {
    id: "wl-2",
    movieId: "oppenheimer-2023",
    title: "Oppenheimer",
    year: 2023,
    type: "MOVIE",
    posterUrl: "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=600&q=80",
    matchScore: 94,
    addedAt: "Added 2 days ago",
  },
  {
    id: "wl-3",
    movieId: "severance-2022",
    title: "Severance",
    year: 2022,
    type: "TV_SERIES",
    posterUrl: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80",
    matchScore: 96,
    addedAt: "Added last week",
  },
  {
    id: "wl-4",
    movieId: "blade-runner-2049",
    title: "Blade Runner 2049",
    year: 2017,
    type: "MOVIE",
    posterUrl: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&q=80",
    matchScore: 98,
    addedAt: "Added last week",
  },
];

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>(initialWatchlist);
  const [filter, setFilter] = useState<"ALL" | "MOVIE" | "TV_SERIES">("ALL");

  const removeItem = (id: string) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
  };

  const filteredItems = items.filter((item) => {
    if (filter === "ALL") return true;
    return item.type === filter;
  });

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
            {filteredItems.map((item) => (
              <div
                key={item.id}
                className="group relative p-3 rounded-2xl bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all duration-300 flex flex-col justify-between"
              >
                <div>
                  {/* Poster Link */}
                  <Link
                    href={`/movies/${item.movieId}`}
                    className="relative aspect-[2/3] w-full bg-zinc-950 rounded-xl overflow-hidden block mb-3"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={item.posterUrl}
                      alt={item.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />

                    {/* Floating Badge */}
                    <div className="absolute top-2 left-2 right-2 flex items-center justify-between">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-zinc-950/80 backdrop-blur-md text-zinc-300 border border-zinc-800">
                        {item.type === "MOVIE" ? <Film className="w-2.5 h-2.5" /> : <Tv className="w-2.5 h-2.5" />}
                        {item.type === "MOVIE" ? "Movie" : "Series"}
                      </span>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 backdrop-blur-md">
                        <Sparkles className="w-2.5 h-2.5" />
                        {item.matchScore}%
                      </span>
                    </div>
                  </Link>

                  {/* Title & Year */}
                  <Link
                    href={`/movies/${item.movieId}`}
                    className="text-xs font-bold text-zinc-100 hover:text-violet-400 transition-colors line-clamp-1 block"
                  >
                    {item.title}
                  </Link>

                  <div className="flex items-center justify-between text-[11px] text-zinc-500 mt-1">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-zinc-600" />
                      {item.year}
                    </span>
                    <span>{item.addedAt}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-3 mt-3 border-t border-zinc-900/80">
                  <Link
                    href={`/movies/${item.movieId}`}
                    className="text-[11px] text-violet-400 hover:text-violet-300 font-medium inline-flex items-center gap-1"
                  >
                    <span>View Details</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>

                  <button
                    onClick={() => removeItem(item.id)}
                    title="Remove from Watchlist"
                    className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-zinc-800/80 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
