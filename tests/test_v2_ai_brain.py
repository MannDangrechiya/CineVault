# CineVault OS — Test Suite for Module 3: The AI Brain (v2.0)
# Validates OllamaClient (embeddings & chat), Vector Group Matchmaking math,
# Taste Profile real vector computation, and AI API endpoints with mocked HTTP calls.

import uuid
from unittest.mock import patch, AsyncMock
import httpx
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.ai.ollama_client import OllamaClient
from services.api.routers.ai import compute_average_group_vector
from services.api.schemas.ai import GroupMatchRequest, GroupMatchResponse
from services.api.schemas.social import TasteProfileComputeRequest
from services.api.repositories.social import (
    social_repository,
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


def extract_error_message(resp) -> str:
    """Extracts error message from standardized CineVault RFC 7807 response or FastAPI default."""
    data = resp.json()
    if "error" in data and "message" in data["error"]:
        return data["error"]["message"]
    return data.get("detail", "")


# =============================================================================
# 1. OllamaClient Unit Tests (Isolated Mocking)
# =============================================================================

@pytest.mark.anyio
async def test_ollama_client_generate_embedding_success():
    """Verifies OllamaClient correctly calls /api/embeddings and parses 384-dim vector."""
    mock_vector = [0.01 * (i % 10) for i in range(384)]
    mock_response = httpx.Response(
        status_code=200,
        json={"embedding": mock_vector},
        request=httpx.Request("POST", "http://localhost:11434/api/embeddings"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        ollama = OllamaClient(base_url="http://localhost:11434")
        result = await ollama.generate_embedding("Sci-fi cyberpunk and time travel")

        assert len(result) == 384
        assert result == mock_vector
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:11434/api/embeddings"
        assert kwargs["json"]["model"] == "all-minilm"
        assert kwargs["json"]["prompt"] == "Sci-fi cyberpunk and time travel"


@pytest.mark.anyio
async def test_ollama_client_generate_embedding_batch_format():
    """Verifies OllamaClient compatibility with batch format embeddings."""
    mock_vector = [0.05] * 384
    mock_response = httpx.Response(
        status_code=200,
        json={"embeddings": [mock_vector]},
        request=httpx.Request("POST", "http://localhost:11434/api/embeddings"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        ollama = OllamaClient()
        result = await ollama.generate_embedding("Space opera and psychological thriller")
        assert len(result) == 384
        assert result == mock_vector


@pytest.mark.anyio
async def test_ollama_client_generate_embedding_validation_and_errors():
    """Verifies input validation and exception handling in generate_embedding."""
    ollama = OllamaClient()

    # Empty text raises ValueError
    with pytest.raises(ValueError, match="cannot be empty"):
        await ollama.generate_embedding("")

    with pytest.raises(ValueError, match="cannot be empty"):
        await ollama.generate_embedding("   ")

    # HTTP 500 raises RuntimeError
    err_response = httpx.Response(
        status_code=500,
        text="Internal Server Error",
        request=httpx.Request("POST", "http://localhost:11434/api/embeddings"),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = err_response
        with pytest.raises(RuntimeError, match="Ollama API HTTP 500"):
            await ollama.generate_embedding("test query")


@pytest.mark.anyio
async def test_ollama_client_generate_chat_success():
    """Verifies OllamaClient correctly calls /api/generate and extracts response."""
    ai_text = "Here are 3 movies for your movie night: Inception, Interstellar, and Blade Runner 2049."
    mock_response = httpx.Response(
        status_code=200,
        json={"response": ai_text, "done": True},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        ollama = OllamaClient(chat_model="mistral")
        result = await ollama.generate_chat("Recommend movies for a sci-fi group")

        assert result == ai_text
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:11434/api/generate"
        assert kwargs["json"]["model"] == "mistral"
        assert kwargs["json"]["stream"] is False


@pytest.mark.anyio
async def test_ollama_client_generate_chat_validation_and_errors():
    """Verifies validation and error handling in generate_chat."""
    ollama = OllamaClient()

    # Empty prompt raises ValueError
    with pytest.raises(ValueError, match="cannot be empty"):
        await ollama.generate_chat("")

    # Connection error raises RuntimeError
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        with pytest.raises(RuntimeError, match="Could not connect to Ollama"):
            await ollama.generate_chat("test prompt")


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
# 4. API Endpoints Integration Tests (Mocked Ollama)
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
    2. Ollama generates 384-dimensional vector embedding.
    3. Vector is persisted in repository.
    """
    user_id = "018f4a00-0000-7000-8000-000000000301"
    token = get_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    mock_vec = [0.02 * (i % 10) for i in range(384)]

    with patch("services.api.ai.ollama_client.OllamaClient.generate_embedding", new_callable=AsyncMock) as mock_embed:
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

    # Verify vector was persisted in in-memory / db repository
    u_uuid = uuid.UUID(user_id)
    assert u_uuid in SEED_TASTE_PROFILES
    assert SEED_TASTE_PROFILES[u_uuid]["taste_vector"] == mock_vec


def test_post_taste_profile_compute_ollama_failure_returns_502():
    """When Ollama is unreachable, POST /social/taste-profile/compute returns HTTP 502."""
    user_id = "018f4a00-0000-7000-8000-000000000302"
    token = get_test_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    with patch("services.api.ai.ollama_client.OllamaClient.generate_embedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.side_effect = RuntimeError("Could not connect to Ollama at http://localhost:11434")

        payload = {"taste_summary": "Horror and mystery"}
        resp = client.post("/social/taste-profile/compute", json=payload, headers=headers)

        assert resp.status_code == 502
        msg = extract_error_message(resp)
        assert "Ollama embedding computation failed" in msg


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


def test_group_matchmaking_end_to_end_lifecycle():
    """
    Tests complete Group Matchmaking flow:
    1. User 1 and User 2 become ACCEPTED friends.
    2. User 1 and User 3 become ACCEPTED friends.
    3. User 1, 2, and 3 have 384-dimensional taste profiles.
    4. User 1 initiates group matchmaking for all 3 members.
    5. Ollama AI Brain generates group consensus movie recommendation.
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

    # Step 3: Mock Ollama chat generation
    oracle_response = (
        "As CineVault Oracle, based on your group mood 'Mind-Bending Sci-Fi Night', "
        "I recommend Inception, Interstellar, and Blade Runner 2049. "
        "These films offer the perfect synthesis of your group's love for intricate plots and visionary world-building."
    )

    with patch("services.api.ai.ollama_client.OllamaClient.generate_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = oracle_response

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

        # Check that prompt sent to Ollama contains the Oracle prompt structure
        mock_chat.assert_called_once()
        prompt_arg = mock_chat.call_args[1]["prompt"]
        assert "CineVault Oracle" in prompt_arg
        assert "Mind-Bending Sci-Fi Night" in prompt_arg
        assert "Inception, Interstellar, Blade Runner 2049" in prompt_arg


def test_group_matchmaking_ollama_failure_returns_502():
    """When Ollama chat generation fails during matchmaking, returns HTTP 502."""
    user_a = "018f4a00-0000-7000-8000-000000000601"
    user_b = "018f4a00-0000-7000-8000-000000000602"

    token_a = get_test_token(user_a)
    token_b = get_test_token(user_b)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Setup friendship
    f_res = client.post("/social/friendships", json={"addressee_id": user_b}, headers=headers_a)
    client.patch(f"/social/friendships/{f_res.json()['friendship_id']}", json={"status": "ACCEPTED"}, headers=headers_b)

    with patch("services.api.ai.ollama_client.OllamaClient.generate_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = RuntimeError("Ollama service timeout")

        payload = {"friend_ids": [user_b], "mood": "Action"}
        resp = client.post("/ai/group-matchmaking", json=payload, headers=headers_a)

        assert resp.status_code == 502
        msg = extract_error_message(resp)
        assert "Ollama AI chat generation failed" in msg
