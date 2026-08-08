# CineVault OS — Services Directory Structure

This directory houses the 3-tier microservice boundaries for CineVault OS:

* `services/api/`: Public & Internal REST API microservices (FastAPI / Go, Kong Gateway integration, Keycloak OIDC authentication).
* `services/ingestion/`: Asynchronous ingestion pipeline workers (RabbitMQ consumers, Provider adapters, Licensing Gate verification, Raw payload capture).
* `services/quality/`: 8-layer Data Quality Verification Engine & Quarantine Processor (`CAT-6`).
* `services/sync/`: Client Offline Sync Engine & Personal Data (`CAT-2`) dispute resolution service.
