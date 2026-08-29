"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Film, Tv, Sparkles } from "lucide-react";
import { TitleSummary } from "@/lib/api/types";

interface TitleCardProps {
  title: TitleSummary;
  matchScore?: number;
}

// Netflix/Letterboxd-style poster card: the poster is the whole card, no
// metadata footer competing for attention. Title, year, and match score only
// appear in a gradient scrim on hover, keeping the grid itself uncluttered.
export const TitleCard: React.FC<TitleCardProps> = ({ title, matchScore }) => {
  const [imageError, setImageError] = useState(false);
  const isMovie = title.content_type === "MOVIE";
  const detailUrl = isMovie ? `/movies/${title.id}` : `/series/${title.id || title.display_id}`;
  const showPoster = title.poster_url && !imageError;

  return (
    <Link
      href={detailUrl}
      className="group relative block aspect-[2/3] w-full rounded-2xl overflow-hidden border border-zinc-800/80 bg-zinc-950 transition-all duration-300 hover:scale-[1.03] hover:shadow-2xl hover:shadow-black/50 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
    >
      {showPoster ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={title.poster_url!}
          alt={title.canonical_title}
          onError={() => setImageError(true)}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          loading="lazy"
        />
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-gradient-to-b from-zinc-900 to-zinc-950 text-zinc-600">
          {isMovie ? (
            <Film className="w-10 h-10 mb-2 opacity-40" />
          ) : (
            <Tv className="w-10 h-10 mb-2 opacity-40" />
          )}
          <span className="text-[11px] font-mono text-zinc-400 opacity-90 line-clamp-2 px-2">
            {title.canonical_title}
          </span>
        </div>
      )}

      {/* Hover reveal: dark gradient scrim + title, year, amber match badge */}
      <div className="absolute inset-0 flex flex-col justify-end p-3 bg-gradient-to-t from-black via-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        {matchScore !== undefined && (
          <span className="self-start mb-1.5 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 backdrop-blur-sm">
            <Sparkles className="w-2.5 h-2.5" />
            {matchScore}% Match
          </span>
        )}
        <h3 className="text-xs font-semibold text-white line-clamp-2">{title.canonical_title}</h3>
        <span className="text-[11px] text-zinc-300 mt-0.5">{title.production_year || "—"}</span>
      </div>
    </Link>
  );
};
