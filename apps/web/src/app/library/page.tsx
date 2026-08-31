"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import { getLibrary, removeFromLibrary } from "@/lib/api/personal";
import { LoadingState } from "@/components/ui/States";
import { Plus, Film as FilmIcon, ArrowRight, Trash2 } from "lucide-react";
import { MediaPoster } from "@/components/media/MediaPoster";

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
        {displayed.length === 0 ? (
          <div className="py-16 text-center rounded-2xl bg-zinc-900/20 border border-zinc-900 space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto text-zinc-600">
              <FilmIcon className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-zinc-200">Your Vault is Empty</h3>
            <p className="text-xs text-zinc-500 max-w-sm mx-auto">
              Explore the canonical catalog to add movies and series to your personal media library.
            </p>
            <div className="pt-2">
              <Link
                href="/movies"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 border border-violet-500/30 text-xs font-semibold transition-all"
              >
                <span>Browse Catalog</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {displayed.map((item) => {
              const isRemoving = removeMutation.isPending && removeMutation.variables === item.title_id;
              const isMovie = !item.content_type || item.content_type.toUpperCase() === "MOVIE";
              const detailUrl = isMovie ? `/movies/${item.title_id}` : `/series/${item.title_id}`;

              return (
                <div
                  key={item.id}
                  className={`group relative flex flex-col rounded-2xl overflow-hidden bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all p-3 ${
                    isRemoving ? "opacity-40 pointer-events-none" : ""
                  }`}
                >
                  <Link href={detailUrl} className="block">
                    <div className="relative aspect-[2/3] w-full bg-zinc-950 rounded-xl overflow-hidden mb-2.5">
                      <MediaPoster
                        src={item.poster_url}
                        alt={item.canonical_title}
                        contentType={item.content_type}
                        imgClassName="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                      <div className="absolute top-2 left-2 right-2 flex items-center justify-between pointer-events-none">
                        <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-zinc-950/80 backdrop-blur-md text-zinc-300 border border-zinc-800">
                          {isMovie ? "Movie" : "Series"}
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
                      href={detailUrl}
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
        )}
      </div>
    </PageContainer>
  );
}
