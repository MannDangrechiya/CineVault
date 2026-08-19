"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Film, Tv, Calendar, Sparkles } from "lucide-react";
import { TitleSummary } from "@/lib/api/types";

interface TitleCardProps {
  title: TitleSummary;
  matchScore?: number;
}

export const TitleCard: React.FC<TitleCardProps> = ({ title, matchScore }) => {
  const [imageError, setImageError] = useState(false);
  const isMovie = title.content_type === "MOVIE";
  const detailUrl = isMovie ? `/movies/${title.id}` : `/series/${title.id || title.display_id}`;
  const showPoster = title.poster_url && !imageError;

  return (
    <Link
      href={detailUrl}
      className="group relative flex flex-col rounded-xl overflow-hidden transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-violet-500/20 focus:outline-none focus:ring-2 focus:ring-violet-500/50 bg-zinc-950"
    >
      {/* Artwork / Poster Box */}
      <div className="relative aspect-[2/3] w-full bg-zinc-900 rounded-xl overflow-hidden">
        {showPoster ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={title.poster_url!}
            alt={title.canonical_title}
            onError={() => setImageError(true)}
            className="w-full h-full object-cover rounded-xl transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-gradient-to-b from-zinc-900 to-zinc-950 text-zinc-600 rounded-xl">
            {isMovie ? (
              <Film className="w-10 h-10 mb-2 opacity-40 group-hover:text-violet-400 group-hover:opacity-100 transition-all duration-300" />
            ) : (
              <Tv className="w-10 h-10 mb-2 opacity-40 group-hover:text-cyan-400 group-hover:opacity-100 transition-all duration-300" />
            )}
            <span className="text-[11px] font-mono text-zinc-400 opacity-90 line-clamp-2 px-2">
              {title.canonical_title}
            </span>
          </div>
        )}

        {/* Ambient Gradient Overlay for text contrast */}
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-black/30 opacity-60 group-hover:opacity-40 transition-opacity pointer-events-none rounded-xl" />

        {/* Top Floating Badges */}
        <div className="absolute top-2 left-2 right-2 flex items-center justify-between pointer-events-none z-10">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wider uppercase bg-zinc-950/80 backdrop-blur-md text-zinc-300 border border-zinc-800/80 shadow-sm">
            {isMovie ? <Film className="w-2.5 h-2.5" /> : <Tv className="w-2.5 h-2.5" />}
            {isMovie ? "Movie" : "Series"}
          </span>

          {matchScore && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 backdrop-blur-md shadow-sm">
              <Sparkles className="w-2.5 h-2.5" />
              {matchScore}% Match
            </span>
          )}
        </div>
      </div>

      {/* Metadata Info Footer */}
      <div className="pt-2.5 pb-1 px-0.5 flex flex-col space-y-1">
        <h3 className="text-xs font-semibold text-zinc-100 group-hover:text-violet-400 transition-colors line-clamp-1">
          {title.canonical_title}
        </h3>

        <div className="flex items-center justify-between text-[11px] text-zinc-400 font-mono">
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3 text-zinc-500" />
            <span>{title.production_year || "—"}</span>
          </div>
          {title.origin_country && (
            <span className="text-[10px] text-zinc-500 uppercase">{title.origin_country}</span>
          )}
        </div>
      </div>
    </Link>
  );
};

