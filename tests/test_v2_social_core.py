# CineVault OS — Test Suite for Module 1: The Social Core (v2.0)
# Validates SQLAlchemy 2.0 models, Pydantic schemas, isolated 'social' schema,
# friendship pre-checks, and the Recommendation State Machine.

import uuid
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.models.social import FriendshipModel, RecommendationModel
from services.api.schemas.social import (
    FriendshipStatusEnum,
    RecommendationStatusEnum,
    RecommendationCreate,
    RecommendationStateUpdate,
    RecommendationResponse,
    ALLOWED_STATE_TRANSITIONS,
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


def get_any_real_title_id() -> str:
    """Returns a real catalog.title UUID. These tests only care about a valid
    title existing (the recommendation state machine doesn't inspect
    canonical_title), but a hardcoded placeholder UUID doesn't exist in the
    real database and trips social.recommendation's title_id foreign key.
    Resolved dynamically rather than hardcoded again so it can't go stale."""
    res = client.get("/v1/titles?limit=1")
    assert res.status_code == 200
    matches = res.json().get("data", [])
    assert matches, "no titles found in the real catalog"
    return matches[0]["id"]


def extract_error_message(resp) -> str:
    """Extracts error message from standardized CineVault RFC 7807 response or FastAPI default."""
    data = resp.json()
    if "error" in data and "message" in data["error"]:
        return data["error"]["message"]
    return data.get("detail", "")


# -----------------------------------------------------------------------------
# 1. Database Model & Schema Isolation Tests
# -----------------------------------------------------------------------------

def test_social_models_schema_isolation():
    """Verifies that FriendshipModel and RecommendationModel belong strictly to 'social' schema."""
    assert FriendshipModel.__tablename__ == "friendship"
    assert FriendshipModel.__table_args__ == {"schema": "social"}
    assert "friendship_id" in FriendshipModel.__table__.columns
    assert "requester_id" in FriendshipModel.__table__.columns
    assert "addressee_id" in FriendshipModel.__table__.columns
    assert "status" in FriendshipModel.__table__.columns
    assert "trust_score" in FriendshipModel.__table__.columns

    assert RecommendationModel.__tablename__ == "recommendation"
    assert RecommendationModel.__table_args__ == {"schema": "social"}
    assert "recommendation_id" in RecommendationModel.__table__.columns
    assert "sender_id" in RecommendationModel.__table__.columns
    assert "recipient_id" in RecommendationModel.__table__.columns
    assert "title_id" in RecommendationModel.__table__.columns
    assert "status" in RecommendationModel.__table__.columns
    assert "sender_predicted_rating" in RecommendationModel.__table__.columns
    assert "recipient_actual_rating" in RecommendationModel.__table__.columns
    assert "context_note" in RecommendationModel.__table__.columns


# -----------------------------------------------------------------------------
# 2. Pydantic Schema & Transition Logic Tests
# -----------------------------------------------------------------------------

def test_pydantic_schema_validation():
    """Verifies Pydantic schema validation rules and rated state constraints."""
    user1 = uuid.uuid4()
    user2 = uuid.uuid4()
    title_id = uuid.uuid4()

    # Valid RecommendationCreate
    create_schema = RecommendationCreate(
        recipient_id=user2,
        title_id=title_id,
        context_note="Must watch classic",
        sender_predicted_rating=9.0,
    )
    assert create_schema.recipient_id == user2
    assert create_schema.sender_predicted_rating == 9.0

    # RecommendationStateUpdate: RATED requires recipient_actual_rating
    with pytest.raises(ValueError, match="recipient_actual_rating is required"):
        RecommendationStateUpdate(
            status=RecommendationStatusEnum.RATED,
            recipient_actual_rating=None,
        )

    # Valid RATED update
    rated_update = RecommendationStateUpdate(
        status=RecommendationStatusEnum.RATED,
        recipient_actual_rating=8.5,
    )
    assert rated_update.recipient_actual_rating == 8.5


# -----------------------------------------------------------------------------
# 3. Social API Endpoints & State Machine Integration Tests
# -----------------------------------------------------------------------------

def test_unauthenticated_requests_rejected():
    """Unauthenticated requests to social endpoints should return HTTP 401."""
    resp = client.post("/social/recommendations", json={
        "recipient_id": str(uuid.uuid4()),
        "title_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 401


def test_recommendation_requires_accepted_friendship():
    """Verify that sending a recommendation fails if sender and recipient are not ACCEPTED friends."""
    sender_id = "018f4a00-0000-7000-8000-000000000001"
    stranger_id = "018f4a00-0000-7000-8000-000000000002"
    title_id = str(uuid.uuid4())

    token = get_test_token(sender_id)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "recipient_id": stranger_id,
        "title_id": title_id,
        "context_note": "You will love this movie!",
        "sender_predicted_rating": 8.5,
    }

    # Should fail because they are not friends
    response = client.post("/social/recommendations", json=payload, headers=headers)
    assert response.status_code == 403
    msg = extract_error_message(response)
    assert "ACCEPTED friends" in msg


def test_full_social_core_and_recommendation_state_machine_lifecycle():
    """
    Tests the complete end-to-end lifecycle:
    1. User A and User B establish an ACCEPTED friendship.
    2. User A creates a recommendation for User B (status: SENT).
    3. User B accepts the recommendation (status: ACCEPTED).
    4. User B marks it as watched (status: WATCHED).
    5. User B rates it (status: RATED, rating: 9.5).
    6. Invalid transitions are properly rejected.
    """
    user_a_id = "018f4a00-0000-7000-8000-000000000010"
    user_b_id = "018f4a00-0000-7000-8000-000000000020"
    title_id = get_any_real_title_id()

    token_a = get_test_token(user_a_id)
    token_b = get_test_token(user_b_id)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Step 1: User A sends friend request to User B
    friend_req_res = client.post(
        "/social/friendships",
        json={"addressee_id": user_b_id, "trust_score": 75.0},
        headers=headers_a,
    )
    assert friend_req_res.status_code == 201
    friendship_data = friend_req_res.json()
    friendship_id = friendship_data["friendship_id"]
    assert friendship_data["status"] == "PENDING"

    # User B accepts the friendship
    accept_res = client.patch(
        f"/social/friendships/{friendship_id}",
        json={"status": "ACCEPTED", "trust_score": 80.0},
        headers=headers_b,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "ACCEPTED"

    # Step 2: User A sends a recommendation to User B (State: SENT)
    rec_payload = {
        "recipient_id": user_b_id,
        "title_id": title_id,
        "context_note": "A masterpiece thriller",
        "sender_predicted_rating": 9.2,
    }
    create_rec_res = client.post(
        "/social/recommendations", json=rec_payload, headers=headers_a
    )
    assert create_rec_res.status_code == 201
    rec_data = create_rec_res.json()
    rec_id = rec_data["recommendation_id"]
    assert rec_data["status"] == "SENT"
    assert rec_data["sender_predicted_rating"] == 9.2
    assert rec_data["recipient_actual_rating"] is None

    # Step 3: Test invalid transition attempt: SENT -> RATED directly (must be rejected)
    invalid_jump_res = client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "RATED", "recipient_actual_rating": 9.0},
        headers=headers_b,
    )
    assert invalid_jump_res.status_code == 400
    msg = extract_error_message(invalid_jump_res)
    assert "Invalid state transition" in msg

    # Step 4: User B updates state: SENT -> ACCEPTED
    accept_rec_res = client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "ACCEPTED"},
        headers=headers_b,
    )
    assert accept_rec_res.status_code == 200
    assert accept_rec_res.json()["status"] == "ACCEPTED"

    # Step 5: User B updates state: ACCEPTED -> WATCHED
    watched_rec_res = client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "WATCHED"},
        headers=headers_b,
    )
    assert watched_rec_res.status_code == 200
    assert watched_rec_res.json()["status"] == "WATCHED"

    # Step 6: User B updates state: WATCHED -> RATED without rating (must fail validation)
    fail_rate_res = client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "RATED"},
        headers=headers_b,
    )
    assert fail_rate_res.status_code in (400, 422)

    # Step 7: User B updates state: WATCHED -> RATED with rating 9.5
    rated_rec_res = client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "RATED", "recipient_actual_rating": 9.5},
        headers=headers_b,
    )
    assert rated_rec_res.status_code == 200
    assert rated_rec_res.json()["status"] == "RATED"
    assert rated_rec_res.json()["recipient_actual_rating"] == 9.5

    # Step 8: Terminal state test: RATED cannot transition back to WATCHED or ACCEPTED
    invalid_from_terminal_res = client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "WATCHED"},
        headers=headers_b,
    )
    assert invalid_from_terminal_res.status_code == 400

    # Step 9: Verify GET /social/recommendations/{id}
    get_rec_res = client.get(f"/social/recommendations/{rec_id}", headers=headers_a)
    assert get_rec_res.status_code == 200
    assert get_rec_res.json()["recommendation_id"] == rec_id

    # Step 10: Verify GET /social/recommendations
    list_rec_res = client.get("/social/recommendations?role=all", headers=headers_a)
    assert list_rec_res.status_code == 200
    assert len(list_rec_res.json()) >= 1


