# CineVault OS — Test Suite for Celery AI Worker (Phase 4)
# Validates Celery app initialization, task registration, and deterministic vector calculations.

import pytest
from services.ai_worker.worker import (
    celery_app,
    generate_title_embedding_task,
    batch_tmdb_artwork_sync_task,
    compute_user_taste_profile_task,
    _generate_synthetic_384_embedding,
)


def test_celery_app_configuration():
    """Verifies Celery application tasks registration and serialization settings."""
    assert "generate_title_embedding_task" in celery_app.tasks
    assert "batch_tmdb_artwork_sync_task" in celery_app.tasks
    assert "compute_user_taste_profile_task" in celery_app.tasks
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.timezone == "UTC"


def test_synthetic_384_embedding_math():
    """Verifies generated embeddings have exact 384 dimensions and normalized magnitude."""
    vector = _generate_synthetic_384_embedding("test-title-dune-2024")
    assert len(vector) == 384
    # Calculate vector norm
    norm = sum(x * x for x in vector)
    assert abs(norm - 1.0) < 0.01


def test_generate_title_embedding_task_execution():
    """Tests synchronous invocation of title embedding task."""
    result = generate_title_embedding_task.apply(args=["018f2e4a-7b31-7000-8000-000000000001"]).get()
    assert result["status"] == "success"
    assert result["title_id"] == "018f2e4a-7b31-7000-8000-000000000001"
    assert result["dimension"] == 384
    assert len(result["vector_preview"]) == 5


def test_batch_tmdb_artwork_sync_task_execution():
    """Tests synchronous invocation of artwork batch sync task."""
    result = batch_tmdb_artwork_sync_task.apply(args=[50]).get()
    assert result["status"] == "success"
    assert result["requested_limit"] == 50
    assert result["synced_count"] <= 50


def test_compute_user_taste_profile_task_execution():
    """Tests synchronous invocation of user taste profile recomputation task."""
    result = compute_user_taste_profile_task.apply(args=["018f4a00-0000-7000-8000-000000000001"]).get()
    assert result["status"] == "success"
    assert result["user_id"] == "018f4a00-0000-7000-8000-000000000001"
    assert result["vector_dimension"] == 384
