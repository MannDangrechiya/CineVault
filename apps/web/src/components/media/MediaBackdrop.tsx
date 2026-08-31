"use client";

import React, { useState, useEffect } from "react";
import { Film, Tv } from "lucide-react";
import { resolveBackdropUrl } from "@/lib/media";
import { cn } from "@/lib/utils";

interface MediaBackdropProps {
  src?: string | null;
  alt: string;
  contentType?: string;
  className?: string;
  imgClassName?: string;
  loading?: "lazy" | "eager";
}

export const MediaBackdrop: React.FC<MediaBackdropProps> = ({
  src,
  alt,
  contentType,
  className,
  imgClassName,
  loading = "lazy",
}) => {
  const [hasError, setHasError] = useState(false);
  const resolvedSrc = resolveBackdropUrl(src);
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
        className={cn(
          "w-full h-full object-cover object-center filter brightness-[0.75] contrast-[1.05]",
          imgClassName || className
        )}
      />
    );
  }

  return (
    <div
      className={cn(
        "w-full h-full bg-gradient-to-br from-zinc-900 via-zinc-950 to-black flex items-center justify-center select-none",
        className
      )}
      aria-label={alt}
    >
      {isMovie ? (
        <Film className="w-16 h-16 text-zinc-800" aria-hidden="true" />
      ) : (
        <Tv className="w-16 h-16 text-zinc-800" aria-hidden="true" />
      )}
    </div>
  );
};
