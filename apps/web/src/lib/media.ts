// CineVault OS — Universal Media & Image URL Normalization Helper
// Ensures canonical URL resolution, protocol safety, provider relative-path resolution, and honest null fallback.

export const TMDB_POSTER_BASE = "https://image.tmdb.org/t/p/w500";
export const TMDB_BACKDROP_BASE = "https://image.tmdb.org/t/p/w1280";

// This module is imported by "use client" components (MediaPoster/
// MediaBackdrop), so only a NEXT_PUBLIC_-prefixed var is visible here — it's
// inlined into the client bundle at build time, unlike next.config.ts's
// server-only CDN_HOSTNAME which the standalone server re-reads at runtime
// start. See apps/web/Dockerfile (build ARG) and docker-compose.prod.yml
// (nextjs-web build.args) for how the real value reaches this build. Left
// undefined, the HTTP->HTTPS upgrade below simply never matches a CDN host —
// a safe no-op, not a hardcoded domain.
const CDN_HOSTNAME = process.env.NEXT_PUBLIC_CDN_HOSTNAME;

export type MediaType = "poster" | "backdrop" | "avatar";

/**
 * Normalizes any media/image URL or relative provider path.
 * 
 * Rules:
 * - null / undefined / empty / "null" / "none" -> returns null
 * - Local asset paths starting with "/assets/" or "/images/" -> returns path as-is
 * - Full HTTPS URLs -> returns URL as-is
 * - Full HTTP URLs -> upgraded to HTTPS where appropriate
 * - Provider-relative paths (e.g. "/abc123.jpg" or "abc123.jpg") -> resolved to TMDB / CDN base
 */
export function resolveMediaUrl(
  url?: string | null,
  type: MediaType = "poster"
): string | null {
  if (!url) return null;

  const trimmed = url.trim();
  if (
    !trimmed ||
    trimmed.toLowerCase() === "null" ||
    trimmed.toLowerCase() === "none" ||
    trimmed.toLowerCase() === "undefined" ||
    trimmed.toLowerCase().includes("images.unsplash.com")
  ) {
    return null;
  }

  // 1. Local Next.js public assets
  if (trimmed.startsWith("/assets/") || trimmed.startsWith("/images/") || trimmed.startsWith("/icons/")) {
    return trimmed;
  }

  // 2. Absolute URLs
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    try {
      const parsed = new URL(trimmed);
      // Upgrade HTTP for known CDNs to prevent mixed-content blocking
      if (
        parsed.protocol === "http:" &&
        (parsed.hostname === "image.tmdb.org" ||
          parsed.hostname === "m.media-amazon.com" ||
          (!!CDN_HOSTNAME && parsed.hostname === CDN_HOSTNAME))
      ) {
        return `https://${parsed.host}${parsed.pathname}${parsed.search}`;
      }
      return trimmed;
    } catch {
      return null;
    }
  }

  // 3. Provider-relative path (e.g. "/1XddXPXbAh2g2Ur5KNvV26C5W.jpg")
  const path = trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  const base = type === "backdrop" ? TMDB_BACKDROP_BASE : TMDB_POSTER_BASE;
  return `${base}${path}`;
}

export function resolvePosterUrl(url?: string | null): string | null {
  return resolveMediaUrl(url, "poster");
}

export function resolveBackdropUrl(url?: string | null): string | null {
  return resolveMediaUrl(url, "backdrop");
}

export function resolveAvatarUrl(url?: string | null): string | null {
  return resolveMediaUrl(url, "avatar");
}
