# CineVault OS — Services Directory Structure

This directory houses the 3-tier microservice boundaries for CineVault OS:

* `services/api/`: Public & Internal REST API (FastAPI), served directly behind Caddy — no separate API gateway. Native HS256 authentication (see `services/api/routers/auth.py`); ingestion (`services/api/ingestion/`), quality checks, and sync all live inside this one service rather than as the separate `ingestion/`/`quality/`/`sync/` microservices this file used to describe.
