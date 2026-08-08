# CineVault OS — Master API Service Foundation
# Main FastAPI application entrypoint implementing OpenAPI 3.1 & Phase 3 Gateway Boundary

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .config import config
from .errors import APIError, api_error_handler, http_exception_handler, validation_exception_handler, unhandled_exception_handler
from .telemetry import CorrelationAndMetricsMiddleware, logger
from .routers import (
    health,
    titles,
    search,
    personal,
    sync,
    internal,
    metrics
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CineVault OS API Service Foundation...")
    logger.info(f"Environment: {config.environment} | PgBouncer: {config.pgbouncer_host}:{config.pgbouncer_port} | Valkey: {config.valkey_host}:{config.valkey_port}")
    yield
    logger.info("Shutting down CineVault OS API Service Foundation.")

app = FastAPI(
    title="CineVault OS — API Specification V1",
    description="Authoritative API boundary for canonical entertainment platform data (CAT-1), user personal data (CAT-2), offline sync, and control room curation.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 1. Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

# 2. Add Middlewares in order
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationAndMetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID", "X-Idempotency-Key", "X-Service-Identity", "X-Service-Action"],
)

# 3. Register Global Safe Error Handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# 4. Mount Routers
app.include_router(health.router)
app.include_router(titles.router)
app.include_router(search.router)
app.include_router(personal.router)
app.include_router(sync.router)
app.include_router(internal.router)
app.include_router(metrics.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.api.main:app", host="0.0.0.0", port=8000, reload=True)
