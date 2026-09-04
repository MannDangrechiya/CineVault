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
    auth,
    titles,
    search,
    personal,
    sync,
    internal,
    metrics,
    recommendations,
    ai_assistant,
    control_room,
    observability,
    jobs,
    performance,
    social,
    ai,
    automation,
    admin
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CineVault OS API Service Foundation...")
    logger.info(f"Environment: {config.environment} | Postgres: {config.postgres_host}:{config.postgres_port} | Valkey: {config.valkey_host}:{config.valkey_port}")
    yield
    logger.info("Shutting down CineVault OS API Service Foundation.")

app = FastAPI(
    title="CineVault OS — API Specification V1",
    description="Authoritative API boundary for canonical entertainment platform data (CAT-1), user personal data (CAT-2), offline sync, and control room curation.",
    version="1.0.0",
    openapi_url="/openapi.json" if config.docs_enabled else None,
    docs_url="/docs" if config.docs_enabled else None,
    redoc_url="/redoc" if config.docs_enabled else None,
    lifespan=lifespan
)

# 1. Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

# 2. Add Middlewares in order
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationAndMetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in config.cors_allowed_origins.split(",") if o.strip()],
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
app.include_router(auth.router)
app.include_router(titles.router)
app.include_router(titles.catalog_router)
app.include_router(titles.root_router)
app.include_router(search.router)
app.include_router(personal.router)
app.include_router(personal.personal_router)
app.include_router(sync.router)
app.include_router(internal.router)
app.include_router(metrics.router)
app.include_router(recommendations.router)
app.include_router(ai_assistant.public_router)
app.include_router(ai_assistant.internal_router)
app.include_router(control_room.router)
app.include_router(observability.router)
app.include_router(jobs.router)
app.include_router(performance.router)
app.include_router(social.router)
app.include_router(ai.router)
app.include_router(automation.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run("services.api.main:app", host="0.0.0.0", port=port, reload=True)
