# CineVault OS — Next.js 15 Web Frontend Production Multi-Stage Dockerfile
FROM node:20-alpine AS base

# Stage 1: Dependencies
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci || npm install

# Stage 2: Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
# next.config.ts only emits the standalone server (.next/standalone) when this
# is "true" (see apps/web/next.config.ts) — added so plain `npm run build`
# (CI/local) stays non-standalone, but never set here, so this image's build
# always produced a `.next` directory with no `standalone/` subfolder for the
# runner stage's COPY below to find. Production-build-only: harmless for the
# CI/local `npm run build` path since that never sets it.
ENV BUILD_STANDALONE=true

# CDN_HOSTNAME must be known at BUILD time, not just container-runtime start.
# Verified against the actual built image (R1 hardening pass): Next.js
# resolves next.config.ts's `images.remotePatterns` during `next build` and
# freezes the result into .next/required-server-files.json — the standalone
# server.js loads that frozen JSON at boot, it does not re-read
# process.env.CDN_HOSTNAME at that point. (Confirmed by building once with
# CDN_HOSTNAME unset, then starting that image with a *different*
# CDN_HOSTNAME at `docker run` time: the image optimizer still enforced the
# build-time value, not the runtime one.) NEXT_PUBLIC_CDN_HOSTNAME is
# separately required because it's inlined into the client JS bundle
# (apps/web/src/lib/media.ts) — same build-time constraint, different
# mechanism. Both are set from the one ARG below; passed from
# docker-compose.prod.yml's `build.args`, which reads the same CDN_HOSTNAME
# the rest of the stack uses. Optional: unset, `next build` still succeeds
# (see next.config.ts's unroutable placeholder fallback) — it just means
# production would silently reject real CDN images, which is caught instead
# by CDN_HOSTNAME being a required (":?") build arg in docker-compose.prod.yml.
ARG CDN_HOSTNAME
ENV CDN_HOSTNAME=${CDN_HOSTNAME}
ENV NEXT_PUBLIC_CDN_HOSTNAME=${CDN_HOSTNAME}

RUN npm run build

# Stage 3: Production Runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
