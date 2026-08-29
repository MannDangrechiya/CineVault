"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import {
  Calendar,
  Clock,
  ArrowRight,
  Trash2,
  Film,
  Tv,
  Sparkles,
} from "lucide-react";
import { getHistory, deleteHistoryItem } from "@/lib/api/personal";
import { EmptyState, ErrorState } from "@/components/ui/States";

function HistorySkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3, 4].map((n) => (
        <div
          key={n}
          className="p-4 rounded-2xl bg-zinc-900/30 border border-zinc-900 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-16 rounded-xl bg-zinc-800/60 shrink-0" />
            <div className="space-y-2">
              <div className="w-40 h-4 bg-zinc-800/60 rounded" />
              <div className="w-24 h-3 bg-zinc-800/40 rounded" />
            </div>
          </div>
          <div className="w-20 h-6 bg-zinc-800/40 rounded-full" />
        </div>
      ))}
    </div>
  );
}

export default function HistoryPage() {
  const [filter, setFilter] = useState<"ALL" | "MOVIE" | "TV_SERIES">("ALL");
  const queryClient = useQueryClient();

  const {
    data: historyData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["history", filter],
    queryFn: () =>
      // Initial view caps at the latest 10 events for a clean, uncluttered
      // timeline; `totalCount` below still reflects the true lifetime total.
      getHistory({
        type: filter === "ALL" ? undefined : filter,
        limit: 10,
        offset: 0,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteHistoryItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["history"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });

  const items = historyData?.items || [];
  const totalCount = historyData?.total ?? items.length;

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return isoString;
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <PageContainer
      title="Watch History"
      subtitle="Append-only timeline of viewing events, scrobbles, and playback sessions (CAT-2)"
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
        {/* Navigation Filters & Stats Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-zinc-900">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFilter("ALL")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                filter === "ALL"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              All Events ({totalCount})
            </button>
            <button
              onClick={() => setFilter("MOVIE")}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                filter === "MOVIE"
                  ? "bg-violet-600/15 text-violet-300 font-semibold border border-violet-500/30 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
              }`}
            >
              Movies
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

          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <Clock className="w-3.5 h-3.5 text-violet-400" />
            <span>{totalCount} Viewing Events Recorded</span>
          </div>
        </div>

        {/* Content Body */}
        {isLoading ? (
          <HistorySkeleton />
        ) : isError ? (
          <ErrorState
            title="Failed to Load History"
            description="Unable to connect to CineVault history API. Please try again."
            onAction={() => refetch()}
          />
        ) : items.length === 0 ? (
          <EmptyState
            title="No Viewing History Found"
            description="You haven't logged any watch events yet. Mark titles as watched or scrobble via media servers."
            actionLabel="Browse Movies Catalog"
            onAction={() => {
              window.location.href = "/movies";
            }}
          />
        ) : (
          <div className="space-y-3">
            {items.map((item) => {
              const poster =
                item.poster_url ||
                "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80";
              const isDeleting =
                deleteMutation.isPending && deleteMutation.variables === item.id;

              return (
                <div
                  key={item.id}
                  className={`p-4 rounded-2xl bg-zinc-900/40 hover:bg-zinc-900/70 border border-zinc-900 hover:border-zinc-800 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group ${
                    isDeleting ? "opacity-40 pointer-events-none" : ""
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <Link
                      href={`/movies/${item.title_id}`}
                      className="w-12 h-16 rounded-xl bg-zinc-950 overflow-hidden shrink-0 block border border-zinc-800"
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={poster}
                        alt={item.canonical_title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                    </Link>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/movies/${item.title_id}`}
                          className="text-xs sm:text-sm font-bold text-zinc-100 group-hover:text-violet-400 transition-colors"
                        >
                          {item.canonical_title}
                        </Link>
                        {item.production_year && (
                          <span className="text-[11px] text-zinc-500">
                            ({item.production_year})
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-500">
                        <span className="flex items-center gap-1 text-zinc-400">
                          <Calendar className="w-3 h-3 text-zinc-500" />
                          {formatDate(item.watched_at)}
                        </span>
                        {item.device_type && (
                          <>
                            <span>•</span>
                            <span className="text-zinc-400">{item.device_type}</span>
                          </>
                        )}
                        <span>•</span>
                        <span className="inline-flex items-center gap-1 text-zinc-400">
                          {item.content_type === "MOVIE" ? (
                            <Film className="w-3 h-3 text-violet-400" />
                          ) : (
                            <Tv className="w-3 h-3 text-emerald-400" />
                          )}
                          {item.content_type === "MOVIE" ? "Movie" : "Series"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 justify-between sm:justify-end shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-zinc-900">
                    {item.rating_value !== undefined && item.rating_value !== null && (
                      <div className="flex items-center gap-1 text-xs font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full">
                        <Sparkles className="w-3 h-3" />
                        <span>{item.rating_value} / 5</span>
                      </div>
                    )}

                    <Link
                      href={`/movies/${item.title_id}`}
                      className="inline-flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 font-medium px-2 py-1 rounded-lg hover:bg-violet-600/10 transition-colors"
                    >
                      <span>Details</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>

                    <button
                      onClick={() => deleteMutation.mutate(item.id)}
                      disabled={isDeleting}
                      title="Remove watch event"
                      className="p-2 rounded-xl text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
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
