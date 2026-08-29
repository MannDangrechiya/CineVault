# CineVault OS — Test Suite for Module 3: The AI Brain (v2.0)
# Validates the self-hosted embedding service, Vector Group Matchmaking math,
# Taste Profile real vector computation, and AI API endpoints with mocked calls.

import asyncio
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.database import AsyncSessionLocal
from services.api.ai import embedding_service
from services.api.routers.ai import compute_average_group_vector
from services.api.schemas.ai import GroupMatchRequest, GroupMatchResponse
from services.api.schemas.social import TasteProfileComputeRequest
from services.api.schemas.recommendations import (
    RecommendationListResponse,
    RecommendationItemResponse,
    RecommendationModeEnum,
    GroundedExplanation,
)
from services.api.repositories.social import (
    social_repository,
    SEED_FRIENDSHIPS,
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


def extract_error_message(resp) -> str:
    """Extracts error message from standardized CineVault RFC 7807 response or FastAPI default."""
    data = resp.json()
    if "error" in data and "message" in data["error"]:
        return data["error"]["message"]
    return data.get("detail", "")


# =============================================================================
# 1. Embedding Service Unit Tests (Isolated Mocking — no real model load)
# =============================================================================

@pytest.mark.anyio
async def test_embedding_service_generate_embedding_success(monkeypatch):
    """Verifies generate_embedding returns a 384-dim vector from the (mocked) model."""
    mock_vector = [0.01 * (i % 10) for i in range(384)]

    class _FakeVector:
        def tolist(self):
            return mock_vector

    class _FakeModel:
        def encode(self, text, normalize_embeddings=True):
            assert text == "Sci-fi cyberpunk and time travel"
            return _FakeVector()

    monkeypatch.setattr(embedding_service, "_get_model", lambda: _FakeModel())

    result = await embedding_service.generate_embedding("Sci-fi cyberpunk and time travel")

    assert len(result) == 384
    assert result == mock_vector


@pytest.mark.anyio
async def test_embedding_service_generate_embedding_validation():
    """Empty/whitespace-only input raises ValueError before touching the model."""
    with pytest.raises(ValueError, match="cannot be empty"):
        await embedding_service.generate_embedding("")

    with pytest.raises(ValueError, match="cannot be empty"):
        await embedding_service.generate_embedding("   ")


@pytest.mark.anyio
async def test_embedding_service_generate_embedding_model_failure(monkeypatch):
    """A model-load/encode failure is wrapped into a RuntimeError."""

    def _raise():
        raise RuntimeError("model failed to load")

    monkeypatch.setattr(embedding_service, "_get_model", _raise)

    with pytest.raises(RuntimeError, match="Embedding generation failed"):
        await embedding_service.generate_embedding("test query")


# =============================================================================
# 2. Mathematical Mean & Group Vector Calculation Tests
# =============================================================================

def test_compute_average_group_vector_mathematical_mean():
    """Verifies the mathematical mean vector computation across multiple group members."""
    # 3 group members with 384-dimensional vectors
    vec_1 = [1.0, 2.0, 3.0] + [0.0] * 381
    vec_2 = [3.0, 4.0, 5.0] + [3.0] * 381
    vec_3 = [2.0, 3.0, 4.0] + [6.0] * 381

    # Expected mean: [ (1+3+2)/3, (2+4+3)/3, (3+5+4)/3, (0+3+6)/3, ... ] = [2.0, 3.0, 4.0, 3.0, ...]
    mean_vec = compute_average_group_vector([vec_1, vec_2, vec_3])

    assert len(mean_vec) == 384
    assert mean_vec[0] == pytest.approx(2.0, abs=1e-5)
    assert mean_vec[1] == pytest.approx(3.0, abs=1e-5)
    assert mean_vec[2] == pytest.approx(4.0, abs=1e-5)
    assert mean_vec[3] == pytest.approx(3.0, abs=1e-5)


def test_compute_average_group_vector_single_vector():
    """A group with a single member should have a mean vector identical to their individual vector."""
    vec = [0.25] * 384
    mean_vec = compute_average_group_vector([vec])
    assert mean_vec == vec


def test_compute_average_group_vector_errors():
    """Verifies validation rules for empty vector lists and dimension mismatches."""
    # Empty list
    with pytest.raises(ValueError, match="empty list"):
        compute_average_group_vector([])

    # Dimension mismatch
    vec_a = [1.0, 2.0, 3.0]
    vec_b = [1.0, 2.0]
    with pytest.raises(ValueError, match="expected 3"):
        compute_average_group_vector([vec_a, vec_b])


# =============================================================================
# 3. Pydantic Schemas Validation Tests
# =============================================================================

def test_pydantic_ai_schemas_validation():
    """Verifies validation rules on AI module request models."""
    uid = uuid.uuid4()

    # Valid GroupMatchRequest
    req = GroupMatchRequest(friend_ids=[uid], mood="Action thriller")
    assert req.friend_ids == [uid]
    assert req.mood == "Action thriller"

    # Empty friend_ids list
    with pytest.raises(ValidationError):
        GroupMatchRequest(friend_ids=[], mood="Action")

    # Valid TasteProfileComputeRequest
    comp_req = TasteProfileComputeRequest(taste_summary="I love sci-fi and action")
    assert comp_req.taste_summary == "I love sci-fi and action"

    # Empty taste_summary
    with pytest.raises(ValidationError):
        TasteProfileComputeRequest(taste_summary="")


# =============================================================================
# 4. API Endpoints Integration Tests (Mocked embedding service / AI provider)
# =============================================================================

def test_unauthenticated_endpoints_rejected():
    """Unauthenticated requests to AI endpoints must return HTTP 401."""
    # POST /social/taste-profile/compute
    resp_compute = client.post(
        "/social/taste-profile/compute",
        json={"taste_summary": "I love classic cinema"},
    )
    assert resp_compute.status_code == 401

    # POST /ai/group-matchmaking
    resp_match = client.post(
        "/ai/group-matchmaking",
        json={"friend_ids": [str(uuid.uuid4())], "mood": "chill comedy"},
    )
    assert resp_match.status_code == 401


def test_post_taste_profile_compute_endpoint_success():
    """
    Tests POST /social/taste-profile/compute:
    1. Sends taste summary.
    2. The self-hosted embedding service generates a 384-dimensional vector.
    3. Vector is persisted in repository.
    """
    user_id = "018f4a00-0000-7000-8000-000000000301"
    token = get_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    mock_vec = [0.02 * (i % 10) for i in range(384)]

    with patch("services.api.ai.embedding_service.generate_embedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_vec

        payload = {"taste_summary": "I love mind-bending psychological thrillers and cyberpunk aesthetics"}
        resp = client.post("/social/taste-profile/compute", json=payload, headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["user_id"] == user_id
        assert data["dimension"] == 384
        assert "last_computed_at" in data

        mock_embed.assert_called_once_with(payload["taste_summary"])

    # Verify the vector was actually persisted in Postgres (social.user_taste_profile),
    # not just the in-memory SEED_TASTE_PROFILES fallback dict used when db=None.
    async def _fetch_persisted_profile():
        async with AsyncSessionLocal() as session:
            return await social_repository.get_taste_profile(db=session, user_id=user_id)

    persisted = asyncio.run(_fetch_persisted_profile())
    assert persisted is not None
    assert list(persisted["taste_vector"]) == mock_vec


def test_post_taste_profile_compute_embedding_failure_returns_502():
    """When embedding generation fails, POST /social/taste-profile/compute returns HTTP 502."""
    user_id = "018f4a00-0000-7000-8000-000000000302"
    token = get_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    with patch("services.api.ai.embedding_service.generate_embedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.side_effect = RuntimeError("Embedding generation failed: model unavailable")

        payload = {"taste_summary": "Horror and mystery"}
        resp = client.post("/social/taste-profile/compute", json=payload, headers=headers)

        assert resp.status_code == 502
        msg = extract_error_message(resp)
        assert "Embedding computation failed" in msg


def test_group_matchmaking_rejects_non_friends():
    """Verify that group matchmaking is rejected (HTTP 403) if any requested user is not an ACCEPTED friend."""
    user_a = "018f4a00-0000-7000-8000-000000000401"
    stranger = "018f4a00-0000-7000-8000-000000000402"

    token_a = get_test_token(user_a)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    payload = {
        "friend_ids": [stranger],
        "mood": "High energy action",
    }

    resp = client.post("/ai/group-matchmaking", json=payload, headers=headers_a)
    assert resp.status_code == 403
    msg = extract_error_message(resp)
    assert "not an ACCEPTED friend" in msg


def _fake_recommendation_item(canonical_title: str, score: float) -> RecommendationItemResponse:
    """Builds a minimal valid recommendation item for mocking get_recommendations()."""
    return RecommendationItemResponse(
        title_id=str(uuid.uuid4()),
        display_id=f"MOV-{canonical_title[:3].upper()}",
        canonical_title=canonical_title,
        content_type="MOVIE",
        recommendation_score=score,
        explanation=GroundedExplanation(explanation_text="test fixture"),
    )


def test_group_matchmaking_end_to_end_lifecycle():
    """
    Tests complete Group Matchmaking flow:
    1. User 1 and User 2 become ACCEPTED friends.
    2. User 1 and User 3 become ACCEPTED friends.
    3. User 1, 2, and 3 have 384-dimensional taste profiles.
    4. User 1 initiates group matchmaking for all 3 members.
    5. The configured AI provider generates a group consensus recommendation,
       grounded in real candidate titles from the recommendations pipeline.
    6. Verifies response payload, recommended titles, and consensus vector.
    """
    user_1 = "018f4a00-0000-7000-8000-000000000501"
    user_2 = "018f4a00-0000-7000-8000-000000000502"
    user_3 = "018f4a00-0000-7000-8000-000000000503"

    token_1 = get_test_token(user_1)
    token_2 = get_test_token(user_2)
    token_3 = get_test_token(user_3)

    headers_1 = {"Authorization": f"Bearer {token_1}"}
    headers_2 = {"Authorization": f"Bearer {token_2}"}
    headers_3 = {"Authorization": f"Bearer {token_3}"}

    # Step 1: Establish Friendships (1 <-> 2) and (1 <-> 3)
    f_12 = client.post("/social/friendships", json={"addressee_id": user_2, "trust_score": 85.0}, headers=headers_1)
    assert f_12.status_code == 201
    client.patch(f"/social/friendships/{f_12.json()['friendship_id']}", json={"status": "ACCEPTED"}, headers=headers_2)

    f_13 = client.post("/social/friendships", json={"addressee_id": user_3, "trust_score": 75.0}, headers=headers_1)
    assert f_13.status_code == 201
    client.patch(f"/social/friendships/{f_13.json()['friendship_id']}", json={"status": "ACCEPTED"}, headers=headers_3)

    # Step 2: Set taste profiles for all 3 users
    vec_1 = [1.0] + [0.0] * 383
    vec_2 = [0.0, 1.0] + [0.0] * 382
    vec_3 = [0.0, 0.0, 1.0] + [0.0] * 381

    client.put("/social/taste-profile", json={"taste_vector": vec_1}, headers=headers_1)
    client.put("/social/taste-profile", json={"taste_vector": vec_2}, headers=headers_2)
    client.put("/social/taste-profile", json={"taste_vector": vec_3}, headers=headers_3)

    # Step 3: Mock the recommendations pipeline (real candidate titles) and
    # the configured AI provider's response generation.
    oracle_response = (
        "As CineVault Oracle, based on your group mood 'Mind-Bending Sci-Fi Night', "
        "I recommend Inception, Interstellar, and Blade Runner 2049. "
        "These films offer the perfect synthesis of your group's love for intricate plots and visionary world-building."
    )
    fake_recs = RecommendationListResponse(
        mode=RecommendationModeEnum.TONIGHT,
        total=3,
        is_cold_start=False,
        data=[
            _fake_recommendation_item("Inception", 92.0),
            _fake_recommendation_item("Interstellar", 90.0),
            _fake_recommendation_item("Blade Runner 2049", 88.0),
        ],
    )
    mock_provider = MagicMock()
    mock_provider.generate_assistant_response = AsyncMock(return_value=oracle_response)

    with patch(
        "services.api.routers.ai.recommendation_repository.get_recommendations",
        new_callable=AsyncMock,
        return_value=fake_recs,
    ), patch(
        "services.api.routers.ai.AIProviderFactory.get_provider",
        return_value=mock_provider,
    ):
        # Step 4: Initiate Group Matchmaking
        payload = {
            "friend_ids": [user_2, user_3],
            "mood": "Mind-Bending Sci-Fi Night",
        }
        resp = client.post("/ai/group-matchmaking", json=payload, headers=headers_1)

        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "success"
        assert data["mood"] == "Mind-Bending Sci-Fi Night"
        assert data["group_size"] == 3
        assert len(data["group_member_ids"]) == 3
        assert data["recommended_titles"] == ["Inception", "Interstellar", "Blade Runner 2049"]
        assert data["ai_recommendation"] == oracle_response
        assert data["group_vector_preview"] is not None
        assert len(data["group_vector_preview"]) == 5

        # Check the request sent to the AI provider is grounded in the real
        # candidate titles and carries the group's mood.
        mock_provider.generate_assistant_response.assert_called_once()
        call_kwargs = mock_provider.generate_assistant_response.call_args.kwargs
        assert "Mind-Bending Sci-Fi Night" in call_kwargs["sanitized_query"]
        assert [t["canonical_title"] for t in call_kwargs["matched_titles"]] == [
            "Inception",
            "Interstellar",
            "Blade Runner 2049",
        ]


def test_group_matchmaking_ai_provider_failure_returns_502():
    """When the AI provider fails during matchmaking, returns HTTP 502."""
    user_a = "018f4a00-0000-7000-8000-000000000601"
    user_b = "018f4a00-0000-7000-8000-000000000602"

    token_a = get_test_token(user_a)
    token_b = get_test_token(user_b)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Setup friendship
    f_res = client.post("/social/friendships", json={"addressee_id": user_b}, headers=headers_a)
    client.patch(f"/social/friendships/{f_res.json()['friendship_id']}", json={"status": "ACCEPTED"}, headers=headers_b)

    mock_provider = MagicMock()
    mock_provider.generate_assistant_response = AsyncMock(side_effect=RuntimeError("AI provider timeout"))
    empty_recs = RecommendationListResponse(mode=RecommendationModeEnum.TONIGHT, total=0, is_cold_start=True, data=[])

    with patch(
        "services.api.routers.ai.recommendation_repository.get_recommendations",
        new_callable=AsyncMock,
        return_value=empty_recs,
    ), patch(
        "services.api.routers.ai.AIProviderFactory.get_provider",
        return_value=mock_provider,
    ):
        payload = {"friend_ids": [user_b], "mood": "Action"}
        resp = client.post("/ai/group-matchmaking", json=payload, headers=headers_a)

        assert resp.status_code == 502
        msg = extract_error_message(resp)
        assert "AI group matchmaking generation failed" in msg
