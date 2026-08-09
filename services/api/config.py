# CineVault OS — API Service Configuration Management (P1 Fix)
# P1 Fix: ALLOW_SEED_FALLBACK defaults to False in all non-local environments.
#         Added S3 access key fields, JWT secret key, and computed provider properties.

import os
from typing import Optional
from pydantic import BaseModel


class APIConfig(BaseModel):
    app_name: str = "CineVault OS API Gateway & Service Foundation"
    environment: str = os.getenv("ENVIRONMENT", "local_development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # P1 Fix: Default to True ONLY in local_development; False everywhere else.
    # This prevents silent seed fallbacks from masking real infrastructure failures
    # in staging and production environments.
    allow_seed_fallback: bool = os.getenv(
        "ALLOW_SEED_FALLBACK",
        "true" if os.getenv("ENVIRONMENT", "local_development") == "local_development" else "false",
    ).lower() == "true"

    # Database Integration (PgBouncer -> PostgreSQL)
    pgbouncer_host: str = os.getenv("PGBOUNCER_HOST", "localhost")
    pgbouncer_port: int = int(os.getenv("PGBOUNCER_PORT", "6432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "cinevault")
    postgres_user: str = os.getenv("POSTGRES_USER", "cinevault_dev")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "dev_postgres_password_change_me")

    # Cache & Rate Limiting (Valkey)
    valkey_host: str = os.getenv("VALKEY_HOST", "localhost")
    valkey_port: int = int(os.getenv("VALKEY_PORT", "6379"))

    # Message Queue Broker (RabbitMQ AMQP 0-9-1)
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user: str = os.getenv("RABBITMQ_USER", "cinevault_dev")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "dev_rabbitmq_password_change_me")
    rabbitmq_vhost: str = os.getenv("RABBITMQ_VHOST", "/")

    # OIDC / Keycloak Authentication
    keycloak_issuer: str = os.getenv(
        "KEYCLOAK_ISSUER", "http://localhost:8080/realms/cinevault-dev"
    )
    keycloak_audience: str = os.getenv("KEYCLOAK_AUDIENCE", "cinevault-api-gateway")
    jwks_uri: str = os.getenv(
        "JWKS_URI",
        "http://localhost:8080/realms/cinevault-dev/protocol/openid-connect/certs",
    )

    # Local dev JWT signing secret (HS256 — NOT used in staging/production)
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
    ai_provider: str = os.getenv("AI_PROVIDER", "mock")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Ingestion Provider Configuration
    ingestion_mode: str = os.getenv("INGESTION_MODE", "mock")
    kobis_api_key: Optional[str] = os.getenv("KOBIS_API_KEY")
    tvdb_api_key: Optional[str] = os.getenv("TVDB_API_KEY")

    # S3 & CDN Storage Configuration
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    s3_artwork_bucket: str = os.getenv("S3_ARTWORK_BUCKET", "cinevault-dev-artwork")
    cdn_base_url: str = os.getenv("CDN_BASE_URL", "https://cdn.cinevault.org/artwork")
    # P1 Fix: Added S3 access key fields (previously missing — boto3 couldn't authenticate)
    s3_access_key_id: str = os.getenv("S3_ACCESS_KEY_ID", "dev_s3_access_key")
    s3_secret_access_key: str = os.getenv("S3_SECRET_ACCESS_KEY", "dev_s3_secret_key")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.pgbouncer_host}:{self.pgbouncer_port}/{self.postgres_db}"
        )

    @property
    def effective_ai_provider(self) -> str:
        """
        Resolves the active AI provider.
        - If AI_PROVIDER env var is explicitly set to a non-mock value, use it.
        - Otherwise, auto-detect based on available API keys.
        - Falls back to 'mock' only when no credentials are present.
        """
        if self.ai_provider != "mock":
            return self.ai_provider
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
        if self.kobis_api_key or self.tvdb_api_key:
            return "live"
        return "mock"


config = APIConfig()
