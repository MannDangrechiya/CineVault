"use client";

import React, { useState, useMemo } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { PageContainer } from "@/components/ui/PageContainer";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { CatalogSkeleton } from "@/components/catalog/CatalogSkeleton";
import { VirtualizedCatalogGrid } from "@/components/catalog/VirtualizedCatalogGrid";
import { CatalogFilterBar } from "@/components/catalog/CatalogFilterBar";
import { getCatalogPage, getGenres } from "@/lib/api/titles";
import { useDebounce } from "@/lib/use-debounce";
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
      <div className="space-y-8">
        {/* ── Search & Filters Bar ──────────────────────────────────── */}
        <CatalogFilterBar
          searchValue={searchInput}
          onSearchChange={setSearchInput}
          searchPlaceholder="Search series, seasons, display IDs..."
          genres={genres}
          selectedGenre={selectedGenre}
          onGenreChange={setSelectedGenre}
          yearOptions={YEAR_OPTIONS}
          selectedYear={selectedYear}
          onYearChange={setSelectedYear}
          sortOptions={SORT_OPTIONS}
          selectedSort={selectedSort}
          onSortChange={setSelectedSort}
          hasActiveFilters={hasActiveFilters}
          onClearFilters={clearFilters}
        />

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

