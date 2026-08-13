import React from "react";
import { Film, Tv, Calendar, Tag } from "lucide-react";
import { TitleSummary } from "@/lib/api/types";

interface TitleCardProps {
  title: TitleSummary;
}

export const TitleCard: React.FC<TitleCardProps> = ({ title }) => {
  const isMovie = title.content_type === "MOVIE";

  return (
    <div className="group relative rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-violet-500/50 transition-all duration-300 overflow-hidden flex flex-col hover:shadow-lg hover:shadow-violet-950/20">
      {/* Artwork / Poster Aspect Box */}
      <div className="relative aspect-[2/3] w-full bg-slate-950 flex items-center justify-center overflow-hidden">
        {title.poster_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={title.poster_url}
            alt={title.canonical_title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-4 text-center text-slate-600">
            {isMovie ? (
              <Film className="w-10 h-10 mb-2 opacity-40 group-hover:text-violet-400 group-hover:opacity-100 transition-all" />
            ) : (
              <Tv className="w-10 h-10 mb-2 opacity-40 group-hover:text-cyan-400 group-hover:opacity-100 transition-all" />
            )}
            <span className="text-xs font-mono opacity-50">{title.display_id}</span>
          </div>
        )}

        {/* Content Type Badge */}
        <div className="absolute top-2.5 left-2.5 z-10">
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold tracking-wider uppercase border backdrop-blur-md ${
              isMovie
                ? "bg-violet-950/80 text-violet-300 border-violet-700/50"
                : "bg-cyan-950/80 text-cyan-300 border-cyan-700/50"
            }`}
          >
            {isMovie ? <Film className="w-2.5 h-2.5" /> : <Tv className="w-2.5 h-2.5" />}
            {title.content_type}
          </span>
        </div>
      </div>

      {/* Title Card Details */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 group-hover:text-violet-300 transition-colors line-clamp-1">
            {title.canonical_title}
          </h3>
          {title.original_title && title.original_title !== title.canonical_title && (
            <p className="text-xs text-slate-400 line-clamp-1 italic mt-0.5">
              {title.original_title}
            </p>
          )}
        </div>

        <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60 font-mono">
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3 text-slate-500" />
            <span>{title.production_year || "N/A"}</span>
          </div>
          <div className="flex items-center gap-1">
            <Tag className="w-3 h-3 text-slate-500" />
            <span className="text-[11px] text-slate-400">{title.display_id}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
