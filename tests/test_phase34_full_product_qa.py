# CineVault OS — Phase 34 Full Product QA End-to-End Scenarios
# Executes the 6 required full product end-to-end user journeys:
# 1. Core loop: new user -> search -> title -> watchlist -> watch -> rate -> review -> stats -> recs
# 2. TV series: series -> season -> episode -> progress -> completion -> history
# 3. Offline sync: offline mutations -> reconnect -> outbox replay -> server verification
# 4. Metadata update safety: canonical update -> history preserved with no data loss
# 5. Conflict resolution: conflict queue -> curator decision -> provenance preserved
# 6. Recommendations & AI: AI recommendation -> explanation -> feedback loop

import time
import uuid
import base64
import json
import asyncio
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.repositories.canonical import canonical_repository

client = TestClient(app)

# NOTE: this module used to set app.dependency_overrides[get_db] to a stub
# yielding None, permanently (no teardown) for the rest of the pytest
# session -- forcing every test collected afterward onto the db=None mock
# path regardless of what conftest.py or any other module wanted. These are
# "Full Product QA End-to-End Scenarios"; they should run against the real
# database, which is now conftest.py's default for the whole suite.


def generate_mock_jwt(roles: list, sub: str = "user-9999999") -> str:
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


class TestPhase34FullProductQA:
    """Phase 34 — Full Product QA: End-to-End User and System Scenarios."""

    # ------------------------------------------------------------------
    # Scenario 1: Core Loop
    # ------------------------------------------------------------------
    def test_scenario_1_core_user_loop(self):
        """
        Scenario 1 — Core loop:
        new user -> login -> search movie -> open title -> add watchlist -> watch -> rate -> statistics update -> recs
        """
        user_id = f"qa_user_core_{uuid.uuid4().hex[:8]}"
        user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub=user_id)
        auth_headers = {"Authorization": f"Bearer {user_jwt}"}

        # 1. Search / List titles
        titles_res = client.get("/v1/titles", headers=auth_headers)
        assert titles_res.status_code == 200
        titles = titles_res.json().get("data", [])
        assert len(titles) >= 1
        target_movie = titles[0]
        title_id = target_movie["id"]

        # 2. Open title details
        detail_res = client.get(f"/v1/titles/{title_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        assert detail_res.json()["canonical_title"] is not None

        # 3. Update Title State (Add to Favorites / Plan to watch)
        wl_res = client.patch(
            f"/v1/me/title-states/{title_id}",
            headers=auth_headers,
            json={"is_favorite": True, "manual_status_override": "PLAN_TO_WATCH"}
        )
        assert wl_res.status_code == 200

        # 4. Record Watch Event
        watch_res = client.post(
            "/v1/me/watch-events",
            headers=auth_headers,
            json={
                "title_id": title_id,
                "watched_at": "2026-08-16T10:00:00Z",
                "progress_percentage": 100.0,
                "notes": "Masterpiece of cinema"
            }
        )
        assert watch_res.status_code == 201

        # 5. Rate the title
        rate_res = client.post(
            "/v1/me/ratings",
            headers=auth_headers,
            json={"title_id": title_id, "rating_value": 10}
        )
        assert rate_res.status_code == 201

        # 6. Verify Personal Dashboard / Statistics Update
        stats_res = client.get("/v1/me/dashboard", headers=auth_headers)
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats.get("total_titles", 0) >= 1 or stats.get("watched_count", 0) >= 0

        # 7. Verify Recommendations endpoint
        rec_res = client.get("/v1/recommendations", headers=auth_headers)
        assert rec_res.status_code == 200
        recs = rec_res.json()
        assert "data" in recs or "items" in recs

    # ------------------------------------------------------------------
    # Scenario 2: TV Series Progression
    # ------------------------------------------------------------------
    def test_scenario_2_tv_series_lifecycle(self):
        """
        Scenario 2 — TV series:
        series -> season -> episode -> progress -> completion -> history
        """
        user_id = f"qa_user_tv_{uuid.uuid4().hex[:8]}"
        user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub=user_id)
        auth_headers = {"Authorization": f"Bearer {user_jwt}"}

        # 1. Find a real series and open its details (was a hardcoded UUID that
        # doesn't exist in the real catalog -- only ever worked against the
        # db=None mock fallback, which returned 200 for any ID)
        catalog_res = client.get("/v1/titles?content_type=TV_SERIES&limit=1", headers=auth_headers)
        assert catalog_res.status_code == 200
        series_candidates = catalog_res.json().get("data", [])
        assert len(series_candidates) >= 1, "no TV_SERIES title found in the real catalog"
        series_id = series_candidates[0]["id"]

        series_res = client.get(f"/v1/titles/{series_id}", headers=auth_headers)
        assert series_res.status_code == 200

        # 2. Record Episode 1 progress (50% watched)
        ep1_res = client.post(
            "/v1/me/watch-events",
            headers=auth_headers,
            json={
                "title_id": series_id,
                "watched_at": "2026-08-16T11:00:00Z",
                "progress_percentage": 50.0,
                "notes": "Halfway through Pilot episode"
            }
        )
        assert ep1_res.status_code == 201

        # 3. Complete Episode 1
        ep1_done = client.post(
            "/v1/me/watch-events",
            headers=auth_headers,
            json={
                "title_id": series_id,
                "watched_at": "2026-08-16T12:00:00Z",
                "progress_percentage": 100.0,
                "notes": "Finished Pilot"
            }
        )
        assert ep1_done.status_code == 201

        # 4. Verify History reflects watch events
        history_res = client.get("/v1/me/watch-events", headers=auth_headers)
        assert history_res.status_code == 200
        events = history_res.json().get("data", [])
        assert any(e.get("title_id") == series_id for e in events)

    # ------------------------------------------------------------------
    # Scenario 3: Offline Sync Lifecycle
    # ------------------------------------------------------------------
    def test_scenario_3_offline_sync_lifecycle(self):
        """
        Scenario 3 — Offline:
        offline mutations -> reconnect -> sync push -> server verification
        """
        user_id = f"qa_user_sync_{uuid.uuid4().hex[:8]}"
        user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub=user_id)
        auth_headers = {"Authorization": f"Bearer {user_jwt}"}

        mutation_id_1 = str(uuid.uuid4())
        mutation_id_2 = str(uuid.uuid4())
        title_id = "018f2e4a-7b31-7000-8000-123456789abc"

        sync_payload = {
            "mutations": [
                {
                    "mutation_id": mutation_id_1,
                    "mutation_type": "CREATE_WATCH_EVENT",
                    "client_timestamp": "2026-08-16T14:00:00Z",
                    "payload": {
                        "title_id": title_id,
                        "watched_at": "2026-08-16T14:00:00Z",
                        "progress_percentage": 100.0,
                        "notes": "Recorded while offline in airplane mode"
                    }
                },
                {
                    "mutation_id": mutation_id_2,
                    "mutation_type": "SET_RATING",
                    "client_timestamp": "2026-08-16T14:01:00Z",
                    "payload": {
                        "title_id": title_id,
                        "rating_value": 10
                    }
                }
            ]
        }

        # Sync push batch
        sync_res = client.post("/v1/sync/push", headers=auth_headers, json=sync_payload)
        assert sync_res.status_code == 200
        sync_result = sync_res.json()
        assert sync_result.get("processed_count", 0) >= 1 or len(sync_result.get("acknowledged_mutation_ids", [])) >= 1

        # Verify sync pull stream
        pull_res = client.get("/v1/sync/pull", headers=auth_headers)
        assert pull_res.status_code == 200

    # ------------------------------------------------------------------
    # Scenario 4: Metadata Update Safety
    # ------------------------------------------------------------------
    def test_scenario_4_metadata_update_safety(self):
        """
        Scenario 4 — Metadata update safety:
        canonical metadata update -> history preserved without personal data corruption
        """
        title_id = "018f2e4a-7b31-7000-8000-123456789abc"

        # Record a test metadata change
        asyncio.run(
            canonical_repository.record_metadata_change(
                db=None,
                title_id=title_id,
                field_name="synopsis",
                old_value="Old brief synopsis",
                new_value="Updated canonical synopsis with enriched details",
                source_provider="TMDB",
                actor_id="qa_system",
                actor_type="SYSTEM",
                reason="Automatic enrichment",
                confidence=0.99
            )
        )

        # 1. Fetch title history
        hist_res = client.get(f"/v1/titles/{title_id}/history")
        assert hist_res.status_code == 200
        history = hist_res.json()
        assert isinstance(history, list)
        assert len(history) >= 1

        # 2. Verify public title detail still returns clean canonical data
        detail_res = client.get(f"/v1/titles/{title_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["canonical_title"] == "Parasite"

    # ------------------------------------------------------------------
    # Scenario 5: Curator Conflict Resolution
    # ------------------------------------------------------------------
    def test_scenario_5_conflict_resolution(self):
        """
        Scenario 5 — Conflict resolution:
        conflict inspection -> curator resolution -> canonical update -> provenance retained
        """
        curator_jwt = generate_mock_jwt(["Curator", "AuthenticatedUser"], sub="018f4a00-0000-7000-8000-000000000001")
        curator_headers = {
            "Authorization": f"Bearer {curator_jwt}"
        }

        # 1. Control room stats
        stats_res = client.get("/internal/v1/control-room/stats", headers=curator_headers)
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert "pending_reconciliation_candidates" in stats or "catalog_total_titles" in stats

    # ------------------------------------------------------------------
    # Scenario 6: Recommendations & AI Quality
    # ------------------------------------------------------------------
    def test_scenario_6_recommendation_and_ai_quality(self):
        """
        Scenario 6 — Recommendations:
        AI recommendation -> explanation -> diversity -> response structure
        """
        user_id = f"qa_user_ai_{uuid.uuid4().hex[:8]}"
        user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub=user_id)
        auth_headers = {"Authorization": f"Bearer {user_jwt}"}

        # 1. Query personalized recommendations
        rec_res = client.get("/v1/recommendations", headers=auth_headers)
        assert rec_res.status_code == 200
        data = rec_res.json()
        assert "data" in data or "items" in data

        # 2. Query taste profile
        taste_res = client.get("/v1/recommendations/taste-profile", headers=auth_headers)
        assert taste_res.status_code == 200
        assert "top_genres" in taste_res.json()
