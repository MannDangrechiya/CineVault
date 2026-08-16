"use client";

import React, { useState } from "react";
import Link from "next/link";
import { PageContainer } from "@/components/ui/PageContainer";
import { Calendar, Clock, ArrowRight } from "lucide-react";

interface HistoryEntry {
  id: string;
  movieId: string;
  title: string;
  year: number;
  type: "MOVIE" | "TV_SERIES";
  posterUrl: string;
  watchedAt: string;
  rating?: number;
  device: string;
}

const mockHistory: HistoryEntry[] = [
  {
    id: "hist-1",
    movieId: "dune-part-two-2024",
    title: "Dune: Part Two",
    year: 2024,
    type: "MOVIE",
    posterUrl: "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80",
    watchedAt: "Today, 8:45 PM",
    rating: 5,
    device: "Living Room Apple TV 4K",
  },
  {
    id: "hist-2",
    movieId: "blade-runner-2049",
    title: "Blade Runner 2049",
    year: 2017,
    type: "MOVIE",
    posterUrl: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&q=80",
    watchedAt: "Yesterday, 10:15 PM",
    rating: 5,
    device: "Home Theater OLED 65\"",
  },
  {
    id: "hist-3",
    movieId: "severance-2022",
    title: "Severance — S1:E9 'The We We Are'",
    year: 2022,
    type: "TV_SERIES",
    posterUrl: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80",
    watchedAt: "3 days ago",
    rating: 5,
    device: "iPad Pro",
  },
  {
    id: "hist-4",
    movieId: "oppenheimer-2023",
    title: "Oppenheimer",
    year: 2023,
    type: "MOVIE",
    posterUrl: "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=600&q=80",
    watchedAt: "Last week",
    rating: 4.5,
    device: "Plex Server (Living Room)",
  },
];

export default function HistoryPage() {
  const [historyItems] = useState<HistoryEntry[]>(mockHistory);

  return (
    <PageContainer
      title="Watch History"
      subtitle="Append-only timeline of viewing events, scrobbles, and playback sessions (CAT-2)"
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <Clock className="w-3.5 h-3.5 text-violet-400" />
            <span>4 Viewing Events Recorded • Synced via Webhook</span>
          </div>
        </div>

        <div className="space-y-3">
          {historyItems.map((item) => (
            <div
              key={item.id}
              className="p-4 rounded-2xl bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
            >
              <div className="flex items-center gap-4">
                <Link
                  href={`/movies/${item.movieId}`}
                  className="w-12 h-16 rounded-xl bg-zinc-950 overflow-hidden shrink-0 block"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={item.posterUrl}
                    alt={item.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  />
                </Link>

                <div className="space-y-1">
                  <Link
                    href={`/movies/${item.movieId}`}
                    className="text-xs sm:text-sm font-bold text-zinc-100 group-hover:text-violet-400 transition-colors"
                  >
                    {item.title}
                  </Link>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-500">
                    <span className="flex items-center gap-1 text-zinc-400">
                      <Calendar className="w-3 h-3 text-zinc-500" />
                      {item.watchedAt}
                    </span>
                    <span>•</span>
                    <span className="text-zinc-400">{item.device}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 justify-between sm:justify-end shrink-0">
                {item.rating && (
                  <div className="flex items-center gap-1 text-xs font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full">
                    <span>★</span>
                    <span>{item.rating} / 5</span>
                  </div>
                )}

                <Link
                  href={`/movies/${item.movieId}`}
                  className="inline-flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 font-medium"
                >
                  <span>Details</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
