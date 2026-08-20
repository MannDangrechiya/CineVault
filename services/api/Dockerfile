# CineVault OS — FastAPI Backend Production Dockerfile
FROM python:3.12-slim AS runner

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application sources
COPY . /app/

# Create non-root user for security hardening
RUN useradd -m -u 1000 cinevault && chown -R cinevault:cinevault /app
USER cinevault

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Run Uvicorn multi-worker production server with graceful shutdown
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--timeout-keep-alive", "65"]
