import React from "react";

/**
 * Shimmer skeleton cards matching the TitleCard 2:3 aspect ratio grid.
 * Uses the .shimmer CSS animation defined in globals.css.
 */
export const CatalogSkeleton: React.FC<{ count?: number }> = ({
  count = 12,
}) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex flex-col gap-2.5 animate-pulse">
          {/* Poster placeholder */}
          <div className="aspect-[2/3] rounded-xl bg-zinc-900 shimmer" />
          {/* Title text placeholder */}
          <div className="h-3 w-3/4 rounded bg-zinc-900 shimmer" />
          {/* Meta text placeholder */}
          <div className="h-2.5 w-1/2 rounded bg-zinc-900/60 shimmer" />
        </div>
      ))}
    </div>
  );
};
