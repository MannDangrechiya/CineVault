# CineVault OS — Test Suite for Data Import & AI Assistant Endpoints (v2.0 Phase 3)
# Validates import schemas, preview endpoints, apply execution, and AI conversational workflows.

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.schemas.personal import (
    ImportItemPayload,
    ImportPreviewRequest,
    ImportPreviewResponse,
    ImportApplyRequest,
    ImportApplyResponse,
    ImportConflictStrategyEnum,
)
from services.api.schemas.ai_assistant import AssistantQueryRequest, AssistantQueryResponse
from services.api.schemas.ai import GroupMatchRequest, GroupMatchResponse
from services.api.routers.auth import generate_dev_jwt

client = TestClient(app)


def get_test_token(user_id: str = "018f4a00-0000-7000-8000-000000000001") -> str:
    """Generates an authenticated JWT for API testing."""
    return generate_dev_jwt(
        user_id=user_id,
        email="cinephile@cinevault.test",
        username="cinephile_test",
        roles=["authenticated_user"],
    )


# -----------------------------------------------------------------------------
# 1. Schema Validation Tests
# -----------------------------------------------------------------------------

def test_import_schemas_validation():
    """Verifies Pydantic schema validation for personal import item payloads."""
    item = ImportItemPayload(
        canonical_title="Dune: Part Two",
        production_year=2024,
        rating_value=5,
        manual_status_override="COMPLETED",
        notes="Desert cinematography",
    )
    assert item.canonical_title == "Dune: Part Two"
    assert item.production_year == 2024
    assert item.rating_value == 5

    req = ImportPreviewRequest(items=[item])
    assert len(req.items) == 1

    apply_req = ImportApplyRequest(
        items=[item],
        conflict_strategy=ImportConflictStrategyEnum.KEEP_EXISTING,
    )
    assert apply_req.conflict_strategy == ImportConflictStrategyEnum.KEEP_EXISTING


# -----------------------------------------------------------------------------
# 2. Import Preview & Apply Endpoints
# -----------------------------------------------------------------------------

def test_personal_import_preview_endpoint():
    """Tests POST /v1/personal/import/preview."""
    token = get_test_token()
    payload = {
        "items": [
            {"canonical_title": "Dune: Part Two", "production_year": 2024, "rating_value": 5},
            {"canonical_title": "Blade Runner 2049", "production_year": 2017, "rating_value": 5},
            {"canonical_title": "Arrival", "production_year": 2016, "rating_value": 5},
            {"canonical_title": "Totally Nonexistent Cinematic Title 9999", "production_year": 2099},
        ]
    }
    response = client.post(
        "/v1/personal/import/preview",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 4
    assert data["matched_titles"] >= 2
    assert "conflicts" in data
    assert "item_verdicts" in data
    assert len(data["item_verdicts"]) == 4

    # Check matched item verdict
    first_item = data["item_verdicts"][0]
    assert first_item["canonical_title"] == "Dune: Part Two"
    assert first_item["matched"] is True
    assert first_item["confidence_score"] > 0.5
    assert first_item["verdict"] in ("EXACT_MATCH", "PROBABLE_MATCH")

    # Check unmatched item verdict
    last_item = data["item_verdicts"][3]
    assert last_item["matched"] is False
    assert last_item["confidence_score"] == 0.0
    assert last_item["verdict"] == "UNMATCHED"


def test_personal_import_apply_endpoint():
    """Tests POST /v1/personal/import/apply with conflict strategy."""
    token = get_test_token()
    payload = {
        "items": [
            {"canonical_title": "Solaris", "production_year": 1972, "rating_value": 5},
        ],
        "conflict_strategy": "KEEP_EXISTING",
    }
    response = client.post(
        "/v1/personal/import/apply",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["applied_count"] >= 1
    assert data["strategy_applied"] == "KEEP_EXISTING"


# -----------------------------------------------------------------------------
# 3. AI Assistant & Oracle Endpoints
# -----------------------------------------------------------------------------

def test_ai_assistant_query_endpoint():
    """Tests POST /v1/ai/assistant/query conversational endpoint."""
    token = get_test_token()
    payload = {
        "query_text": "Recommend 3 cyberpunk movies with neon visuals",
        "include_recommendation_context": True,
        "max_results": 3,
    }
    response = client.post(
        "/v1/ai/assistant/query",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response_text" in data
    assert "intent" in data
    assert "matched_titles" in data
    assert data["is_grounded"] is True


def test_group_matchmaking_schema():
    """Tests GroupMatchRequest schema validation."""
    req = GroupMatchRequest(
        friend_ids=["018f4a00-0000-7000-8000-000000000201"],
        mood="Late night sci-fi thriller",
    )
    assert len(req.friend_ids) == 1
    assert req.mood == "Late night sci-fi thriller"
