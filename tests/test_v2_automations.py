# CineVault OS — Test Suite for Module 4: Automations & Hooks (v2.0)
# Validates Media Server Webhooks (Plex & Jellyfin), External ID Resolvers,
# Automated State Machine Transitions (ACCEPTED -> WATCHED), and Smart Watchlist Categorization.

import uuid
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.schemas.automation import (
    MediaServerWebhookPayload,
    MediaServerWebhookResponse,
    SmartWatchlistResponse,
    SmartWatchlistItem,
)
from services.api.schemas.social import (
    RecommendationStatusEnum,
    RecommendationCreate,
    RecommendationStateUpdate,
    FriendshipCreate,
    FriendshipUpdate,
    FriendshipStatusEnum,
)
from services.api.repositories.social import (
    social_repository,
    SEED_FRIENDSHIPS,
    SEED_RECOMMENDATIONS,
)
from services.api.repositories.personal import SEED_WATCH_EVENTS
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
# 1. Pydantic Schema Validation Tests
# -----------------------------------------------------------------------------

def test_automation_schemas_validation():
    """Validates structure and serialization of automation schemas."""
    # 1. MediaServerWebhookPayload (Plex format)
    plex_payload = MediaServerWebhookPayload(
        event="media.scrobble",
        Account={"id": 1, "title": "cinephile_alex"},
        Metadata={
            "title": "The Dark Knight",
            "year": 2008,
            "guid": "imdb://tt0468569",
            "Guid": [{"id": "imdb://tt0468569"}, {"id": "tmdb://155"}],
        },
        Player={"title": "Living Room AppleTV"},
    )
    assert plex_payload.event == "media.scrobble"
    assert plex_payload.Account["title"] == "cinephile_alex"
    assert plex_payload.Metadata["guid"] == "imdb://tt0468569"

    # 2. MediaServerWebhookPayload (Jellyfin format)
    jelly_payload = MediaServerWebhookPayload(
        event="ItemFinished",
        User={"Name": "jelly_master", "Id": "usr_999"},
        Item={
            "Name": "Parasite",
            "PremiereDate": "2019-05-30",
            "Provider_imdb": "tt6751668",
            "ProviderIds": {"Imdb": "tt6751668", "Tmdb": "496243"},
        },
    )
    assert jelly_payload.event == "ItemFinished"
    assert jelly_payload.User["Name"] == "jelly_master"
    assert jelly_payload.Item["Provider_imdb"] == "tt6751668"

    # 3. SmartWatchlistResponse
    watchlist_resp = SmartWatchlistResponse(
        weekend_epics=[
            SmartWatchlistItem(
                title_id="018f2e4a-7b31-7000-8000-123456789abd",
                canonical_title="Sholay",
                runtime_minutes=204,
                production_year=1975,
            )
        ],
        quick_watches=[
            SmartWatchlistItem(
                title_id="018f2e4a-7b31-7000-8000-123456789ac4",
                canonical_title="Sacred Games",
                runtime_minutes=50,
                production_year=2018,
            )
        ],
        friend_recommended=[
            SmartWatchlistItem(
                title_id="018f2e4a-7b31-7000-8000-123456789abc",
                canonical_title="Parasite",
                runtime_minutes=132,
                recommendation_note="Masterpiece from Bong Joon-ho",
                recommended_by="user_bob",
            )
        ],
    )
    assert len(watchlist_resp.weekend_epics) == 1
    assert watchlist_resp.weekend_epics[0].runtime_minutes == 204
    assert len(watchlist_resp.quick_watches) == 1
    assert watchlist_resp.quick_watches[0].runtime_minutes == 50
    assert len(watchlist_resp.friend_recommended) == 1


# -----------------------------------------------------------------------------
# 2. Webhook Ingestion Tests (Plex & Jellyfin)
# -----------------------------------------------------------------------------

