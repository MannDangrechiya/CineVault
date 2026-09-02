import type { NextConfig } from "next";

// CDN_HOSTNAME must be set at BUILD time (see apps/web/Dockerfile's ARG
// CDN_HOSTNAME and docker-compose.prod.yml's nextjs-web build.args) — NOT
// just as a container-runtime env var. Verified against the actual built
// image (R1 hardening pass): Next.js resolves `images.remotePatterns` during
// `next build` and freezes the result into
// .next/required-server-files.json; the standalone server.js loads that
// frozen JSON at boot and does not re-evaluate this file or re-read
// process.env.CDN_HOSTNAME at that point. (Confirmed empirically: an image
// built with CDN_HOSTNAME unset, then started with a *different*
// CDN_HOSTNAME at `docker run` time, still enforced the build-time value —
// requests for the runtime-only host were rejected.) The unroutable
// "cdn.invalid.example" fallback (RFC 2606 .invalid TLD) only exists so a
// plain `npm run build`/`next build` with no CDN_HOSTNAME set (CI, local
// dev) still succeeds — it is never the value actually enforced in a real
// production image, since docker-compose.prod.yml requires CDN_HOSTNAME as a
// build arg there.
const cdnHostname = process.env.CDN_HOSTNAME || "cdn.invalid.example";

const nextConfig: NextConfig = {
  output: process.env.BUILD_STANDALONE === "true" ? "standalone" : undefined,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "image.tmdb.org",
        pathname: "/t/p/**",
      },
      {
        protocol: "https",
        hostname: "m.media-amazon.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: cdnHostname,
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "cdn.myanimelist.net",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "images.unsplash.com",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
