# CineVault OS — Local Artwork Storage & CDN Integration Tests (Phase 9.12)
# MinIO/S3 was audited and removed in the Phase 3 infrastructure
# consolidation (zero production traffic ever reached the upload endpoint —
# see the storage.py module docstring); this now exercises the local-disk
# adapter and the security hardening added as part of that swap.

import pytest
import base64
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.storage import LocalArtworkStorageAdapter, StorageError
from services.api.routers.auth import generate_dev_jwt

client = TestClient(app)

# Real magic bytes for each supported format — content is sniffed, not
# trusted from the caller-declared content_type.
_REAL_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 16
_REAL_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def test_object_storage_upload_dev_mode(tmp_path):
    adapter = LocalArtworkStorageAdapter(
        artwork_path=str(tmp_path),
        cdn_base_url="https://cdn.cinevault.org/artwork",
    )

    cdn_url = adapter.upload_artwork(
        file_bytes=_REAL_JPEG_BYTES,
        filename="dune_part_two_poster.jpg",
        content_type="image/jpeg",
        folder="posters",
    )

    assert "dune_part_two_poster.jpg" in cdn_url
    assert cdn_url.startswith("https://cdn.cinevault.org/artwork/posters/")

    # The file actually landed on disk under the given root.
    written = list((tmp_path / "posters").glob("*_dune_part_two_poster.jpg"))
    assert len(written) == 1
    assert written[0].read_bytes() == _REAL_JPEG_BYTES


def test_object_storage_rejects_empty_file(tmp_path):
    adapter = LocalArtworkStorageAdapter(artwork_path=str(tmp_path))
    with pytest.raises(StorageError, match="Cannot upload empty artwork file"):
        adapter.upload_artwork(file_bytes=b"", filename="empty.jpg")


def test_object_storage_rejects_oversized_file(tmp_path):
    adapter = LocalArtworkStorageAdapter(artwork_path=str(tmp_path))
    oversized = _REAL_JPEG_BYTES + (b"\x00" * (10 * 1024 * 1024))
    with pytest.raises(StorageError, match="exceeds the .*MB size limit"):
        adapter.upload_artwork(file_bytes=oversized, filename="huge.jpg")


def test_object_storage_rejects_content_not_matching_declared_type(tmp_path):
    """The declared content_type is never trusted — real magic bytes decide."""
    adapter = LocalArtworkStorageAdapter(artwork_path=str(tmp_path))
    with pytest.raises(StorageError, match="does not match a supported image format"):
        adapter.upload_artwork(
            file_bytes=b"MZ\x90\x00" + b"executable_not_an_image",
            filename="malicious.jpg",
            content_type="image/jpeg",  # lies — bytes are not a real JPEG
        )


def test_object_storage_sanitizes_path_traversal_filename(tmp_path):
    """A path-traversal filename is sanitized down to a safe basename and
    written inside artwork_root — it must never escape to the attempted
    target path."""
    adapter = LocalArtworkStorageAdapter(artwork_path=str(tmp_path))
    cdn_url = adapter.upload_artwork(
        file_bytes=_REAL_PNG_BYTES,
        filename="../../etc/passwd.png",
        content_type="image/png",
    )

    # Landed safely under artwork_root/posters, not escaped anywhere.
    written = list((tmp_path / "posters").glob("*_passwd.png"))
    assert len(written) == 1
    assert "passwd.png" in cdn_url
    assert not (tmp_path.parent.parent / "etc" / "passwd.png").exists()


def test_object_storage_get_object_rejects_raw_traversal_key(tmp_path):
    """Defense-in-depth: even a raw object_key handed straight to
    get_object() (bypassing generate_object_key entirely) must not escape
    artwork_root."""
    adapter = LocalArtworkStorageAdapter(artwork_path=str(tmp_path))
    assert adapter.get_object("../../../../etc/passwd") is None


def test_object_storage_rejects_disallowed_folder(tmp_path):
    adapter = LocalArtworkStorageAdapter(artwork_path=str(tmp_path))
    with pytest.raises(StorageError, match="Invalid artwork folder"):
        adapter.upload_artwork(
            file_bytes=_REAL_JPEG_BYTES,
            filename="poster.jpg",
            folder="../../etc",
        )


def test_internal_artwork_upload_endpoint():
    base64_image = base64.b64encode(_REAL_JPEG_BYTES).decode("utf-8")

    curator_token = generate_dev_jwt(
        user_id="usr_curator_999",
        email="curator@cinevault.local",
        username="curator",
        roles=["authenticated_user", "curator"],
    )
    headers = {"Authorization": f"Bearer {curator_token}"}

    payload = {
        "filename": "parasite_poster.jpg",
        "content_type": "image/jpeg",
        "folder": "posters",
        "file_base64": base64_image,
    }

    response = client.post("/internal/v1/artwork/upload", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "cdn_url" in data
    assert "parasite_poster.jpg" in data["cdn_url"]
    assert data["filename"] == "parasite_poster.jpg"


def test_internal_artwork_upload_endpoint_rejects_fake_image():
    """A caller lying about content_type is caught by the endpoint too, not
    just the adapter directly."""
    base64_payload = base64.b64encode(b"not_actually_an_image_at_all").decode("utf-8")

    curator_token = generate_dev_jwt(
        user_id="usr_curator_998",
        email="curator2@cinevault.local",
        username="curator2",
        roles=["authenticated_user", "curator"],
    )
    headers = {"Authorization": f"Bearer {curator_token}"}

    payload = {
        "filename": "fake.jpg",
        "content_type": "image/jpeg",
        "folder": "posters",
        "file_base64": base64_payload,
    }

    response = client.post("/internal/v1/artwork/upload", json=payload, headers=headers)
    assert response.status_code == 400
