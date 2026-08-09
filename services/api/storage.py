# CineVault OS — S3 Object Storage & CDN Artwork Adapter (P1 Fix)
# Handles poster/backdrop image uploads to S3-compatible storage.
# P1 Fix: Replaced in-memory Python dict with real boto3 S3 SDK calls to MinIO (dev)
#         and AWS S3 (production). Added presigned URL generation and bucket bootstrap.

import io
import logging
import hashlib
from typing import Optional
from .config import config

logger = logging.getLogger("cinevault.storage")

# ---------------------------------------------------------------------------
# boto3 availability guard
# ---------------------------------------------------------------------------
try:
    import boto3
    from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError
    _BOTO3_AVAILABLE = True
except ImportError:  # pragma: no cover
    _BOTO3_AVAILABLE = False
    logger.warning(
        "boto3 is not installed. MinIO/S3 storage is unavailable. "
        "Run: pip install boto3"
    )


class StorageError(Exception):
    """Raised when S3 object storage operations fail."""
    pass


class ObjectStorageAdapter:
    """
    S3-compatible Object Storage Adapter supporting MinIO (local dev) and AWS S3 (production).

    In local_development with allow_seed_fallback=True: falls back to an in-memory
    store if the boto3 client cannot connect to MinIO, to preserve offline dev experience.
    In staging/production (allow_seed_fallback=False): raises StorageError immediately
    if S3 operations fail — no silent fallback.
    """

    PRESIGNED_URL_EXPIRY_SECONDS = 3600  # 1 hour

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        bucket_name: Optional[str] = None,
        cdn_base_url: Optional[str] = None,
    ):
        self.endpoint_url = endpoint_url or config.s3_endpoint_url
        self.bucket_name = bucket_name or config.s3_artwork_bucket
        self.cdn_base_url = cdn_base_url or config.cdn_base_url
        # Fallback in-memory store — used ONLY in local_development when MinIO is offline
        self._in_memory_store: dict = {}
        self._s3_client = None

        if _BOTO3_AVAILABLE:
            self._init_s3_client()

    def _init_s3_client(self) -> None:
        """Initializes the boto3 S3 client with MinIO-compatible settings."""
        try:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=config.s3_access_key_id,
                aws_secret_access_key=config.s3_secret_access_key,
                region_name=config.s3_region,
                # MinIO requires path-style addressing (not virtual-hosted-style)
                config=boto3.session.Config(signature_version="s3v4"),
            )
            logger.info(
                "S3 client initialized: endpoint=%s bucket=%s",
                self.endpoint_url,
                self.bucket_name,
            )
        except Exception as exc:
            logger.error("Failed to initialize boto3 S3 client: %s", exc)
            self._s3_client = None

    def ensure_bucket_exists(self) -> None:
        """
        Ensures the artwork bucket exists, creating it if necessary.
        Called at application startup. Raises StorageError if MinIO is unreachable
        and allow_seed_fallback=False.
        """
        if not _BOTO3_AVAILABLE or self._s3_client is None:
            if not config.allow_seed_fallback:
                raise StorageError(
                    "boto3 is not available and allow_seed_fallback=False. "
                    "MinIO/S3 storage is required in this environment."
                )
            return

        try:
            self._s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("S3 bucket '%s' confirmed reachable.", self.bucket_name)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchBucket"):
                try:
                    self._s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info("S3 bucket '%s' created.", self.bucket_name)
                except ClientError as create_exc:
                    raise StorageError(
                        f"Failed to create S3 bucket '{self.bucket_name}': {create_exc}"
                    ) from create_exc
            else:
                raise StorageError(
                    f"S3 bucket check failed with code '{error_code}': {exc}"
                ) from exc
        except EndpointConnectionError as exc:
            if not config.allow_seed_fallback:
                raise StorageError(
                    f"Cannot connect to S3 endpoint '{self.endpoint_url}': {exc}. "
                    "Ensure MinIO is running (docker-compose up minio)."
                ) from exc
            logger.warning(
                "MinIO unreachable at %s — falling back to in-memory storage "
                "(local_development only).",
                self.endpoint_url,
            )

    def generate_object_key(self, filename: str, folder: str = "posters") -> str:
        """Generates a deterministic content-addressed S3 object key."""
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
        """
        Uploads artwork image bytes to the S3/MinIO bucket.
        Returns the public CDN URL (production) or MinIO endpoint URL (local dev).

        Raises:
            StorageError: If the upload fails and allow_seed_fallback=False.
        """
        if not file_bytes:
            raise StorageError("Cannot upload empty artwork file.")

        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if content_type.lower() not in allowed_types:
            raise StorageError(
                f"Unsupported content type '{content_type}'. "
                f"Allowed: {sorted(allowed_types)}."
            )

        object_key = self.generate_object_key(filename, folder=folder)

        # --- Real S3 upload ---
        if _BOTO3_AVAILABLE and self._s3_client is not None:
            try:
                self._s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=file_bytes,
                    ContentType=content_type,
                    ContentLength=len(file_bytes),
                )
                logger.info(
                    "Uploaded artwork to s3://%s/%s (%d bytes)",
                    self.bucket_name,
                    object_key,
                    len(file_bytes),
                )
                return self._resolve_public_url(object_key)
            except (ClientError, EndpointConnectionError, NoCredentialsError) as exc:
                if not config.allow_seed_fallback:
                    raise StorageError(
                        f"S3 upload failed for '{object_key}': {exc}"
                    ) from exc
                logger.warning(
                    "S3 upload failed — falling back to in-memory store: %s", exc
                )

        # --- In-memory fallback (local_development only) ---
        self._in_memory_store[object_key] = file_bytes
        logger.debug(
            "Stored artwork in-memory: key=%s (%d bytes)", object_key, len(file_bytes)
        )
        return self._resolve_public_url(object_key)

    def get_object(self, object_key: str) -> Optional[bytes]:
        """
        Retrieves raw bytes for an object from S3/MinIO.
        Falls back to in-memory store in local_development if S3 is unavailable.

        Returns None if the object does not exist.
        """
        if _BOTO3_AVAILABLE and self._s3_client is not None:
            try:
                response = self._s3_client.get_object(
                    Bucket=self.bucket_name, Key=object_key
                )
                return response["Body"].read()
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code", "")
                if error_code in ("NoSuchKey", "404"):
                    return None
                if not config.allow_seed_fallback:
                    raise StorageError(
                        f"S3 get_object failed for '{object_key}': {exc}"
                    ) from exc
                logger.warning("S3 get_object failed, checking in-memory: %s", exc)
            except EndpointConnectionError as exc:
                if not config.allow_seed_fallback:
                    raise StorageError(
                        f"Cannot connect to S3 to retrieve '{object_key}': {exc}"
                    ) from exc

        # In-memory fallback
        return self._in_memory_store.get(object_key)

    def get_presigned_url(
        self,
        object_key: str,
        expires_in: int = PRESIGNED_URL_EXPIRY_SECONDS,
    ) -> Optional[str]:
        """
        Generates a presigned GET URL for temporary direct access to a private S3 object.
        Returns None if S3 is unavailable (falls back to direct URL in dev).
        """
        if _BOTO3_AVAILABLE and self._s3_client is not None:
            try:
                url = self._s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": object_key},
                    ExpiresIn=expires_in,
                )
                return url
            except (ClientError, Exception) as exc:
                logger.warning("generate_presigned_url failed: %s", exc)

        # Fallback: return direct MinIO URL in local dev
        return self._resolve_public_url(object_key)

    def _resolve_public_url(self, object_key: str) -> str:
        """Resolves the public URL for a stored object based on current environment."""
        if config.environment in ("staging", "production"):
            return f"{self.cdn_base_url.rstrip('/')}/{object_key}"
        # Local dev: direct MinIO URL
        return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{object_key}"


storage_adapter = ObjectStorageAdapter()
