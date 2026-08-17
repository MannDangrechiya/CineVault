"use client";

import React, { useState, useMemo } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useInView } from "react-intersection-observer";
import { Search, X, SlidersHorizontal, Loader2, Film } from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { TitleCard } from "@/components/catalog/TitleCard";
import { CatalogSkeleton } from "@/components/catalog/CatalogSkeleton";
import { getCatalogPage, getGenres } from "@/lib/api/titles";
import { useDebounce } from "@/lib/use-debounce";
import { cn } from "@/lib/utils";
import type { CatalogPageResponse } from "@/lib/api/types";

// ── Year range for filter dropdown ──────────────────────────────────────
const currentYear = new Date().getFullYear();
const YEAR_OPTIONS = Array.from(
  { length: currentYear - 1919 },
  (_, i) => currentYear - i
);

// ── Sort options ────────────────────────────────────────────────────────
const SORT_OPTIONS = [
  { value: "-production_year,canonical_title", label: "Newest First" },
  { value: "canonical_title", label: "Title A–Z" },
] as const;

export default function MoviesPage() {
  // ── Filter state ────────────────────────────────────────────────────
  const [searchInput, setSearchInput] = useState("");
  const [selectedGenre, setSelectedGenre] = useState("");
  const [selectedYear, setSelectedYear] = useState<number | undefined>();
  const [selectedSort, setSelectedSort] = useState<string>(SORT_OPTIONS[0].value);

  const debouncedQuery = useDebounce(searchInput, 500);

  const hasActiveFilters =
    !!debouncedQuery || !!selectedGenre || !!selectedYear;

  // ── Fetch genres ──────────────────────────────────────────────────────
  const { data: genres = [] } = useQuery({
    queryKey: ["genres"],
    queryFn: getGenres,
    staleTime: Infinity,
  });

  // ── Infinite scroll query ─────────────────────────────────────────────
  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useInfiniteQuery<CatalogPageResponse>({
    queryKey: [
      "catalog",
      debouncedQuery,
      selectedGenre,
      selectedYear,
      selectedSort,
    ],
    queryFn: ({ pageParam }) =>
      getCatalogPage({
        q: debouncedQuery || undefined,
        genre: selectedGenre || undefined,
        production_year: selectedYear,
        sort: selectedSort,
        limit: 24,
        offset: pageParam as number,
      }),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.next_offset ?? undefined,
  });

  // ── Flatten pages into a single items array ───────────────────────────
  const items = useMemo(
    () => data?.pages.flatMap((p) => p.items) ?? [],
    [data]
  );
  const totalCount = data?.pages[0]?.total ?? 0;

  // ── Intersection observer for scroll sentinel ─────────────────────────
  const { ref: sentinelRef } = useInView({
    threshold: 0,
    rootMargin: "400px",
    onChange: (inView) => {
      if (inView && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
  });

  // ── Clear all filters ─────────────────────────────────────────────────
  const clearFilters = () => {
    setSearchInput("");
    setSelectedGenre("");
    setSelectedYear(undefined);
    setSelectedSort(SORT_OPTIONS[0].value);
  };

  return (
    <PageContainer
      title="Movies Catalog"
      subtitle={
        !isLoading && !isError
          ? `${totalCount.toLocaleString()} title${totalCount !== 1 ? "s" : ""} in catalog`
          : "Browsing canonical feature films and series"
      }
    >
      <div className="space-y-6">
        {/* ── Search & Filters Bar ──────────────────────────────────── */}
        <div className="space-y-4">
          {/* Search input */}
          <div className="relative max-w-xl">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
              <Search className="w-4 h-4" />
            </div>
            <input
              id="catalog-search"
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search titles, synopses, directors..."
              className="w-full pl-10 pr-10 py-2.5 text-sm bg-zinc-900/60 border border-zinc-800/80 rounded-xl text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/30 transition-all"
            />
            {searchInput && (
              <button
                onClick={() => setSearchInput("")}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Filters row */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-zinc-500">
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Filters</span>
            </div>

            {/* Genre pills */}
            <div className="flex flex-wrap gap-1.5">
              {genres.map((g) => (
                <button
                  key={g.genre_id}
                  onClick={() =>
                    setSelectedGenre(
                      selectedGenre === g.name ? "" : g.name
                    )
                  }
                  className={cn(
                    "px-3 py-1 text-xs font-medium rounded-full border transition-all cursor-pointer",
                    selectedGenre === g.name
                      ? "bg-violet-600/20 border-violet-500/40 text-violet-300"
                      : "bg-zinc-900/60 border-zinc-800/60 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300"
                  )}
                >
                  {g.name}
                </button>
              ))}
            </div>

            {/* Year dropdown */}
            <select
              id="catalog-year-filter"
              value={selectedYear ?? ""}
              onChange={(e) =>
                setSelectedYear(
                  e.target.value ? Number(e.target.value) : undefined
                )
              }
              className="px-3 py-1.5 text-xs bg-zinc-900/60 border border-zinc-800/60 rounded-lg text-zinc-300 focus:outline-none focus:border-violet-500/50 cursor-pointer appearance-none"
            >
              <option value="">All Years</option>
              {YEAR_OPTIONS.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>

            {/* Sort dropdown */}
            <select
              id="catalog-sort"
              value={selectedSort}
              onChange={(e) => setSelectedSort(e.target.value)}
              className="px-3 py-1.5 text-xs bg-zinc-900/60 border border-zinc-800/60 rounded-lg text-zinc-300 focus:outline-none focus:border-violet-500/50 cursor-pointer appearance-none"
            >
              {SORT_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>

            {/* Clear filters */}
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-full hover:bg-rose-500/20 transition-all cursor-pointer"
              >
                <X className="w-3 h-3" />
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {/* ── Loading skeleton (initial load) ──────────────────────── */}
        {isLoading && <CatalogSkeleton count={24} />}

        {/* ── Error state ──────────────────────────────────────────── */}
        {isError && (
          <ErrorState
            title="Unable to Load Catalog"
            description={
              error instanceof Error
                ? error.message
                : "Failed to connect to CineVault backend."
            }
            onAction={() => refetch()}
          />
        )}

        {/* ── Empty state ──────────────────────────────────────────── */}
        {!isLoading && !isError && items.length === 0 && (
          <EmptyState
            title="No Titles Found"
            description={
              hasActiveFilters
                ? "No titles match your current search and filter criteria. Try adjusting your filters."
                : "The catalog is empty. Ingest titles to populate the catalog."
            }
            actionLabel={hasActiveFilters ? "Clear Filters" : undefined}
            onAction={hasActiveFilters ? clearFilters : undefined}
          />
        )}

        {/* ── Title grid ───────────────────────────────────────────── */}
        {!isLoading && !isError && items.length > 0 && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {items.map((title, idx) => (
                <TitleCard key={`${title.id}-${idx}`} title={title} />
              ))}
            </div>

            {/* Scroll sentinel — triggers next page fetch */}
            <div ref={sentinelRef} className="h-px" />

            {/* Loading spinner for next page */}
            {isFetchingNextPage && (
              <div className="flex items-center justify-center py-8">
                <div className="flex items-center gap-3 px-5 py-2.5 rounded-full bg-zinc-900/60 border border-zinc-800/50">
                  <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                  <span className="text-xs text-zinc-400 font-medium">
                    Loading more titles…
                  </span>
                </div>
              </div>
            )}

            {/* End of catalog */}
            {!hasNextPage && items.length > 0 && (
              <div className="flex items-center justify-center py-8">
                <div className="flex items-center gap-2 text-xs text-zinc-600">
                  <Film className="w-3.5 h-3.5" />
                  <span>
                    Showing all {totalCount.toLocaleString()} titles
                  </span>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </PageContainer>
  );
}
