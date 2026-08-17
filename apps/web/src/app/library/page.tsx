"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import { Plus } from "lucide-react";
import { getTitles } from "@/lib/api/titles";
import { LoadingState } from "@/components/ui/States";

export default function LibraryPage() {
  const [tab, setTab] = useState<"ALL" | "MOVIE" | "TV_SERIES">("ALL");

  const { data: moviesRes, isLoading: isLoadingMovies } = useQuery({
    queryKey: ["library", "movies"],
    queryFn: () => getTitles({ content_type: "MOVIE", limit: 6 }),
  });

  const { data: seriesRes, isLoading: isLoadingSeries } = useQuery({
    queryKey: ["library", "series"],
    queryFn: () => getTitles({ content_type: "TV_SERIES", limit: 4 }),
  });

  const libraryMovies = moviesRes?.data || [];
  const librarySeries = seriesRes?.data || [];

  const displayed =
    tab === "MOVIE"
      ? libraryMovies
      : tab === "TV_SERIES"
      ? librarySeries
      : [...libraryMovies, ...librarySeries];

  if (isLoadingMovies || isLoadingSeries) {
    return (
      <PageContainer title="Personal Media Library" subtitle="Loading your vault...">
        <div className="p-8">
          <LoadingState message="Fetching library media..." />
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title="Personal Media Library"
      subtitle="Canonical entertainment records and custom user editions stored in your personal vault (CAT-2)"
      action={
        <Link
          href="/movies"
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-500 rounded-full shadow-lg shadow-violet-600/30 transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add New Title</span>
        </Link>
      }
    >
      <div className="space-y-6">
        {/* Navigation Filters */}
        <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTab("ALL")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                tab === "ALL"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              All Media ({libraryMovies.length + librarySeries.length})
            </button>
            <button
              onClick={() => setTab("MOVIE")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                tab === "MOVIE"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              Feature Films ({libraryMovies.length})
            </button>
            <button
              onClick={() => setTab("TV_SERIES")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                tab === "TV_SERIES"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              TV Series ({librarySeries.length})
            </button>
          </div>
        </div>

        {/* Media Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {displayed.map((item) => (
            <Link
              key={item.id}
              href={`/movies/${item.id}`}
              className="group relative flex flex-col rounded-2xl overflow-hidden bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all p-3"
            >
              <div className="relative aspect-[2/3] w-full bg-zinc-950 rounded-xl overflow-hidden mb-2.5">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={item.poster_url || ""}
                  alt={item.canonical_title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute top-2 left-2 right-2 flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-zinc-950/80 backdrop-blur-md text-zinc-300 border border-zinc-800">
                    {item.content_type === "MOVIE" ? "Movie" : "Series"}
                  </span>
                  <span className="px-1.5 py-0.5 rounded-md text-[9px] font-mono bg-violet-600/30 text-violet-300 border border-violet-500/40">
                    4K
                  </span>
                </div>
              </div>

              <h4 className="text-xs font-bold text-zinc-100 group-hover:text-violet-400 transition-colors line-clamp-1">
                {item.canonical_title}
              </h4>
              <div className="flex items-center justify-between text-[11px] text-zinc-500 mt-1">
                <span>{item.production_year}</span>
                <span className="text-emerald-400 text-[10px]">Vault Verified</span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
