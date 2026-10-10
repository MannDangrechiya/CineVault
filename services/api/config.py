# CineVault OS — API Service Configuration Management (P1 Fix)
# P1 Fix: ALLOW_SEED_FALLBACK defaults to False in all non-local environments.
#         Added S3 access key fields, JWT secret key, and computed provider properties.

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, model_validator

# The root .env file was previously never loaded anywhere in this codebase —
# every os.getenv() below only ever saw real values if they happened to
# already be exported in the shell before Python started. Loading it here,
# before any os.getenv() call in this module executes, is what makes "put
# your API key in .env" actually true. load_dotenv() never overrides a
# variable already set in the real environment, so an explicit shell export
# still wins over the file, same as the standard convention.
load_dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
try:
    from dotenv import load_dotenv

    load_dotenv(load_dotenv_path)
except ImportError:
    # python-dotenv isn't installed — fall back to whatever is already in
    # the process environment rather than hard-failing config import.
    pass


# P0 Fix (Day 1-7 remediation): known-insecure placeholder values that must
# never be active outside local_development. If any of these are still set
# when ENVIRONMENT is staging/production, the process refuses to boot rather
# than silently running with a forgeable/guessable secret.
_INSECURE_DEFAULTS = {
    "jwt_secret_key": "cinevault-local-dev-jwt-secret-CHANGE-IN-PROD-00000000",
    "postgres_password": "dev_postgres_password_change_me",
}


