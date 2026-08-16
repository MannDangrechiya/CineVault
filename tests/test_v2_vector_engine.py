# CineVault OS — Test Suite for Module 2: The Vector Engine (v2.0)
# Validates pgvector integration, 384-dimensional taste profiles,
# Pydantic vector validations, cosine similarity math, and API endpoints.

import math
import uuid
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.models.social import UserTasteProfileModel
from services.api.schemas.social import (
    TasteMatchResponse,
    UserTasteProfileUpdate,
    UserTasteProfileResponse,
)
from services.api.repositories.social import (
    social_repository,
    _compute_cosine_distance,
    SEED_FRIENDSHIPS,
    SEED_TASTE_PROFILES,
)
from services.api.routers.auth import generate_dev_jwt

client = TestClient(app)


def get_test_token(user_id: str) -> str:
    """Generates an authenticated JWT for integration testing."""
    return generate_dev_jwt(
        user_id=user_id,
        email=f"{user_id}@cinevault.test",
        username=f"user_{user_id[-6:]}",
        roles=["authenticated_user"],
    )


# -----------------------------------------------------------------------------
# 1. Database Model & Schema Isolation Tests
# -----------------------------------------------------------------------------

def test_user_taste_profile_model_schema_isolation():
    """Verifies UserTasteProfileModel belongs strictly to 'social' schema with 384-dim vector."""
    assert UserTasteProfileModel.__tablename__ == "user_taste_profile"
    assert UserTasteProfileModel.__table_args__ == {"schema": "social"}
    assert "user_id" in UserTasteProfileModel.__table__.columns
    assert "taste_vector" in UserTasteProfileModel.__table__.columns
    assert "last_computed_at" in UserTasteProfileModel.__table__.columns


# -----------------------------------------------------------------------------
# 2. Pydantic Schema Validation Tests
# -----------------------------------------------------------------------------

def test_pydantic_schema_rejects_non_384_dimensions():
    """Verifies that UserTasteProfileUpdate strictly requires exactly 384 dimensions."""
    # 1. Reject vector with less than 384 dimensions
    with pytest.raises(ValidationError) as exc_info:
        UserTasteProfileUpdate(taste_vector=[0.1] * 128)
    assert "taste_vector must have exactly 384 dimensions" in str(exc_info.value)

    # 2. Reject vector with more than 384 dimensions
    with pytest.raises(ValidationError) as exc_info:
        UserTasteProfileUpdate(taste_vector=[0.1] * 385)
    assert "taste_vector must have exactly 384 dimensions" in str(exc_info.value)

    # 3. Reject empty vector
    with pytest.raises(ValidationError) as exc_info:
        UserTasteProfileUpdate(taste_vector=[])
    assert "taste_vector must have exactly 384 dimensions" in str(exc_info.value)

    # 4. Valid 384-dimension vector succeeds
    valid_vector = [0.05] * 384
    schema = UserTasteProfileUpdate(taste_vector=valid_vector)
    assert len(schema.taste_vector) == 384


def test_taste_match_response_schema():
    """Verifies TasteMatchResponse schema and bounds validation."""
    friend_id = uuid.uuid4()
    match = TasteMatchResponse(friend_id=friend_id, compatibility_score=94.5)
    assert match.friend_id == friend_id
    assert match.compatibility_score == 94.5

    # Out-of-bounds compatibility scores
    with pytest.raises(ValidationError):
        TasteMatchResponse(friend_id=friend_id, compatibility_score=-5.0)

    with pytest.raises(ValidationError):
        TasteMatchResponse(friend_id=friend_id, compatibility_score=105.0)


# -----------------------------------------------------------------------------
# 3. Repository Vector Math & Cosine Similarity Tests
# -----------------------------------------------------------------------------

def test_cosine_distance_computation():
    """Verifies mathematical correctness of vector cosine distance calculations."""
    # Identical vectors -> cosine distance = 0.0, similarity = 1.0
    vec_a = [1.0, 2.0, 3.0] + [0.0] * 381
    assert _compute_cosine_distance(vec_a, vec_a) == pytest.approx(0.0, abs=1e-5)

    # Orthogonal vectors -> cosine distance = 1.0, similarity = 0.0
    vec_b = [1.0, 0.0] + [0.0] * 382
    vec_c = [0.0, 1.0] + [0.0] * 382
    assert _compute_cosine_distance(vec_b, vec_c) == pytest.approx(1.0, abs=1e-5)

    # Opposite vectors -> cosine distance = 2.0, similarity = -1.0
    vec_d = [1.0] * 384
    vec_e = [-1.0] * 384
    assert _compute_cosine_distance(vec_d, vec_e) == pytest.approx(2.0, abs=1e-5)


