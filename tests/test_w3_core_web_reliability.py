# CineVault OS — Phase W3 Core Web Reliability Test Suite
# Tests all Core Web Endpoints against REAL PostgreSQL:
# 1. Canonical Title Lookups by UUID and display_id (e.g. MOV-000001, TV-000001)
# 2. Personal Title State (Watchlist, Favorites, Preferred Edition)
# 3. Personal Ratings CRUD (Create, List, Filter by title_id, Delete)
# 4. Personal Notes CRUD (Create, List, Filter by title_id, Delete)
# 5. Personal Reviews CRUD (Create, List, Filter by title_id, Delete)
# 6. Watch Events logging with Edition/Season/Episode & Streak Tracking
# 7. User Isolation (User A personal data is completely isolated from User B)
# 8. Library Add & Remove Operations

import time
import base64
import json
import uuid
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.database import get_db

def generate_mock_jwt(roles: list, sub: str = "w3-test-user-1") -> str:
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
    token = generate_mock_jwt(["AuthenticatedUser"], sub=f"w3-user-{uuid.uuid4().hex[:8]}")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def user2_headers():
    token = generate_mock_jwt(["AuthenticatedUser"], sub=f"w3-user-{uuid.uuid4().hex[:8]}")
    return {"Authorization": f"Bearer {token}"}

def test_w3_title_lookup_by_uuid_and_display_id(client):
    # Fetch a title from catalog
    res = client.get("/v1/catalog?limit=5")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) > 0

    first = items[0]
    title_uuid = first["id"]
    display_id = first["display_id"]

    # 1. Lookup by UUID
    res_uuid = client.get(f"/v1/titles/{title_uuid}")
    assert res_uuid.status_code == 200
    data_uuid = res_uuid.json()
    assert data_uuid["id"] == title_uuid
    assert data_uuid["display_id"] == display_id

    # 2. Lookup by display_id (e.g. MOV-000001)
    if display_id:
        res_display = client.get(f"/v1/titles/{display_id}")
        assert res_display.status_code == 200
        data_display = res_display.json()
        assert data_display["id"] == title_uuid
        assert data_display["display_id"] == display_id

    # 3. Invalid identifier yields 404, not 500
    res_404 = client.get("/v1/titles/NONEXISTENT-999999")
    assert res_404.status_code == 404

def test_w3_personal_title_state_and_watchlist(client, user1_headers):
    # Pick a title
    res_cat = client.get("/v1/catalog?limit=1")
    title_id = res_cat.json()["items"][0]["id"]

    # Initial state
    res_get = client.get(f"/v1/me/title-states/{title_id}", headers=user1_headers)
    assert res_get.status_code == 200
    initial_state = res_get.json()
    assert initial_state["title_id"] == title_id

    # Update manual_status_override to PLAN_TO_WATCH (Watchlist) & Favorite
    res_patch = client.patch(
        f"/v1/me/title-states/{title_id}",
        json={"manual_status_override": "PLAN_TO_WATCH", "is_favorite": True},
        headers=user1_headers
    )
    assert res_patch.status_code == 200
    patched = res_patch.json()
    assert patched["manual_status_override"] == "PLAN_TO_WATCH"
    assert patched["is_favorite"] is True

    # Verify title appears in watchlist
    res_wl = client.get("/v1/personal/watchlist", headers=user1_headers)
    assert res_wl.status_code == 200
    wl_items = res_wl.json()["items"]
    assert any(item["title_id"] == title_id for item in wl_items)

    # Clear watchlist state
    res_clear = client.patch(
        f"/v1/me/title-states/{title_id}",
        json={"manual_status_override": None, "is_favorite": False},
        headers=user1_headers
    )
    assert res_clear.status_code == 200
    assert res_clear.json()["manual_status_override"] is None
    assert res_clear.json()["is_favorite"] is False

def test_w3_personal_ratings_crud(client, user1_headers, user2_headers):
    res_cat = client.get("/v1/catalog?limit=2")
    title_1 = res_cat.json()["items"][0]["id"]
    title_2 = res_cat.json()["items"][1]["id"]

    # 1. Create/Set rating for user1 on title_1
    res_set1 = client.post(
        "/v1/me/ratings",
        json={"title_id": title_1, "rating_value": 9},
        headers=user1_headers
    )
    assert res_set1.status_code in (200, 201)
    r1 = res_set1.json()
    assert r1["title_id"] == title_1
    assert r1["rating_value"] == 9

    # 2. Create/Set rating for user1 on title_2
    res_set2 = client.post(
        "/v1/me/ratings",
        json={"title_id": title_2, "rating_value": 7},
        headers=user1_headers
    )
    assert res_set2.status_code in (200, 201)

    # 3. List all ratings for user1
    res_list = client.get("/v1/me/ratings", headers=user1_headers)
    assert res_list.status_code == 200
    all_ratings = res_list.json()
    assert len(all_ratings) >= 2

    # 4. List ratings filtered by title_id
    res_filter = client.get(f"/v1/me/ratings?title_id={title_1}", headers=user1_headers)
    assert res_filter.status_code == 200
    filtered = res_filter.json()
    assert len(filtered) == 1
    assert filtered[0]["title_id"] == title_1
    assert filtered[0]["rating_value"] == 9

    # 5. User 2 isolation: user 2 has no ratings
    res_user2 = client.get(f"/v1/me/ratings?title_id={title_1}", headers=user2_headers)
    assert res_user2.status_code == 200
    assert len(res_user2.json()) == 0

    # 6. Delete rating for title_1
    res_del = client.delete(f"/v1/me/ratings/{title_1}", headers=user1_headers)
    assert res_del.status_code == 200

    # 7. Verify rating deleted
    res_after_del = client.get(f"/v1/me/ratings?title_id={title_1}", headers=user1_headers)
    assert len(res_after_del.json()) == 0

