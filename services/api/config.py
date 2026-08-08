# CineVault OS — API Service Configuration Management
# Phase 3 Local Development Configuration Baseline

import os
from pydantic import BaseModel

class APIConfig(BaseModel):
    app_name: str = "CineVault OS API Gateway & Service Foundation"
    environment: str = os.getenv("ENVIRONMENT", "local_development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Database Integration (PgBouncer -> PostgreSQL)
    pgbouncer_host: str = os.getenv("PGBOUNCER_HOST", "localhost")
    pgbouncer_port: int = int(os.getenv("PGBOUNCER_PORT", "6432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "cinevault")
    postgres_user: str = os.getenv("POSTGRES_USER", "cinevault_dev")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "dev_postgres_password_change_me")
    
    # Cache & Rate Limiting (Valkey)
    valkey_host: str = os.getenv("VALKEY_HOST", "localhost")
    valkey_port: int = int(os.getenv("VALKEY_PORT", "6379"))
    
    # OIDC / Keycloak Authentication
    keycloak_issuer: str = os.getenv("KEYCLOAK_ISSUER", "http://localhost:8080/realms/cinevault-dev")
    keycloak_audience: str = os.getenv("KEYCLOAK_AUDIENCE", "cinevault-api-gateway")
    jwks_uri: str = os.getenv("JWKS_URI", "http://localhost:8080/realms/cinevault-dev/protocol/openid-connect/certs")
    
    # API Limits & Default Rate Boundaries
    rate_limit_public_read: int = 600
    rate_limit_search: int = 120
    rate_limit_sync: int = 60
    rate_limit_personal_write: int = 120
    rate_limit_internal_admin: int = 1200

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.pgbouncer_host}:{self.pgbouncer_port}/{self.postgres_db}"

config = APIConfig()
