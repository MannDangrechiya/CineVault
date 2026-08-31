"use client";

import React from "react";
import Link from "next/link";
import { Sparkles } from "lucide-react";
import { TitleSummary } from "@/lib/api/types";
import { MediaPoster } from "@/components/media/MediaPoster";

interface TitleCardProps {
  title: TitleSummary;
  matchScore?: number;
}

// Netflix/Letterboxd-style poster card: the poster is the whole card, no
// metadata footer competing for attention. Title, year, and match score only
// appear in a gradient scrim on hover, keeping the grid itself uncluttered.
export const TitleCard: React.FC<TitleCardProps> = ({ title, matchScore }) => {
  const isMovie = !title.content_type || title.content_type.toUpperCase() === "MOVIE";
  const detailUrl = isMovie ? `/movies/${title.id}` : `/series/${title.id || title.display_id}`;

  return (
    <Link
      href={detailUrl}
      className="group relative block aspect-[2/3] w-full rounded-2xl overflow-hidden border border-zinc-800/80 bg-zinc-950 transition-all duration-300 hover:scale-[1.03] hover:shadow-2xl hover:shadow-black/50 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
    >
      <MediaPoster
        src={title.poster_url}
        alt={title.canonical_title}
        contentType={title.content_type}
        imgClassName="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
      />

      {/* Hover reveal: dark gradient scrim + title, year, amber match badge */}
      <div className="absolute inset-0 flex flex-col justify-end p-3 bg-gradient-to-t from-black via-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
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
