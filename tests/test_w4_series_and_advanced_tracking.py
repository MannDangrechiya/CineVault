# CineVault OS — Phase W4 Series & Advanced Watch Tracking Test Suite
# Tests all Episodic Series & Watch Tracking Endpoints against REAL PostgreSQL:
# 1. Canonical Series Lookups by UUID and display_id (e.g. TV-000001) & Stable Season/Episode Ordering
# 2. Episode Watch Event Creation & Persistence (season_id, episode_id)
# 3. Series-scoped Watch Events Query (GET /v1/me/watch-events?title_id=...)
# 4. Episode Rewatch Behavior (Multiple append-only records)
# 5. Series State Transitions: Partial Watching -> "WATCHING" vs All Episodes -> "COMPLETED"
# 6. User Isolation (User A episode watch does not leak to User B)
# 7. Watch History Episodic Enrichment (season_number, episode_number, episode_name)
# 8. User Streak Progression on Episode Watch
# 9. Watch Event Soft-Delete (Tombstone) Preserves Audit Log

import asyncio
import time
import base64
import json
import uuid
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.database import get_db, AsyncSessionLocal
from services.api.models.canonical import TitleModel, SeasonModel, EpisodeModel

def generate_mock_jwt(roles: list, sub: str = "w4-test-user-1") -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    now = int(time.time())
    payload_dict = {
        "sub": sub,
        "iss": "http://localhost:8080/realms/cinevault-dev",
        "aud": "cinevault-api-gateway",
        "exp": now + 900,
        "iat": now,
        "realm_access": {"roles": roles}
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"mock_signature").decode().rstrip("=")
    return f"{header}.{payload}.{signature}"

@pytest.fixture(autouse=True)
def clean_db_dependency():
    app.dependency_overrides.pop(get_db, None)
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def user1_headers():
    token = generate_mock_jwt(["AuthenticatedUser"], sub=f"w4-user-{uuid.uuid4().hex[:8]}")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def user2_headers():
    token = generate_mock_jwt(["AuthenticatedUser"], sub=f"w4-user-{uuid.uuid4().hex[:8]}")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def w4_series():
    """Ensures a dedicated TV series with 2 seasons and 4 total episodes exists in real PostgreSQL."""
    async def _setup():
        async with AsyncSessionLocal() as session:
            title_uuid = uuid.uuid4()
            unique_name = f"CineVault W4 Master Series {uuid.uuid4().hex[:6]}"
            series_title = TitleModel(
                title_id=title_uuid,
                display_id=f"TV-W4-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="tv_series",
                canonical_title=unique_name,
                original_title=unique_name,
                production_year=2026,
            )
            session.add(series_title)
            await session.flush()

            # Season 1: Episodes 1 & 2
            s1_id = uuid.uuid4()
            s1 = SeasonModel(
                season_id=s1_id,
                title_id=title_uuid,
                season_number=1,
                season_name="Season 1",
            )
            ep1_id = uuid.uuid4()
            ep1 = EpisodeModel(
                episode_id=ep1_id,
                season_id=s1_id,
                episode_number=1,
                episode_name="Pilot Episode",
                runtime_minutes=50,
            )
            ep2_id = uuid.uuid4()
            ep2 = EpisodeModel(
                episode_id=ep2_id,
                season_id=s1_id,
                episode_number=2,
                episode_name="Second Episode",
                runtime_minutes=48,
            )

            # Season 2: Episodes 1 & 2
            s2_id = uuid.uuid4()
            s2 = SeasonModel(
                season_id=s2_id,
                title_id=title_uuid,
                season_number=2,
                season_name="Season 2",
            )
            ep3_id = uuid.uuid4()
            ep3 = EpisodeModel(
                episode_id=ep3_id,
                season_id=s2_id,
                episode_number=1,
                episode_name="Return Episode",
                runtime_minutes=52,
            )
            ep4_id = uuid.uuid4()
            ep4 = EpisodeModel(
                episode_id=ep4_id,
                season_id=s2_id,
                episode_number=2,
                episode_name="Season Finale",
                runtime_minutes=55,
            )

            session.add_all([s1, ep1, ep2, s2, ep3, ep4])
            await session.commit()

            return {
                "title_id": str(title_uuid),
                "display_id": series_title.display_id,
                "season1_id": str(s1_id),
                "season2_id": str(s2_id),
                "episodes": [
                    {"id": str(ep1_id), "season_id": str(s1_id), "season_number": 1, "episode_number": 1, "name": "Pilot Episode"},
                    {"id": str(ep2_id), "season_id": str(s1_id), "season_number": 1, "episode_number": 2, "name": "Second Episode"},
                    {"id": str(ep3_id), "season_id": str(s2_id), "season_number": 2, "episode_number": 1, "name": "Return Episode"},
                    {"id": str(ep4_id), "season_id": str(s2_id), "season_number": 2, "episode_number": 2, "name": "Season Finale"},
                ]
            }

    return asyncio.run(_setup())