def test_w3_personal_notes_crud(client, user1_headers, user2_headers):
    res_cat = client.get("/v1/catalog?limit=1")
    title_id = res_cat.json()["items"][0]["id"]

    # 1. Create a private note
    res_create = client.post(
        "/v1/me/notes",
        json={"title_id": title_id, "note_text": "Remarkable 70mm cinematography."},
        headers=user1_headers
    )
    assert res_create.status_code in (200, 201)
    note = res_create.json()
    note_id = note["id"]
    assert note["title_id"] == title_id
    assert note["note_text"] == "Remarkable 70mm cinematography."

    # 2. Filter notes by title_id
    res_list = client.get(f"/v1/me/notes?title_id={title_id}", headers=user1_headers)
    assert res_list.status_code == 200
    notes = res_list.json()
    assert any(n["id"] == note_id for n in notes)

    # 3. User isolation: User 2 cannot see User 1's private note
    res_u2 = client.get(f"/v1/me/notes?title_id={title_id}", headers=user2_headers)
    assert res_u2.status_code == 200
    assert not any(n["id"] == note_id for n in res_u2.json())

    # 4. Delete note
    res_del = client.delete(f"/v1/me/notes/{note_id}", headers=user1_headers)
    assert res_del.status_code == 200

    # 5. Verify note deleted
    res_after = client.get(f"/v1/me/notes?title_id={title_id}", headers=user1_headers)
    assert not any(n["id"] == note_id for n in res_after.json())

def test_w3_personal_reviews_crud(client, user1_headers, user2_headers):
    res_cat = client.get("/v1/catalog?limit=1")
    title_id = res_cat.json()["items"][0]["id"]

    # 1. Create a review
    res_create = client.post(
        "/v1/me/reviews",
        json={
            "title_id": title_id,
            "review_title": "A Masterclass in Atmosphere",
            "review_text": "The pacing and score create an indelible mood.",
            "is_public": True
        },
        headers=user1_headers
    )
    assert res_create.status_code in (200, 201)
    rev = res_create.json()
    rev_id = rev["id"]
    assert rev["review_title"] == "A Masterclass in Atmosphere"

    # 2. Filter reviews by title_id
    res_list = client.get(f"/v1/me/reviews?title_id={title_id}", headers=user1_headers)
    assert res_list.status_code == 200
    revs = res_list.json()
    assert any(r["id"] == rev_id for r in revs)

    # 3. Delete review
    res_del = client.delete(f"/v1/me/reviews/{rev_id}", headers=user1_headers)
    assert res_del.status_code == 200

    # 4. Verify review deleted
    res_after = client.get(f"/v1/me/reviews?title_id={title_id}", headers=user1_headers)
    assert not any(r["id"] == rev_id for r in res_after.json())

def test_w3_watch_events_and_streak(client, user1_headers):
    res_cat = client.get("/v1/catalog?limit=1")
    title_id = res_cat.json()["items"][0]["id"]

    # 1. Log a watch event
    res_evt = client.post(
        "/v1/me/watch-events",
        json={
            "title_id": title_id,
            "watched_at": "2026-08-29T20:00:00Z",
            "progress_percentage": 100.0,
            "device_type": "OLED Display"
        },
        headers=user1_headers
    )
    assert res_evt.status_code in (200, 201)
    evt_data = res_evt.json()
    assert evt_data["title_id"] == title_id

    # 2. Check history
    res_hist = client.get("/v1/personal/history", headers=user1_headers)
    assert res_hist.status_code == 200
    items = res_hist.json()["items"]
    assert any(i["title_id"] == title_id for i in items)

    # 3. Verify streak endpoint
    res_streak = client.get("/v1/personal/streak", headers=user1_headers)
    assert res_streak.status_code == 200
    streak_data = res_streak.json()
    assert streak_data["current_streak"] >= 1

def test_w3_library_add_and_remove(client, user1_headers):
    res_cat = client.get("/v1/catalog?limit=1")
    title_id = res_cat.json()["items"][0]["id"]

    # 1. Add to library
    res_add = client.post(
        "/v1/personal/library",
        json={"title_id": title_id},
        headers=user1_headers
    )
    assert res_add.status_code in (200, 201)

    # 2. Verify in library
    res_lib = client.get("/v1/personal/library", headers=user1_headers)
    assert res_lib.status_code == 200
    items = res_lib.json()["items"]
    assert any(i["title_id"] == title_id for i in items)

    # 3. Remove from library
    res_del = client.delete(f"/v1/personal/library/{title_id}", headers=user1_headers)
    assert res_del.status_code == 200

    # 4. Verify removed
    res_lib_after = client.get("/v1/personal/library", headers=user1_headers)
    items_after = res_lib_after.json()["items"]
    assert not any(i["title_id"] == title_id for i in items_after)