def test_media_server_webhook_plex_scrobble():
    """Verifies ingestion of a Plex media.scrobble webhook and watch event creation."""
    user_id = str(uuid.uuid4())
    payload = {
        "event": "media.scrobble",
        "Account": {"title": "alex_plex", "id": 42},
        "Metadata": {
            "title": "The Dark Knight",
            "year": 2008,
            "guid": "imdb://tt0468569",
            "Guid": [{"id": "imdb://tt0468569"}, {"id": "tmdb://155"}],
        },
        "Player": {"title": "CineVault Cinema Shield"},
    }

    response = client.post(
        f"/automations/webhooks/media-server?user_id={user_id}",
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event"] == "media.scrobble"
    assert data["title_id"] == "018f2e4a-7b31-7000-8000-123456789abf"  # The Dark Knight
    assert data["canonical_title"] == "The Dark Knight"
    assert "watch_event_id" in data
    assert data["watch_event_id"] is not None


def test_media_server_webhook_jellyfin_item_finished():
    """Verifies ingestion of a Jellyfin ItemFinished webhook and watch event creation."""
    user_id = str(uuid.uuid4())
    payload = {
        "event": "ItemFinished",
        "Account": {},
        "Metadata": {},
        "User": {"Name": "jelly_user", "Id": "usr_jelly_1"},
        "Item": {
            "Name": "Parasite",
            "PremiereDate": "2019-05-30",
            "Provider_imdb": "tt6751668",
            "Provider_tmdb": "496243",
            "ProviderIds": {"Imdb": "tt6751668", "Tmdb": "496243"},
        },
    }

    response = client.post(
        f"/automations/webhooks/media-server?user_id={user_id}",
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event"] == "ItemFinished"
    assert data["title_id"] == "018f2e4a-7b31-7000-8000-123456789abc"  # Parasite
    assert data["canonical_title"] == "Parasite"


# -----------------------------------------------------------------------------
# 3. Social Hook: Auto-Transition ACCEPTED Recommendation -> WATCHED
# -----------------------------------------------------------------------------

def test_webhook_auto_transitions_accepted_recommendation():
    """
    Core Automation Hook Test:
    1. User A and User B are accepted friends.
    2. User A sends a recommendation for 'Parasite' to User B.
    3. User B accepts the recommendation (status becomes ACCEPTED).
    4. External Media Server sends a scrobble webhook indicating User B finished 'Parasite'.
    5. The webhook listener MUST automatically transition the recommendation status to WATCHED.
    """
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = get_test_token(user_a)
    token_b = get_test_token(user_b)
    parasite_id = "018f2e4a-7b31-7000-8000-123456789abc"

    # Step 1: Establish friendship between User A and User B
    req_resp = client.post(
        "/social/friendships",
        json={"addressee_id": user_b},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert req_resp.status_code == 201
    friendship_id = req_resp.json()["friendship_id"]

    # User B accepts friendship
    accept_resp = client.patch(
        f"/social/friendships/{friendship_id}",
        json={"status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert accept_resp.status_code == 200

    # Step 2: User A recommends Parasite to User B
    rec_resp = client.post(
        "/social/recommendations",
        json={
            "recipient_id": user_b,
            "title_id": parasite_id,
            "sender_predicted_rating": 9.5,
            "context_note": "You have to watch this Oscar winner!",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert rec_resp.status_code == 201
    rec_id = rec_resp.json()["recommendation_id"]
    assert rec_resp.json()["status"] == "SENT"

    # Step 3: User B accepts the recommendation
    state_resp = client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert state_resp.status_code == 200
    assert state_resp.json()["status"] == "ACCEPTED"

    # Step 4: External Webhook POST (Plex/Jellyfin scrobble for User B watching Parasite)
    webhook_payload = {
        "event": "media.scrobble",
        "Account": {"username": f"user_{user_b[-6:]}"},
        "Metadata": {
            "title": "Parasite",
            "guid": "imdb://tt6751668",
            "year": 2019,
        },
    }

    webhook_resp = client.post(
        f"/automations/webhooks/media-server?user_id={user_b}",
        json=webhook_payload,
    )
    assert webhook_resp.status_code == 200
    wb_data = webhook_resp.json()
    assert wb_data["social_recommendation_updated"] is True
    assert wb_data["recommendation_id"] == rec_id

    # Step 5: Verify the recommendation has transitioned to WATCHED
    check_rec = client.get(
        f"/social/recommendations/{rec_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert check_rec.status_code == 200
    assert check_rec.json()["status"] == "WATCHED"


def test_webhook_does_not_transition_non_accepted_recommendations():
    """Ensures recommendations in SENT or REJECTED states are NOT transitioned by webhooks."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = get_test_token(user_a)
    token_b = get_test_token(user_b)
    dark_knight_id = "018f2e4a-7b31-7000-8000-123456789abf"

    # Establish friendship
    req_resp = client.post(
        "/social/friendships",
        json={"addressee_id": user_b},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    friendship_id = req_resp.json()["friendship_id"]
    client.patch(
        f"/social/friendships/{friendship_id}",
        json={"status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User A recommends The Dark Knight to User B (Leaves in 'SENT' status)
    rec_resp = client.post(
        "/social/recommendations",
        json={
            "recipient_id": user_b,
            "title_id": dark_knight_id,
            "sender_predicted_rating": 10.0,
            "context_note": "Greatest superhero film ever made.",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    rec_id = rec_resp.json()["recommendation_id"]
    assert rec_resp.json()["status"] == "SENT"

    # User B scrobbles The Dark Knight via webhook
    webhook_payload = {
        "event": "media.scrobble",
        "Account": {"username": f"user_{user_b[-6:]}"},
        "Metadata": {
            "title": "The Dark Knight",
            "guid": "imdb://tt0468569",
            "year": 2008,
        },
    }
    webhook_resp = client.post(
        f"/automations/webhooks/media-server?user_id={user_b}",
        json=webhook_payload,
    )
    assert webhook_resp.status_code == 200
    assert webhook_resp.json()["social_recommendation_updated"] is False

    # Status must still be SENT (state machine rule: SENT cannot jump to WATCHED)
    check_rec = client.get(
        f"/social/recommendations/{rec_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert check_rec.status_code == 200
    assert check_rec.json()["status"] == "SENT"


# -----------------------------------------------------------------------------
# 4. Smart Watchlist Partitioning & Filter Tests
# -----------------------------------------------------------------------------

def test_smart_watchlist_categorization_logic():
    """
    Tests Smart Watchlist grouping:
    - weekend_epics: strictly > 150 mins
    - quick_watches: strictly < 100 mins
    - friend_recommended: ACCEPTED recommendations
    """
    user_id = str(uuid.uuid4())
    token = get_test_token(user_id)

    # Clear watch events for this fresh user
    SEED_WATCH_EVENTS[user_id] = []

    response = client.get(
        "/automations/smart-watchlist",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "weekend_epics" in data
    assert "quick_watches" in data
    assert "friend_recommended" in data

    weekend_epics = data["weekend_epics"]
    quick_watches = data["quick_watches"]

    # Verify weekend epics runtime constraint (> 150 mins)
    assert len(weekend_epics) > 0
    for item in weekend_epics:
        assert item["runtime_minutes"] is not None
        assert item["runtime_minutes"] > 150, f"Title {item['canonical_title']} runtime {item['runtime_minutes']} <= 150"

    # Verify quick watches runtime constraint (< 100 mins)
    assert len(quick_watches) > 0
    for item in quick_watches:
        assert item["runtime_minutes"] is not None
        assert item["runtime_minutes"] < 100, f"Title {item['canonical_title']} runtime {item['runtime_minutes']} >= 100"


def test_smart_watchlist_friend_recommended_inclusion():
    """Verifies that ACCEPTED recommendations appear in the friend_recommended category."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = get_test_token(user_a)
    token_b = get_test_token(user_b)
    inception_id = "018f2e4a-7b31-7000-8000-123456789ac0"  # Inception (148 mins)

    # Establish friendship
    req_resp = client.post(
        "/social/friendships",
        json={"addressee_id": user_b},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    friendship_id = req_resp.json()["friendship_id"]
    client.patch(
        f"/social/friendships/{friendship_id}",
        json={"status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User A recommends Inception to User B
    rec_resp = client.post(
        "/social/recommendations",
        json={
            "recipient_id": user_b,
            "title_id": inception_id,
            "sender_predicted_rating": 9.2,
            "context_note": "Mind-bending dream architecture!",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    rec_id = rec_resp.json()["recommendation_id"]

    # User B accepts recommendation
    client.patch(
        f"/social/recommendations/{rec_id}",
        json={"status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User B requests Smart Watchlist
    watchlist_resp = client.get(
        "/automations/smart-watchlist",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert watchlist_resp.status_code == 200
    wl_data = watchlist_resp.json()

    friend_recs = wl_data["friend_recommended"]
    assert len(friend_recs) >= 1

    matching_recs = [r for r in friend_recs if r["title_id"] == inception_id]
    assert len(matching_recs) == 1
    rec_item = matching_recs[0]
    assert rec_item["canonical_title"] == "Inception"
    assert rec_item["recommendation_note"] == "Mind-bending dream architecture!"
    assert rec_item["recommended_by"] == user_a