def test_w4_series_lookup_and_ordering(client, w4_series):
    """Verifies series lookup by UUID/display_id and deterministic ordering of seasons & episodes."""
    series_id = w4_series["title_id"]
    display_id = w4_series["display_id"]

    # 1. Lookup by UUID
    res_uuid = client.get(f"/v1/titles/{series_id}")
    assert res_uuid.status_code == 200
    data = res_uuid.json()
    assert data["id"] == series_id
    assert "seasons" in data
    assert len(data["seasons"]) == 2

    # Verify seasons are sorted by season_number
    season_numbers = [s["season_number"] for s in data["seasons"]]
    assert season_numbers == [1, 2]

    # Verify episodes within each season are sorted by episode_number
    for s in data["seasons"]:
        ep_numbers = [ep["episode_number"] for ep in s["episodes"]]
        assert ep_numbers == sorted(ep_numbers)

    # 2. Lookup by display_id
    res_disp = client.get(f"/v1/titles/{display_id}")
    assert res_disp.status_code == 200
    assert res_disp.json()["id"] == series_id

    # 3. Invalid identifier yields 404
    res_404 = client.get("/v1/titles/NONEXISTENT-SERIES-999")
    assert res_404.status_code == 404

def test_w4_episode_watch_event_and_title_filter(client, user1_headers, w4_series):
    """Verifies creating an episode watch event and filtering watch events by title_id."""
    series_id = w4_series["title_id"]
    target_ep = w4_series["episodes"][0]

    # 1. Log an episode watch event
    watch_payload = {
        "title_id": series_id,
        "season_id": target_ep["season_id"],
        "episode_id": target_ep["id"],
        "watched_at": "2026-08-30T10:00:00Z",
        "progress_percentage": 100.0,
        "device_type": "Web Browser",
        "notes": "Testing W4 episodic tracking"
    }
    res_log = client.post("/v1/me/watch-events", json=watch_payload, headers=user1_headers)
    assert res_log.status_code == 201
    created_event = res_log.json()
    assert created_event["title_id"] == series_id
    assert created_event["season_id"] == target_ep["season_id"]
    assert created_event["episode_id"] == target_ep["id"]

    # 2. Query watch events filtered by title_id
    res_list = client.get(f"/v1/me/watch-events?title_id={series_id}", headers=user1_headers)
    assert res_list.status_code == 200
    events_data = res_list.json()["data"]
    assert len(events_data) >= 1
    assert any(e["episode_id"] == target_ep["id"] for e in events_data)

def test_w4_episode_rewatch_creates_multiple_events(client, user1_headers, w4_series):
    """Verifies that logging the same episode twice creates distinct append-only records (ADR-003)."""
    series_id = w4_series["title_id"]
    target_ep = w4_series["episodes"][0]

    # First watch
    res1 = client.post("/v1/me/watch-events", json={
        "title_id": series_id,
        "season_id": target_ep["season_id"],
        "episode_id": target_ep["id"],
        "watched_at": "2026-08-28T12:00:00Z",
    }, headers=user1_headers)
    assert res1.status_code == 201
    event1_id = res1.json()["id"]

    # Second watch (rewatch)
    res2 = client.post("/v1/me/watch-events", json={
        "title_id": series_id,
        "season_id": target_ep["season_id"],
        "episode_id": target_ep["id"],
        "watched_at": "2026-08-30T12:00:00Z",
    }, headers=user1_headers)
    assert res2.status_code == 201
    event2_id = res2.json()["id"]

    # Distinct records with distinct IDs
    assert event1_id != event2_id

    # Verify both records returned in watch events list
    res_list = client.get(f"/v1/me/watch-events?title_id={series_id}", headers=user1_headers)
    events = res_list.json()["data"]
    matching_events = [e for e in events if e["episode_id"] == target_ep["id"]]
    assert len(matching_events) >= 2

def test_w4_series_status_transitions(client, user1_headers, w4_series):
    """Verifies partial watching transitions to WATCHING, while all episodes watched transitions to COMPLETED."""
    series_id = w4_series["title_id"]
    episodes = w4_series["episodes"]

    # 1. Watch ONLY the first episode (1 out of 4)
    first_ep = episodes[0]
    res_first = client.post("/v1/me/watch-events", json={
        "title_id": series_id,
        "season_id": first_ep["season_id"],
        "episode_id": first_ep["id"],
        "watched_at": "2026-08-30T09:00:00Z",
    }, headers=user1_headers)
    assert res_first.status_code == 201

    # Check title state: MUST be WATCHING (NOT prematurely COMPLETED)
    res_state1 = client.get(f"/v1/me/title-states/{series_id}", headers=user1_headers)
    assert res_state1.status_code == 200
    state1 = res_state1.json()
    assert state1["manual_status_override"] == "WATCHING"

    # 2. Watch all remaining episodes (episodes 2, 3, 4)
    for ep in episodes[1:]:
        client.post("/v1/me/watch-events", json={
            "title_id": series_id,
            "season_id": ep["season_id"],
            "episode_id": ep["id"],
            "watched_at": "2026-08-30T10:00:00Z",
        }, headers=user1_headers)

    # Check title state: MUST now be COMPLETED
    res_state2 = client.get(f"/v1/me/title-states/{series_id}", headers=user1_headers)
    assert res_state2.status_code == 200
    state2 = res_state2.json()
    assert state2["manual_status_override"] == "COMPLETED"

