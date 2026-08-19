"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import { useWindowVirtualizer } from "@tanstack/react-virtual";
import { Loader2, Film } from "lucide-react";
import { TitleCard } from "./TitleCard";
import type { TitleSummary } from "@/lib/api/types";

interface VirtualizedCatalogGridProps {
  items: TitleSummary[];
  hasNextPage?: boolean;
  isFetchingNextPage: boolean;
  fetchNextPage: () => void;
  totalCount: number;
}

function getColumnCount(width: number): number {
  if (width < 640) return 2;
  if (width < 768) return 3;
  if (width < 1024) return 4;
  if (width < 1280) return 5;
  return 6;
}

export const VirtualizedCatalogGrid: React.FC<VirtualizedCatalogGridProps> = ({
  items,
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
  totalCount,
}) => {
  const parentRef = useRef<HTMLDivElement>(null);
  const [columnCount, setColumnCount] = useState<number>(6);

  // Responsive column calculation
  useEffect(() => {
    const updateColumns = () => {
      if (typeof window !== "undefined") {
        setColumnCount(getColumnCount(window.innerWidth));
      }
    };

    updateColumns();
    window.addEventListener("resize", updateColumns);
    return () => window.removeEventListener("resize", updateColumns);
  }, []);

  const rowCount = Math.ceil(items.length / columnCount);

  const rowVirtualizer = useWindowVirtualizer({
    count: rowCount,
    estimateSize: useCallback(() => 340, []),
    overscan: 4,
    scrollMargin: parentRef.current?.offsetTop ?? 0,
  });

  const virtualRows = rowVirtualizer.getVirtualItems();

  // Infinite scroll trigger when reaching bottom virtual rows
  useEffect(() => {
    if (virtualRows.length === 0) return;
    const lastItem = virtualRows[virtualRows.length - 1];
    if (
      lastItem &&
      lastItem.index >= rowCount - 2 &&
      hasNextPage &&
      !isFetchingNextPage
    ) {
      fetchNextPage();
    }
  }, [virtualRows, rowCount, hasNextPage, isFetchingNextPage, fetchNextPage]);

  return (
    <div className="w-full">
      <div
        ref={parentRef}
        className="relative w-full"
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
        }}
      >
        {virtualRows.map((virtualRow) => {
          const startIndex = virtualRow.index * columnCount;
          const rowItems = items.slice(startIndex, startIndex + columnCount);

          return (
            <div
              key={virtualRow.key}
              data-index={virtualRow.index}
              ref={rowVirtualizer.measureElement}
              className="absolute top-0 left-0 w-full grid gap-4 pb-4"
              style={{
                transform: `translateY(${
                  virtualRow.start - (rowVirtualizer.options.scrollMargin || 0)
                }px)`,
                gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))`,
              }}
            >
              {rowItems.map((title, colIdx) => (
                <TitleCard
                  key={`${title.id}-${startIndex + colIdx}`}
                  title={title}
                />
              ))}
            </div>
          );
        })}
      </div>

      {/* Loading spinner for next page */}
      {isFetchingNextPage && (
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center gap-3 px-5 py-2.5 rounded-full bg-zinc-900/80 border border-zinc-800/60 shadow-lg">
            <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
            <span className="text-xs text-zinc-300 font-medium">
              Loading more titles…
            </span>
          </div>
        </div>
      )}

      {/* End of catalog */}
      {!hasNextPage && items.length > 0 && (
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Film className="w-3.5 h-3.5" />
            <span>
              Showing all {totalCount.toLocaleString()} titles
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
