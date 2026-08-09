# CineVault OS — Object Storage & CDN Architecture Deployment Guide (Phase 9.12)

This document specifies the object storage and CDN architecture for serving canonical poster and backdrop artwork assets (`poster_url`, `backdrop_url`).

---

## 1. Local Development Architecture (MinIO S3 Emulation)

In local development, object storage parity is provided by a MinIO container running alongside PostgreSQL, Valkey, and Keycloak via Docker Compose.

### Service Ports & Credentials
- **S3 API Port**: `http://localhost:9000`
- **Web Console Port**: `http://localhost:9001`
- **Root Credentials**: `MINIO_ROOT_USER=dev_s3_access_key`, `MINIO_ROOT_PASSWORD=dev_s3_secret_key`
- **Dev Buckets**:
  - `cinevault-dev-artwork` (Poster & backdrop image binaries)
  - `cinevault-dev-raw-payloads` (CAT-5 immutable provider payloads)

### Local Dev Environment Config (`.env`)
```ini
ENVIRONMENT=local_development
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=dev_s3_access_key
S3_SECRET_ACCESS_KEY=dev_s3_secret_key
S3_ARTWORK_BUCKET=cinevault-dev-artwork
CDN_BASE_URL=http://localhost:9000/cinevault-dev-artwork
```

---

## 2. Production Architecture (AWS S3 + CloudFront CDN)

In staging and production environments, `ObjectStorageAdapter` connects directly to AWS S3 (or Cloudflare R2 / MinIO Cluster) with CloudFront TLS distribution.

### Production Environment Config (`.env`)
```ini
ENVIRONMENT=production
S3_ENDPOINT_URL=https://s3.us-east-1.amazonaws.com
S3_ACCESS_KEY_ID=prod_s3_access_key_vault
S3_SECRET_ACCESS_KEY=prod_s3_secret_key_vault
S3_ARTWORK_BUCKET=cinevault-prod-artwork
CDN_BASE_URL=https://cdn.cinevault.org/artwork
```

### CDN Caching & Header Requirements
- **Cache-Control**: `public, max-age=31536000, immutable`
- **CORS Headers**: `Access-Control-Allow-Origin: *`
- **MIME Content-Types**: `image/jpeg`, `image/png`, `image/webp`