def test_w4_user_isolation(client, user1_headers, user2_headers, w4_series):
    """Verifies that User A's episode watch events and progress never leak to User B."""
    series_id = w4_series["title_id"]
    target_ep = w4_series["episodes"][0]

    # User A watches the episode
    res_a = client.post("/v1/me/watch-events", json={
        "title_id": series_id,
        "season_id": target_ep["season_id"],
        "episode_id": target_ep["id"],
        "watched_at": "2026-08-30T11:00:00Z",
    }, headers=user1_headers)
    assert res_a.status_code == 201

    # User A sees the watch event
    res_events_a = client.get(f"/v1/me/watch-events?title_id={series_id}", headers=user1_headers)
    assert len(res_events_a.json()["data"]) >= 1

    # User B queries watch events for the same series -> MUST be empty
    res_events_b = client.get(f"/v1/me/watch-events?title_id={series_id}", headers=user2_headers)
    assert len(res_events_b.json()["data"]) == 0

    # User B checks title state -> derived_status is UNWATCHED
    res_state_b = client.get(f"/v1/me/title-states/{series_id}", headers=user2_headers)
    assert res_state_b.json()["derived_status"] == "UNWATCHED"

def test_w4_history_episodic_enrichment(client, user1_headers, w4_series):
    """Verifies that GET /v1/personal/history enriches episodic watch events with season & episode metadata."""
    series_id = w4_series["title_id"]
    target_ep = w4_series["episodes"][0]

    # Log episode watch
    client.post("/v1/me/watch-events", json={
        "title_id": series_id,
        "season_id": target_ep["season_id"],
        "episode_id": target_ep["id"],
        "watched_at": "2026-08-30T11:30:00Z",
    }, headers=user1_headers)

    # Fetch history
    res_hist = client.get("/v1/personal/history?limit=10", headers=user1_headers)
    assert res_hist.status_code == 200
    hist_items = res_hist.json()["items"]
    assert len(hist_items) > 0

    # Find the episodic event
    ep_item = next((item for item in hist_items if item["title_id"] == series_id and item.get("episode_id") == target_ep["id"]), None)
    assert ep_item is not None
    assert ep_item["season_number"] == target_ep["season_number"]
    assert ep_item["episode_number"] == target_ep["episode_number"]
    assert ep_item["episode_name"] == target_ep["name"]

def test_w4_user_streak_on_episode_watch(client, user1_headers, w4_series):
    """Verifies that logging an episode watch maintains the user's daily watch streak."""
    series_id = w4_series["title_id"]
    target_ep = w4_series["episodes"][0]

    # Initial streak
    res_streak0 = client.get("/v1/personal/streak", headers=user1_headers)
    assert res_streak0.status_code == 200

    # Log watch event
    client.post("/v1/me/watch-events", json={
        "title_id": series_id,
        "season_id": target_ep["season_id"],
        "episode_id": target_ep["id"],
        "watched_at": "2026-08-30T12:00:00Z",
    }, headers=user1_headers)

    # Updated streak
    res_streak1 = client.get("/v1/personal/streak", headers=user1_headers)
    assert res_streak1.status_code == 200
    streak_data = res_streak1.json()
    assert streak_data["current_streak"] >= 1
    assert streak_data["longest_streak"] >= 1

def test_w4_watch_event_tombstone(client, user1_headers, w4_series):
    """Verifies that soft-deleting (tombstoning) a watch event removes it from active history."""
    series_id = w4_series["title_id"]
    target_ep = w4_series["episodes"][0]

    # Log event
    res_log = client.post("/v1/me/watch-events", json={
        "title_id": series_id,
        "season_id": target_ep["season_id"],
        "episode_id": target_ep["id"],
        "watched_at": "2026-08-30T13:00:00Z",
    }, headers=user1_headers)
    event_id = res_log.json()["id"]

    # Delete (tombstone) event
    res_del = client.delete(f"/v1/personal/history/{event_id}", headers=user1_headers)
    assert res_del.status_code == 200

    # Verify event no longer returned in history
    res_hist = client.get("/v1/personal/history?limit=20", headers=user1_headers)
    event_ids = [item["id"] for item in res_hist.json()["items"]]
    assert event_id not in event_ids

