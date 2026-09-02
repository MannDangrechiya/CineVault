# CineVault OS — FastAPI Backend Production Dockerfile
# Multi-stage build (R1 fix): build-essential/libpq-dev previously lived in
# the single stage that was actually shipped to production, bloating the
# image and its attack surface with a full C toolchain nothing at runtime
# needs. They now exist only in the builder stage; the runtime stage copies
# the already-compiled packages, not the tools used to compile them.

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
# Installs into an isolated prefix so only the resulting compiled packages —
# not the build tools above — get copied into the runtime stage below.
RUN pip install --no-cache-dir --prefix=/install -r /app/requirements.txt


FROM python:3.12-slim AS runner

WORKDIR /app

COPY --from=builder /install /usr/local

# Only the source this service actually runs (R1 fix — previously `COPY . /app/`
# copied the entire monorepo into the image: apps/mobile, apps/web, docs/,
# tests/, .git, everything). services/api has no imports from packages/,
# apps/, or services/ai_worker (verified: no such imports anywhere in
# services/api), so this is everything it needs.
COPY services/api /app/services/api

# Create non-root user for security hardening
RUN useradd -m -u 1000 cinevault && chown -R cinevault:cinevault /app
USER cinevault

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# No curl/wget needed: urllib is already in the stdlib, so this adds zero
# extra packages to the runtime image.
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health/liveness', timeout=3).status == 200 else 1)"

# Run Uvicorn multi-worker production server with graceful shutdown
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--timeout-keep-alive", "65"]