def test_recommendation_rejection_path():
    """Tests the state transition SENT -> REJECTED and verifies terminal rejection state."""
    user_c_id = "018f4a00-0000-7000-8000-000000000040"
    user_d_id = "018f4a00-0000-7000-8000-000000000050"
    title_id = get_any_real_title_id()

    token_c = get_test_token(user_c_id)
    token_d = get_test_token(user_d_id)
    headers_c = {"Authorization": f"Bearer {token_c}"}
    headers_d = {"Authorization": f"Bearer {token_d}"}

    # Setup friendship
    f_res = client.post(
        "/social/friendships",
        json={"addressee_id": user_d_id, "trust_score": 50.0},
        headers=headers_c,
    )
    f_id = f_res.json()["friendship_id"]
    client.patch(
        f"/social/friendships/{f_id}",
        json={"status": "ACCEPTED"},
        headers=headers_d,
    )

    # User C sends recommendation
    rec_res = client.post(
        "/social/recommendations",
        json={"recipient_id": user_d_id, "title_id": title_id, "context_note": "Check this out"},
        headers=headers_c,
    )
    assert rec_res.status_code == 201
    rec_id = rec_res.json()["recommendation_id"]

    # User D rejects the recommendation
    reject_res = client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "REJECTED"},
        headers=headers_d,
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REJECTED"

    # Terminal state: REJECTED -> ACCEPTED must fail
    fail_res = client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "ACCEPTED"},
        headers=headers_d,
    )
    assert fail_res.status_code == 400
