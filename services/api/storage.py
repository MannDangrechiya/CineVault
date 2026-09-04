# CineVault OS — Local Artwork Storage Adapter (Phase 3 infra consolidation)
# Replaces MinIO/S3 with a persistent local directory (config.artwork_path),
# served publicly and read-only by Caddy at CDN_HOSTNAME (see
# infra/docker/Caddyfile). MinIO was audited and found to carry zero
# production traffic — no client app anywhere calls the upload endpoint
# below, and canonical TMDB artwork is served from remote TMDB URLs, never
# stored here — so this is a storage-backend swap, not a data migration.
#
# Security hardening added as part of this swap: the upload endpoint's
# input handling was safe only by accident of S3 key semantics (an S3
# object key isn't a filesystem path). Backed by a real local directory,
# the same gaps become real vulnerabilities, so this adapter now enforces:
# - generate_object_key(): rejects path traversal (Path(...).name strips
#   any directory components), restricts folder to a fixed allowlist, and
#   restricts filenames to a safe character set
# - _resolve_path(): a defense-in-depth check that the resolved path is
#   still inside artwork_root, independent of generate_object_key
# - upload_artwork(): enforces a real file-size cap and validates content
#   against real magic bytes — the caller-declared content_type is never
#   trusted on its own

import logging
import hashlib
import re
from pathlib import Path
from typing import Optional
from .config import config

logger = logging.getLogger("cinevault.storage")

MAX_ARTWORK_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_FOLDERS = {"posters", "backdrops"}
_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")


class StorageError(Exception):
    """Raised when artwork storage operations fail or reject unsafe input."""
    pass


def _sniff_content_type(file_bytes: bytes) -> Optional[str]:
    """Identifies the real image type from magic bytes, ignoring whatever
    content_type the caller declared. Returns None if the bytes don't match
    any supported image format."""
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
        return "image/webp"
    return None


class LocalArtworkStorageAdapter:
    """
    Local-filesystem artwork storage adapter.

    In local_development with allow_seed_fallback=True: falls back to an
    in-memory store if artwork_root can't be created/written to, to preserve
    offline dev experience. In staging/production (allow_seed_fallback=False):
    raises StorageError immediately on any write failure — no silent fallback.
    """

    def __init__(
        self,
        artwork_path: Optional[str] = None,
        cdn_base_url: Optional[str] = None,
    ):
        self.artwork_root = Path(artwork_path or config.artwork_path).resolve()
        self.cdn_base_url = cdn_base_url or config.cdn_base_url
        # Fallback in-memory store — used ONLY in local_development when the
        # artwork directory can't be created/written to.
        self._in_memory_store: dict = {}

        try:
            self.artwork_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            if not config.allow_seed_fallback:
                raise StorageError(
                    f"Cannot create artwork storage directory '{self.artwork_root}': {exc}"
                ) from exc
            logger.warning(
                "Could not create artwork directory %s — falling back to "
                "in-memory storage (local_development only): %s",
                self.artwork_root,
                exc,
            )

    def generate_object_key(self, filename: str, folder: str = "posters") -> str:
        """Generates a safe, content-addressed relative storage key.

        This key is joined directly onto a real filesystem path (see
        _resolve_path), so it must never be able to escape artwork_root:
        folder is restricted to a fixed allowlist, and Path(filename).name
        strips any directory components a caller might smuggle in (e.g.
        "../../etc/passwd", "a/b/c.jpg") before the remaining characters are
        checked against a safe allowlist.
        """
        if folder not in ALLOWED_FOLDERS:
            raise StorageError(
                f"Invalid artwork folder '{folder}'. Allowed: {sorted(ALLOWED_FOLDERS)}."
            )

        clean_filename = Path(filename).name.lower().replace(" ", "_")
        if not clean_filename or not _SAFE_FILENAME_RE.match(clean_filename):
            raise StorageError(
                "Filename must be non-empty and contain only letters, digits, "
                "dots, underscores, and hyphens."
            )

        hash_prefix = hashlib.sha256(clean_filename.encode()).hexdigest()[:8]
        return f"{folder}/{hash_prefix}_{clean_filename}"

    def _resolve_path(self, object_key: str) -> Path:
        """Joins object_key onto artwork_root and verifies the result is
        still inside artwork_root — a defense-in-depth check independent of
        generate_object_key's own validation."""
        candidate = (self.artwork_root / object_key).resolve()
        if candidate != self.artwork_root and self.artwork_root not in candidate.parents:
            raise StorageError(
                f"Object key '{object_key}' resolves outside artwork storage root."
            )
        return candidate

    def upload_artwork(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "image/jpeg",
        folder: str = "posters",
    ) -> str:
        """
        Writes artwork image bytes to local disk under artwork_root.
        Returns the public CDN URL.

        Raises:
            StorageError: empty file, oversized file, content that doesn't
            match a real supported image type (checked via magic bytes, not
            the caller-declared content_type), or an unsafe filename/folder.
        """
        if not file_bytes:
            raise StorageError("Cannot upload empty artwork file.")

        if len(file_bytes) > MAX_ARTWORK_SIZE_BYTES:
            raise StorageError(
                f"Artwork file exceeds the {MAX_ARTWORK_SIZE_BYTES // (1024 * 1024)}MB size limit."
            )

        sniffed_type = _sniff_content_type(file_bytes)
        if sniffed_type is None:
            raise StorageError(
                "File content does not match a supported image format "
                "(JPEG, PNG, or WebP) — the declared content_type is not trusted."
            )

        object_key = self.generate_object_key(filename, folder=folder)
        target_path = self._resolve_path(object_key)

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(file_bytes)
            logger.info(
                "Wrote artwork to %s (%d bytes, sniffed as %s)",
                target_path,
                len(file_bytes),
                sniffed_type,
            )
            return self._resolve_public_url(object_key)
        except OSError as exc:
            if not config.allow_seed_fallback:
                raise StorageError(f"Failed to write artwork '{object_key}': {exc}") from exc
            logger.warning("Artwork write failed — falling back to in-memory store: %s", exc)
            self._in_memory_store[object_key] = file_bytes
            return self._resolve_public_url(object_key)

    def get_object(self, object_key: str) -> Optional[bytes]:
        """
        Reads raw bytes for an object from local disk.
        Falls back to the in-memory store used by upload_artwork's
        local_development fallback path.

        Returns None if the object does not exist anywhere.
        """
        try:
            path = self._resolve_path(object_key)
            if path.is_file():
                return path.read_bytes()
        except (StorageError, OSError) as exc:
            logger.warning("get_object failed for '%s': %s", object_key, exc)

        return self._in_memory_store.get(object_key)

    def _resolve_public_url(self, object_key: str) -> str:
        """Resolves the public URL Caddy serves this object at."""
        return f"{self.cdn_base_url.rstrip('/')}/{object_key}"


storage_adapter = LocalArtworkStorageAdapter()