@pytest.mark.anyio
async def test_repository_taste_profile_upsert_and_compatibility():
    """Verifies repository methods for taste profile upsert and similarity matching."""
    user_1 = uuid.uuid4()
    user_2 = uuid.uuid4()
    user_3 = uuid.uuid4()

    # User 1 vector: unit vector along dimension 0
    vec_1 = [1.0] + [0.0] * 383
    # User 2 vector: identical to user 1
    vec_2 = [1.0] + [0.0] * 383
    # User 3 vector: orthogonal to user 1 (dimension 1)
    vec_3 = [0.0, 1.0] + [0.0] * 382

    await social_repository.upsert_taste_profile(db=None, user_id=user_1, taste_vector=vec_1)
    await social_repository.upsert_taste_profile(db=None, user_id=user_2, taste_vector=vec_2)
    await social_repository.upsert_taste_profile(db=None, user_id=user_3, taste_vector=vec_3)

    # Establish ACCEPTED friendships: (1, 2) and (1, 3)
    await social_repository.create_friendship(
        db=None, requester_id=user_1, addressee_id=user_2,
        status="ACCEPTED", trust_score=80.0
    )
    await social_repository.create_friendship(
        db=None, requester_id=user_1, addressee_id=user_3,
        status="ACCEPTED", trust_score=60.0
    )

    # Query compatibility for user_1
    matches = await social_repository.get_taste_compatibility(db=None, user_id=user_1, limit=5)
    assert len(matches) == 2

    # User 2 should have 100.0% compatibility (identical vector)
    assert matches[0].friend_id == user_2
    assert matches[0].compatibility_score == 100.0

    # User 3 should have 0.0% compatibility (orthogonal vector)
    assert matches[1].friend_id == user_3
    assert matches[1].compatibility_score == 0.0


# -----------------------------------------------------------------------------
# 4. API Endpoints Integration Tests
# -----------------------------------------------------------------------------

def test_unauthenticated_vector_endpoints_rejected():
    """Unauthenticated requests to vector endpoints must return HTTP 401."""
    resp_matches = client.get("/social/taste-matches")
    assert resp_matches.status_code == 401

    resp_mock = client.put("/social/taste-profile/mock-compute")
    assert resp_mock.status_code == 401

    resp_update = client.put("/social/taste-profile", json={"taste_vector": [0.1] * 384})
    assert resp_update.status_code == 401


def test_mock_compute_taste_profile_endpoint():
    """Tests PUT /social/taste-profile/mock-compute endpoint."""
    user_id = "018f4a00-0000-7000-8000-000000000101"
    token = get_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.put("/social/taste-profile/mock-compute", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["dimension"] == 384
    assert data["user_id"] == user_id
    assert "last_computed_at" in data


def test_update_taste_profile_endpoint():
    """Tests PUT /social/taste-profile endpoint with valid and invalid payloads."""
    user_id = "018f4a00-0000-7000-8000-000000000102"
    token = get_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid dimension -> 422 Unprocessable Content
    invalid_resp = client.put(
        "/social/taste-profile",
        json={"taste_vector": [0.5] * 100},
        headers=headers,
    )
    assert invalid_resp.status_code in (400, 422)

    # Valid 384 dimensions -> 200 OK
    valid_vector = [0.01 * (i % 10) for i in range(384)]
    valid_resp = client.put(
        "/social/taste-profile",
        json={"taste_vector": valid_vector},
        headers=headers,
    )
    assert valid_resp.status_code == 200
    data = valid_resp.json()
    assert data["status"] == "success"
    assert data["dimension"] == 384


def test_taste_matches_endpoint_integration():
    """
    Tests end-to-end taste matching API flow:
    1. User X and User Y establish friendship.
    2. User X and User Z establish friendship.
    3. User X, User Y, and User Z set taste profiles.
    4. User X queries /social/taste-matches.
    5. Verifies ranking and response format.
    """
    user_x = "018f4a00-0000-7000-8000-000000000201"
    user_y = "018f4a00-0000-7000-8000-000000000202"
    user_z = "018f4a00-0000-7000-8000-000000000203"

    token_x = get_test_token(user_x)
    token_y = get_test_token(user_y)
    token_z = get_test_token(user_z)

    headers_x = {"Authorization": f"Bearer {token_x}"}
    headers_y = {"Authorization": f"Bearer {token_y}"}
    headers_z = {"Authorization": f"Bearer {token_z}"}

    # Setup Friendships: X <-> Y and X <-> Z
    f_xy = client.post("/social/friendships", json={"addressee_id": user_y, "trust_score": 90.0}, headers=headers_x)
    assert f_xy.status_code == 201
    client.patch(f"/social/friendships/{f_xy.json()['friendship_id']}", json={"status": "ACCEPTED"}, headers=headers_y)

    f_xz = client.post("/social/friendships", json={"addressee_id": user_z, "trust_score": 70.0}, headers=headers_x)
    assert f_xz.status_code == 201
    client.patch(f"/social/friendships/{f_xz.json()['friendship_id']}", json={"status": "ACCEPTED"}, headers=headers_z)

    # Set taste profiles
    base_vec = [1.0] + [0.0] * 383
    similar_vec = [0.9] + [0.1] * 383  # Very similar to base
    different_vec = [0.0] * 200 + [1.0] + [0.0] * 183  # Orthogonal to base

    client.put("/social/taste-profile", json={"taste_vector": base_vec}, headers=headers_x)
    client.put("/social/taste-profile", json={"taste_vector": similar_vec}, headers=headers_y)
    client.put("/social/taste-profile", json={"taste_vector": different_vec}, headers=headers_z)

    # User X queries taste matches
    matches_resp = client.get("/social/taste-matches?limit=5", headers=headers_x)
    assert matches_resp.status_code == 200
    matches = matches_resp.json()

    assert len(matches) == 2
    # User Y must be ranked first with higher compatibility score
    assert matches[0]["friend_id"] == user_y
    assert matches[1]["friend_id"] == user_z
    assert matches[0]["compatibility_score"] > matches[1]["compatibility_score"]
