"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search, Film, Tv, X } from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { TitleCard } from "@/components/catalog/TitleCard";
import { CatalogSkeleton } from "@/components/catalog/CatalogSkeleton";
import { getCatalogPage } from "@/lib/api/titles";
import { useDebounce } from "@/lib/use-debounce";
import type { CatalogPageResponse } from "@/lib/api/types";

const QUICK_SEARCH_TAGS = [
  "Parasite",
  "Inception",
  "The Dark Knight",
  "Interstellar",
  "Severance",
  "The Godfather",
  "RRR",
  "3 Idiots",
];

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialQuery = searchParams.get("q") || "";

  const [searchInput, setSearchInput] = useState(initialQuery);
  const [contentType, setContentType] = useState<"ALL" | "MOVIE" | "TV_SERIES">("ALL");

  const debouncedQuery = useDebounce(searchInput.trim(), 350);

  // Sync URL search params
  useEffect(() => {
    const params = new URLSearchParams();
    if (debouncedQuery) params.set("q", debouncedQuery);
    if (contentType !== "ALL") params.set("type", contentType);
    const queryString = params.toString();
    router.replace(`/search${queryString ? `?${queryString}` : ""}`, { scroll: false });
  }, [debouncedQuery, contentType, router]);

  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useQuery<CatalogPageResponse>({
    queryKey: ["search", debouncedQuery, contentType],
    queryFn: () =>
      getCatalogPage({
        query: debouncedQuery || undefined,
        content_type: contentType !== "ALL" ? contentType : undefined,
        limit: 30,
      }),
  });

  const results = data?.items || [];
  const totalCount = data?.total || 0;

  return (
    <div className="space-y-8">
      {/* Search Input Bar & Quick Filters */}
      <div className="space-y-4 max-w-4xl">
        <div className="relative">
          <label htmlFor="search-input" className="sr-only">
            Search titles, directors, genres, and display IDs
          </label>
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" aria-hidden="true" />
          <input
            id="search-input"
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search titles, directors, genres, display IDs (e.g. Parasite, MOV-000001)..."
            className="w-full pl-12 pr-12 py-3.5 rounded-2xl bg-zinc-900/60 border border-zinc-800 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all shadow-xl shadow-black/40"
            autoFocus
          />
          {searchInput && (
            <button
              type="button"
              onClick={() => setSearchInput("")}
              aria-label="Clear search"
              className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-zinc-400 hover:text-zinc-200 rounded-lg hover:bg-zinc-800 transition-colors"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          )}
        </div>

        {/* Filter Controls & Quick Tags */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          {/* Content Type Tabs */}
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-zinc-900/80 border border-zinc-800/80" role="tablist" aria-label="Content type filter">
            <button
              type="button"
              role="tab"
              aria-selected={contentType === "ALL"}
              onClick={() => setContentType("ALL")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                contentType === "ALL"
                  ? "bg-violet-600 text-white shadow-md shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              All Types
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={contentType === "MOVIE"}
              onClick={() => setContentType("MOVIE")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                contentType === "MOVIE"
                  ? "bg-violet-600 text-white shadow-md shadow-violet-600/30"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Film className="w-3.5 h-3.5" aria-hidden="true" />
              Movies
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={contentType === "TV_SERIES"}
              onClick={() => setContentType("TV_SERIES")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                contentType === "TV_SERIES"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Tv className="w-3.5 h-3.5" aria-hidden="true" />
              TV Series
            </button>
          </div>

          {/* Suggested Quick Searches */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-zinc-500 font-medium hidden sm:inline">Popular:</span>
            {QUICK_SEARCH_TAGS.slice(0, 5).map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => setSearchInput(tag)}
                className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-zinc-900/60 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results Header */}
      {debouncedQuery && !isLoading && !isError && (
        <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
          <p className="text-xs text-zinc-400">
            Found <span className="text-zinc-100 font-bold">{totalCount}</span> {totalCount === 1 ? "result" : "results"} for &ldquo;{debouncedQuery}&rdquo;
          </p>
        </div>
      )}

      {/* Main Results Grid */}
      {isLoading ? (
        <CatalogSkeleton />
      ) : isError ? (
        <ErrorState
          title="Search Failed"
          description="Unable to complete catalog search. Please verify your connection."
          onAction={() => refetch()}
        />
      ) : results.length === 0 ? (
        <EmptyState
          title={debouncedQuery ? "No Results Found" : "Discover the Entire CineVault Catalog"}
          description={
            debouncedQuery
              ? `No catalog titles matched "${debouncedQuery}". Try refining your keywords or checking spelling.`
              : "Type any title name, director, genre, or display ID above to explore rich canonical metadata."
          }
          actionLabel={debouncedQuery ? "Clear Search" : "Browse Popular Showcase"}
          onAction={() => {
            if (debouncedQuery) {
              setSearchInput("");
            } else {
              setSearchInput("Parasite");
            }
          }}
        />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {results.map((title) => (
            <TitleCard key={title.id} title={title} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <PageContainer
      title="Search & Discovery"
      subtitle="Instant unified search across canonical feature films, television series, and verified media metadata."
    >
      <Suspense fallback={<CatalogSkeleton />}>
        <SearchContent />
      </Suspense>
    </PageContainer>
  );
}
