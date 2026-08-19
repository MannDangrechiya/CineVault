"use client";

import React, { useState, useMemo } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { Search, X, SlidersHorizontal } from "lucide-react";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { CatalogSkeleton } from "@/components/catalog/CatalogSkeleton";
import { VirtualizedCatalogGrid } from "@/components/catalog/VirtualizedCatalogGrid";
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
  { value: "production_year,canonical_title", label: "Oldest First" },
  { value: "canonical_title", label: "Title A–Z" },
  { value: "-canonical_title", label: "Title Z–A" },
] as const;

export default function SeriesPage() {
  // ── Filter state ────────────────────────────────────────────────────
  const [searchInput, setSearchInput] = useState("");
  const [selectedGenre, setSelectedGenre] = useState("");
  const [selectedYear, setSelectedYear] = useState<number | undefined>();
  const [selectedSort, setSelectedSort] = useState<string>(SORT_OPTIONS[0].value);

  const debouncedQuery = useDebounce(searchInput, 400);

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
      "TV_SERIES",
      debouncedQuery,
      selectedGenre,
      selectedYear,
      selectedSort,
    ],
    queryFn: ({ pageParam }) =>
      getCatalogPage({
        content_type: "TV_SERIES",
        query: debouncedQuery || undefined,
        genre: selectedGenre || undefined,
        year: selectedYear,
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

  // ── Clear all filters ─────────────────────────────────────────────────
  const clearFilters = () => {
    setSearchInput("");
    setSelectedGenre("");
    setSelectedYear(undefined);
    setSelectedSort(SORT_OPTIONS[0].value);
  };

  return (
    <PageContainer
      title="TV Series Catalog"
      subtitle={
        !isLoading && !isError
          ? `${totalCount.toLocaleString()} series in catalog`
          : "Episodic title hierarchy, seasons, and episode tracking"
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
              placeholder="Search series, seasons, display IDs..."
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
              aria-label="Filter by year"
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
              aria-label="Sort catalog"
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
            title="Unable to Load TV Series Catalog"
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
            title="No TV Series Found"
            description={
              hasActiveFilters
                ? "No series match your current search and filter criteria. Try adjusting your filters."
                : "There are currently no TV series records in the catalog."
            }
            actionLabel={hasActiveFilters ? "Clear Filters" : undefined}
            onAction={hasActiveFilters ? clearFilters : undefined}
          />
        )}

        {/* ── Virtualized Title Grid ───────────────────────────────── */}
        {!isLoading && !isError && items.length > 0 && (
          <VirtualizedCatalogGrid
            items={items}
            hasNextPage={hasNextPage}
            isFetchingNextPage={isFetchingNextPage}
            fetchNextPage={fetchNextPage}
            totalCount={totalCount}
          />
        )}
      </div>
    </PageContainer>
  );
}

