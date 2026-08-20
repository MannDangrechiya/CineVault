# CineVault OS — Dedicated Celery AI Worker Dockerfile (Production)
FROM python:3.12-slim AS runner

WORKDIR /app

# Install system utilities and cleanup cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/ai_worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application sources
COPY . /app/

# Create and switch to non-root user for security hardening
RUN useradd -m -u 1000 cinevault && chown -R cinevault:cinevault /app
USER cinevault

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run Celery worker daemon
CMD ["celery", "-A", "services.ai_worker.worker.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
