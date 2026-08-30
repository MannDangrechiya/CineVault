"use client";

import React, { useState } from "react";
import { Search, X, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GenreSummary } from "@/lib/api/types";

export interface SortOption {
  value: string;
  label: string;
}

interface CatalogFilterBarProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder: string;
  genres: GenreSummary[];
  selectedGenre: string;
  onGenreChange: (name: string) => void;
  yearOptions: number[];
  selectedYear?: number;
  onYearChange: (year: number | undefined) => void;
  sortOptions: readonly SortOption[];
  selectedSort: string;
  onSortChange: (value: string) => void;
  hasActiveFilters: boolean;
  onClearFilters: () => void;
}

// Single-row search + sort header, with genre/year filters tucked behind a
// collapsible drawer -- keeps the default view uncluttered while leaving
// every control fully functional.
export const CatalogFilterBar: React.FC<CatalogFilterBarProps> = ({
  searchValue,
  onSearchChange,
  searchPlaceholder,
  genres,
  selectedGenre,
  onGenreChange,
  yearOptions,
  selectedYear,
  onYearChange,
  sortOptions,
  selectedSort,
  onSortChange,
  hasActiveFilters,
  onClearFilters,
}) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const advancedFilterCount = (selectedGenre ? 1 : 0) + (selectedYear ? 1 : 0);

  return (
    <div className="space-y-0">
      {/* Single-row header: search, sort, advanced filters toggle */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px] max-w-xl">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
            <Search className="w-4 h-4" />
          </div>
          <input
            id="catalog-search"
            type="text"
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full pl-10 pr-10 py-2.5 text-sm bg-zinc-900/60 border border-zinc-800/80 rounded-xl text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/30 transition-all"
          />
          {searchValue && (
            <button
              onClick={() => onSearchChange("")}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <select
          id="catalog-sort"
          aria-label="Sort catalog"
          value={selectedSort}
          onChange={(e) => onSortChange(e.target.value)}
          className="px-3 py-2.5 text-xs bg-zinc-900/60 border border-zinc-800/80 rounded-xl text-zinc-300 focus:outline-none focus:border-violet-500/50 cursor-pointer appearance-none"
        >
          {sortOptions.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>

        <button
          onClick={() => setDrawerOpen((prev) => !prev)}
          aria-expanded={drawerOpen}
          className={cn(
            "inline-flex items-center gap-1.5 px-3.5 py-2.5 text-xs font-medium rounded-xl border transition-all cursor-pointer",
            drawerOpen || advancedFilterCount > 0
              ? "bg-violet-600/15 border-violet-500/40 text-violet-300"
              : "bg-zinc-900/60 border-zinc-800/80 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300"
          )}
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          <span>Filters</span>
          {advancedFilterCount > 0 && (
            <span className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-violet-500 text-white text-[10px] font-bold">
              {advancedFilterCount}
            </span>
          )}
        </button>

        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-full hover:bg-rose-500/20 transition-all cursor-pointer"
          >
            <X className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      {/* Advanced filters drawer: genre pills + year, collapsed by default */}
      <div
        className={cn(
          "grid transition-all duration-300 ease-in-out",
          drawerOpen ? "grid-rows-[1fr] opacity-100 mt-4" : "grid-rows-[0fr] opacity-0"
        )}
      >
        <div className="overflow-hidden">
          <div className="flex flex-wrap items-center gap-3 p-4 rounded-xl bg-zinc-900/40 border border-zinc-800/60">
            <div className="flex flex-wrap gap-1.5">
              {genres.map((g) => (
                <button
                  key={g.genre_id}
                  onClick={() => onGenreChange(selectedGenre === g.name ? "" : g.name)}
                  className={cn(
                    "px-3 py-1 text-xs font-medium rounded-full border transition-all cursor-pointer",
                    selectedGenre === g.name
                      ? "bg-violet-600/20 border-violet-500/40 text-violet-300"
                      : "bg-zinc-950/60 border-zinc-800/60 text-zinc-400 hover:border-zinc-700 hover:text-zinc-300"
                  )}
                >
                  {g.name}
                </button>
              ))}
            </div>

            <select
              aria-label="Filter by year"
              value={selectedYear ?? ""}
              onChange={(e) => onYearChange(e.target.value ? Number(e.target.value) : undefined)}
              className="px-3 py-1.5 text-xs bg-zinc-950/60 border border-zinc-800/60 rounded-lg text-zinc-300 focus:outline-none focus:border-violet-500/50 cursor-pointer appearance-none"
            >
              <option value="">All Years</option>
              {yearOptions.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};
