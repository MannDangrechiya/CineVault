import React from "react";

/**
 * Shimmer skeleton cards matching the TitleCard 2:3 poster-only card --
 * no separate title/meta placeholders below, since TitleCard no longer
 * renders a text footer (title/year now only appear in the hover scrim).
 * Uses the .shimmer CSS animation defined in globals.css.
 */
export const CatalogSkeleton: React.FC<{ count?: number }> = ({
  count = 12,
}) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="aspect-[2/3] rounded-2xl border border-zinc-800/80 bg-zinc-900 shimmer animate-pulse"
        />
      ))}
    </div>
  );
};
