"use client";

import React, { useState, useEffect } from "react";
import { Film, Tv } from "lucide-react";
import { resolvePosterUrl } from "@/lib/media";
import { cn } from "@/lib/utils";

interface MediaPosterProps {
  src?: string | null;
  alt: string;
  contentType?: string;
  className?: string;
  imgClassName?: string;
  showTitleFallback?: boolean;
  loading?: "lazy" | "eager";
}

export const MediaPoster: React.FC<MediaPosterProps> = ({
  src,
  alt,
  contentType,
  className,
  imgClassName,
  showTitleFallback = true,
  loading = "lazy",
}) => {
  const [hasError, setHasError] = useState(false);
  const resolvedSrc = resolvePosterUrl(src);
  const isMovie = !contentType || contentType.toUpperCase() === "MOVIE";

  // Reset error state if src changes
  useEffect(() => {
    setHasError(false);
  }, [src]);

  if (resolvedSrc && !hasError) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={resolvedSrc}
        alt={alt}
        loading={loading}
        onError={() => setHasError(true)}
        className={cn("w-full h-full object-cover", imgClassName || className)}
      />
    );
  }

  return (
    <div
      className={cn(
        "w-full h-full flex flex-col items-center justify-center p-3 text-center bg-gradient-to-b from-zinc-900 via-zinc-900/90 to-zinc-950 text-zinc-600 select-none",
        className
      )}
      aria-label={alt}
    >
      {isMovie ? (
        <Film className="w-8 h-8 sm:w-10 sm:h-10 mb-2 opacity-40 text-zinc-400" aria-hidden="true" />
      ) : (
        <Tv className="w-8 h-8 sm:w-10 sm:h-10 mb-2 opacity-40 text-cyan-400" aria-hidden="true" />
      )}
      {showTitleFallback && (
        <span className="text-[10px] sm:text-[11px] font-mono text-zinc-400 opacity-90 line-clamp-2 px-1">
          {alt}
        </span>
      )}
    </div>
  );
};
