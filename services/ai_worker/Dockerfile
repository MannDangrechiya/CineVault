# CineVault OS — Dedicated Celery AI Worker Dockerfile (Production)
# Multi-stage build (R1 fix): build-essential/libpq-dev previously lived in
# the single stage that was actually shipped to production. They now exist
# only in the builder stage; the runtime stage copies the already-compiled
# packages, not the tools used to compile them.

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY services/ai_worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /app/requirements.txt


FROM python:3.12-slim AS runner

WORKDIR /app

COPY --from=builder /install /usr/local

# Only the source this service actually runs (R1 fix — previously `COPY . /app/`
# copied the entire monorepo into the image). services/ai_worker has no
# imports from packages/, apps/, or services/api (verified).
COPY services/ai_worker /app/services/ai_worker

# Create and switch to non-root user for security hardening
RUN useradd -m -u 1000 cinevault && chown -R cinevault:cinevault /app
USER cinevault

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# No HTTP server here (Celery worker, no listening port). `celery inspect
# ping` would be the natural healthcheck (round-trips through the real
# broker connection) but is NOT usable here: confirmed live against this
# project's actual rabbitmq:4-management-alpine broker, `celery inspect`
# itself fails with "Feature `transient_nonexcl_queues` is deprecated" —
# the same RabbitMQ 4.x incompatibility that made worker_enable_remote_
# control=False necessary in worker.py (see the comment there). This is a
# process-liveness check instead: confirms the celery worker process
# itself is still running (catches the crash-loop this investigation
# found), not full broker round-trip health. No extra packages needed —
# reads /proc directly, works in this minimal image without procps/curl.
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import os,sys; sys.exit(0 if any(b'celery' in open(f'/proc/{p}/cmdline','rb').read() for p in os.listdir('/proc') if p.isdigit()) else 1)"

# Run Celery worker daemon. --without-mingle/--without-gossip/--without-
# heartbeat: see the worker_enable_remote_control comment in worker.py —
# these skip the same broken RabbitMQ 4.x queue declaration from the
# worker-command side (mingle's startup "hello" broadcast uses the pidbox
# mechanism internally regardless of the remote-control setting).
CMD ["celery", "-A", "services.ai_worker.worker.celery_app", "worker", "--loglevel=info", "--concurrency=4", "--without-mingle", "--without-gossip", "--without-heartbeat"]
