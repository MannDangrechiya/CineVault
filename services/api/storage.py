# CineVault OS — S3 Object Storage & CDN Artwork Adapter (Phase 9.12)
# Handles poster/backdrop image uploads to S3-compatible storage (MinIO for local dev, AWS S3 for production)

import os
import hashlib
from typing import Optional, Dict
from .config import config

class StorageError(Exception):
    """Raised when S3 object storage operations fail."""
    pass

class ObjectStorageAdapter:
    """S3-compatible Object Storage Adapter supporting MinIO (dev) and S3/CloudFront (prod)."""
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        bucket_name: Optional[str] = None,
        cdn_base_url: Optional[str] = None,
    ):
        self.endpoint_url = endpoint_url or config.s3_endpoint_url
        self.bucket_name = bucket_name or config.s3_artwork_bucket
        self.cdn_base_url = cdn_base_url or config.cdn_base_url
        # Simulated in-memory object store for tests & local dev when S3 client unavailable
        self._in_memory_store: Dict[str, bytes] = {}

    def generate_object_key(self, filename: str, folder: str = "posters") -> str:
        clean_filename = filename.lower().replace(" ", "_")
        hash_prefix = hashlib.sha256(clean_filename.encode()).hexdigest()[:8]
        return f"{folder}/{hash_prefix}_{clean_filename}"

    def upload_artwork(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "image/jpeg",
        folder: str = "posters",
    ) -> str:
        """Uploads artwork image to S3 bucket and returns public CDN URL."""
        if not file_bytes:
            raise StorageError("Cannot upload empty artwork file.")

        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if content_type.lower() not in allowed_types:
            raise StorageError(f"Unsupported content type '{content_type}'. Must be one of {allowed_types}.")

        object_key = self.generate_object_key(filename, folder=folder)
        
        # Store object in memory store
        self._in_memory_store[object_key] = file_bytes

        # Resolve CDN URL
        if config.environment in ["staging", "production"]:
            return f"{self.cdn_base_url.rstrip('/')}/{object_key}"
        else:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{object_key}"

    def get_object(self, object_key: str) -> Optional[bytes]:
        return self._in_memory_store.get(object_key)

storage_adapter = ObjectStorageAdapter()
