# CineVault OS — Object Storage & Artwork CDN Integration Tests (Phase 9.12)

import pytest
import base64
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.storage import ObjectStorageAdapter, StorageError
from services.api.routers.auth import generate_dev_jwt

client = TestClient(app)

def test_object_storage_upload_dev_mode():
    adapter = ObjectStorageAdapter(
        endpoint_url="http://localhost:9000",
        bucket_name="cinevault-dev-artwork",
        cdn_base_url="https://cdn.cinevault.org/artwork",
    )
    test_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    
    cdn_url = adapter.upload_artwork(
        file_bytes=test_bytes,
        filename="dune_part_two_poster.jpg",
        content_type="image/jpeg",
        folder="posters",
    )

    assert "dune_part_two_poster.jpg" in cdn_url
    assert cdn_url.startswith("http://localhost:9000/cinevault-dev-artwork/posters/")

def test_object_storage_rejects_empty_file():
    adapter = ObjectStorageAdapter()
    with pytest.raises(StorageError, match="Cannot upload empty artwork file"):
        adapter.upload_artwork(file_bytes=b"", filename="empty.jpg")

def test_object_storage_rejects_unsupported_content_type():
    adapter = ObjectStorageAdapter()
    with pytest.raises(StorageError, match="Unsupported content type"):
        adapter.upload_artwork(
            file_bytes=b"executable_data",
            filename="malicious.exe",
            content_type="application/x-msdownload",
        )

def test_internal_artwork_upload_endpoint():
    dummy_image = b"dummy_jpeg_binary_data"
    base64_image = base64.b64encode(dummy_image).decode("utf-8")

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
