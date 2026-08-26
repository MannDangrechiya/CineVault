"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import { Plus, Film as FilmIcon, Tv as TvIcon, Trash2, ArrowRight } from "lucide-react";
import { getLibrary, removeFromLibrary } from "@/lib/api/personal";
import { LoadingState } from "@/components/ui/States";

export default function LibraryPage() {
  const [tab, setTab] = useState<"ALL" | "MOVIE" | "TV_SERIES">("ALL");
  const queryClient = useQueryClient();

  // Real per-user library data (personal.library_entry), not the general catalog --
  // a brand-new user correctly sees an empty library here (no fabricated fallback).
  const { data: moviesRes, isLoading: isLoadingMovies } = useQuery({
    queryKey: ["library", "movies"],
    queryFn: () => getLibrary({ type: "MOVIE", limit: 100 }),
  });

  const { data: seriesRes, isLoading: isLoadingSeries } = useQuery({
    queryKey: ["library", "series"],
    queryFn: () => getLibrary({ type: "TV_SERIES", limit: 100 }),
  });

  // removeFromLibrary existed in the API client but nothing in the UI ever
  // called it -- there was no way to remove a title from your library once
  // added, same gap as the missing "Add to Library" button fixed elsewhere
  // this session.
  const removeMutation = useMutation({
    mutationFn: removeFromLibrary,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["library"] });
    },
  });

  const libraryMovies = moviesRes?.items || [];
  const librarySeries = seriesRes?.items || [];

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
          {displayed.map((item) => {
            const isRemoving = removeMutation.isPending && removeMutation.variables === item.title_id;
            return (
              <div
                key={item.id}
                className={`group relative flex flex-col rounded-2xl overflow-hidden bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all p-3 ${
                  isRemoving ? "opacity-40 pointer-events-none" : ""
                }`}
              >
                <Link href={`/movies/${item.title_id}`} className="block">
                  <div className="relative aspect-[2/3] w-full bg-zinc-950 rounded-xl overflow-hidden mb-2.5">
                    {item.poster_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={item.poster_url}
                        alt={item.canonical_title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-zinc-900 to-zinc-950 text-zinc-700">
                        {item.content_type === "MOVIE" ? (
                          <FilmIcon className="w-8 h-8" />
                        ) : (
                          <TvIcon className="w-8 h-8" />
                        )}
                      </div>
                    )}
                    <div className="absolute top-2 left-2 right-2 flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-zinc-950/80 backdrop-blur-md text-zinc-300 border border-zinc-800">
                        {item.content_type === "MOVIE" ? "Movie" : "Series"}
                      </span>
                    </div>
                  </div>

                  <h4 className="text-xs font-bold text-zinc-100 group-hover:text-violet-400 transition-colors line-clamp-1">
                    {item.canonical_title}
                  </h4>
                  <div className="flex items-center justify-between text-[11px] text-zinc-500 mt-1">
                    <span>{item.production_year}</span>
                  </div>
                </Link>

                <div className="flex items-center justify-between pt-2.5 mt-2.5 border-t border-zinc-900/80">
                  <Link
                    href={`/movies/${item.title_id}`}
                    className="text-[10px] text-violet-400 hover:text-violet-300 font-medium inline-flex items-center gap-1"
                  >
                    <span>View</span>
                    <ArrowRight className="w-2.5 h-2.5" />
                  </Link>
                  <button
                    onClick={() => removeMutation.mutate(item.title_id)}
                    disabled={removeMutation.isPending}
                    title="Remove from Library"
                    className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-zinc-800/80 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </PageContainer>
  );
}