class APIConfig(BaseModel):
    app_name: str = "CineVault OS API Gateway & Service Foundation"
    environment: str = os.getenv("ENVIRONMENT", "local_development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "debug" if os.getenv("ENVIRONMENT", "local_development") == "local_development" else "info")

    # CORS: comma-separated list of allowed origins. Defaults to common
    # local development origins. Production MUST override via env var.
    cors_allowed_origins: str = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000,http://localhost:8080",
    )

    # API documentation (Swagger/ReDoc) visibility. Enabled by default in
    # local_development, disabled in production to reduce attack surface.
    docs_enabled: bool = os.getenv(
        "DOCS_ENABLED",
        "true" if os.getenv("ENVIRONMENT", "local_development") == "local_development" else "false",
    ).lower() == "true"

    # P1 Fix: Default to True ONLY in local_development; False everywhere else.
    # This prevents silent seed fallbacks from masking real infrastructure failures
    # in staging and production environments.
    allow_seed_fallback: bool = os.getenv(
        "ALLOW_SEED_FALLBACK",
        "true" if os.getenv("ENVIRONMENT", "local_development") == "local_development" else "false",
    ).lower() == "true"

    # Database Integration (direct to PostgreSQL — PgBouncer was removed in
    # the Phase 3 infrastructure consolidation; SQLAlchemy owns pooling now,
    # see database.py's bounded AsyncAdaptedQueuePool)
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "cinevault")
    postgres_user: str = os.getenv("POSTGRES_USER", "cinevault_dev")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "dev_postgres_password_change_me")

    # Cache & Rate Limiting (Valkey)
    valkey_host: str = os.getenv("VALKEY_HOST", "localhost")
    valkey_port: int = int(os.getenv("VALKEY_PORT", "6379"))

    # Native JWT signing secret (HS256 — the only auth mechanism; Keycloak/OIDC
    # was removed in the Phase 3 infrastructure consolidation)
    # IMPORTANT: Override this in your .env file. Never commit the real value.
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "cinevault-local-dev-jwt-secret-CHANGE-IN-PROD-00000000",
    )

    # API Limits & Default Rate Boundaries
    rate_limit_public_read: int = 600
    rate_limit_search: int = 120
    rate_limit_sync: int = 60
    rate_limit_personal_write: int = 120
    rate_limit_internal_admin: int = 1200

    # AI Provider Configuration
    # None (not the string "mock") when AI_PROVIDER is unset — this is what
    # lets effective_ai_provider below distinguish "not configured, please
    # auto-detect from whichever key is present" from "explicitly forced to
    # mock, ignore any keys". Collapsing both into the literal string "mock"
    # (the previous default) meant AI_PROVIDER=mock could never actually
    # force mock mode once any real API key existed in the environment.
    ai_provider: Optional[str] = os.getenv("AI_PROVIDER")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    # Groq: OpenAI-compatible API (https://console.groq.com), free tier —
    # reuses OpenAIProviderAdapter with a different base_url + model.
    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    # xAI Grok: OpenAI-compatible API (https://docs.x.ai) — a different
    # provider from Groq above despite the similar name; also reuses
    # OpenAIProviderAdapter with a different base_url + model.
    grok_api_key: Optional[str] = os.getenv("GROK_API_KEY")
    grok_model: str = os.getenv("GROK_MODEL", "grok-4")

    # Ingestion Provider Configuration
    ingestion_mode: str = os.getenv("INGESTION_MODE", "mock")
    provider_api_key: Optional[str] = os.getenv("PROVIDER_API_KEY")
    kobis_api_key: Optional[str] = os.getenv("KOBIS_API_KEY")
    tvdb_api_key: Optional[str] = os.getenv("TVDB_API_KEY")
    tmdb_api_key: Optional[str] = os.getenv("TMDB_API_KEY")

    # Local Artwork Storage (MinIO/S3 was removed in the Phase 3
    # infrastructure consolidation — audited to have zero production
    # traffic, since no client app ever called the upload endpoint. Files
    # now live in a persistent local directory served publicly by Caddy at
    # CDN_HOSTNAME, see infra/docker/Caddyfile and services/api/storage.py)
    artwork_path: str = os.getenv("ARTWORK_PATH", "./data/artwork")
    cdn_base_url: str = os.getenv("CDN_BASE_URL", "https://cdn.cinevault.org/artwork")

    @model_validator(mode="after")
    def _refuse_unsafe_defaults_outside_local_dev(self) -> "APIConfig":
        """
        P0 Fix (Day 1-7 remediation): a staging/production deployment must
        never boot with a placeholder secret still active. local_development
        is exempt — those defaults exist specifically to make first-run dev
        setup work without a .env file.
        """
        if self.environment != "local_development" and "ALLOW_SEED_FALLBACK" not in os.environ:
            self.allow_seed_fallback = False

        if self.environment == "local_development":
            return self

        unsafe = [
            field
            for field, placeholder in _INSECURE_DEFAULTS.items()
            if getattr(self, field) == placeholder
        ]
        if unsafe:
            raise RuntimeError(
                "Refusing to start: ENVIRONMENT="
                f"'{self.environment}' but the following secrets are still "
                f"set to their insecure local_development default: {', '.join(unsafe)}. "
                "Set real values via environment variables before deploying "
                "outside local_development."
            )
        return self

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def effective_ai_provider(self) -> str:
        """
        Resolves the active AI provider.
        - If AI_PROVIDER env var is explicitly set (to ANY value, including
          the literal string "mock"), use it exactly as given — this is what
          lets a test session or a developer force real mock behavior even
          when a working API key is also present in the environment.
        - Otherwise (AI_PROVIDER unset entirely), auto-detect based on
          whichever API key is present.
        - Falls back to 'mock' only when neither an explicit setting nor any
          credentials are present.
        """
        if self.ai_provider is not None:
            return self.ai_provider
        if self.grok_api_key:
            return "grok"
        if self.groq_api_key:
            return "groq"
        if self.openai_api_key:
            return "openai"
        if self.gemini_api_key:
            return "gemini"
        return "mock"

    @property
    def effective_ingestion_mode(self) -> str:
        """
        Resolves the active ingestion mode.
        - If INGESTION_MODE env var is explicitly set to a non-mock value, use it.
        - Otherwise, auto-detect based on available provider API keys.
        - Falls back to 'mock' only when no provider credentials are present.
        """
        if self.ingestion_mode != "mock":
            return self.ingestion_mode
        if self.kobis_api_key or self.tvdb_api_key or self.tmdb_api_key or self.provider_api_key:
            return "live"
        return "mock"


config = APIConfig()
