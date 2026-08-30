# CineVault OS — Phase W5 Data Completeness & Ingestion Reliability Test Suite
# Tests all W5 Data & Pipeline Reliability requirements against REAL PostgreSQL:
# 1. Source registry governance & licensing gate enforcement
# 2. Provider normalization without fabricated fallbacks
# 3. 4-level identity resolution & transliteration matching
# 4. Level-1 exact match resilience on preload failure (PostgreSQL fallback)
# 5. Truthful item status and run status reporting (COMPLETED / PARTIAL / FAILED)
# 6. Duplicate prevention on movie re-ingestion
# 7. Series and episode hierarchy ingestion & deduplication on re-ingestion
# 8. Field provenance recording & deterministic conflict resolution
# 9. Personal data preservation across title re-ingestion & refresh
# 10. Catalog health and operational internal endpoints

import asyncio
import base64
import json
import time
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select, func

from services.api.main import app
from services.api.database import get_db, AsyncSessionLocal
from services.api.ingestion.licensing import licensing_gate, SourceAccessStatus
from services.api.ingestion.adapters import (
    KobisProviderAdapter, TvdbProviderAdapter, TmdbProviderAdapter,
    AniListProviderAdapter, MyAnimeListProviderAdapter, WikidataProviderAdapter
)
from services.api.ingestion.pipeline import pipeline_engine
from services.api.quality.identity_resolution import identity_resolver, MatchState
from services.api.models.canonical import (
    TitleModel, TitleExternalIdModel, SeasonModel, EpisodeModel
)
from services.api.models.personal import (
    UserTitleStateModel, LibraryEntryModel, WatchEventModel, RatingModel, NoteModel, ReviewModel
)
from services.api.models.ingestion import (
    FieldProvenanceModel
)
from services.api.models.quality import MetadataConflictModel
from services.api.schemas.internal import IngestionTriggerRequest, IngestionItemPayload

def generate_jwt(roles: list, sub: str = "w5-test-user") -> str:
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
def curator_headers():
    token = generate_jwt(["AuthenticatedUser", "Curator"], sub=f"w5-curator-{uuid.uuid4().hex[:8]}")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def user_headers():
    user_id = str(uuid.uuid4())
    token = generate_jwt(["AuthenticatedUser"], sub=user_id)
    return {"Authorization": f"Bearer {token}", "user_id": user_id}

# --------------------------------------------------------------------------
# 1. Source Registry Governance & Licensing Gate Enforcement
# --------------------------------------------------------------------------
def test_w5_source_registry_and_licensing_gate():
    registry = licensing_gate.get_source_registry()
    
    # Active permitted sources
    assert "KOBIS" in registry
    assert registry["KOBIS"]["access_status"] == SourceAccessStatus.PERMITTED
    assert registry["KOBIS"]["rate_limit_per_min"] == 300
    assert "TMDB" in registry
    assert registry["TMDB"]["access_status"] == SourceAccessStatus.PERMITTED_SERVER_ONLY
    assert "TVDB" in registry
    assert "ANILIST" in registry
    assert "WIKIDATA" in registry

    # Prohibited sources blocked at gate
    with pytest.raises(PermissionError):
        licensing_gate.verify_source_access("JUSTWATCH")

    with pytest.raises(PermissionError):
        licensing_gate.verify_source_access("IMDB_DATASETS")

    with pytest.raises(PermissionError):
        licensing_gate.verify_source_access("THEPIRATEBAY")

    with pytest.raises(PermissionError):
        licensing_gate.verify_source_access("UNKNOWN_SOURCE")

    with pytest.raises(PermissionError):
        licensing_gate.verify_source_access("KOBIS", is_scraping_attempt=True)

# --------------------------------------------------------------------------
# 2. Provider Normalization Without Fabricated Defaults
# --------------------------------------------------------------------------
def test_w5_provider_normalization_no_fabrication():
    # Kobis normalization
    kobis = KobisProviderAdapter()
    kobis_raw = {
        "movieCd": "20249991",
        "movieNm": "테스트 영화",
        "movieNmEn": "Test Movie",
        "prdtYear": "2024",
        "showTm": "110",
        "nationAlt": "한국",
        "genres": [{"genreNm": "드라마"}, {"genreNm": "스릴러"}],
        "directors": [{"peopleNm": "김감독"}],
        "actors": [{"peopleNm": "이배우"}]
    }
    kobis_norm = kobis.normalize_payload(kobis_raw)
    assert kobis_norm["provider_name"] == "KOBIS"
    assert kobis_norm["external_id"] == "20249991"
    assert kobis_norm["canonical_title_proposal"] == "Test Movie"
    assert kobis_norm["original_title"] == "테스트 영화"
    assert kobis_norm["production_year"] == 2024
    assert kobis_norm["runtime_minutes"] == 110
    assert kobis_norm["origin_country"] == "KR"
    assert kobis_norm["genres"] == ["드라마", "스릴러"]
    assert kobis_norm["directors"] == ["김감독"]
    assert kobis_norm["cast"] == ["이배우"]

    # Kobis with missing year should be None, not 2019
    kobis_missing_year = kobis.normalize_payload({"movieCd": "20249992", "movieNm": "No Year"})
    assert kobis_missing_year["production_year"] is None
    assert kobis_missing_year["runtime_minutes"] is None

    # TVDB normalization
    tvdb = TvdbProviderAdapter()
    tvdb_raw = {
        "id": 987654,
        "name": "Global Drama",
        "originalName": "글로벌 드라마",
        "year": "2023",
        "originalCountry": "kor",
        "overview": "A series synopsis.",
        "genres": [{"name": "Drama"}, {"name": "Mystery"}]
    }
    tvdb_norm = tvdb.normalize_payload(tvdb_raw)
    assert tvdb_norm["provider_name"] == "TVDB"
    assert tvdb_norm["external_id"] == "987654"
    assert tvdb_norm["production_year"] == 2023
    assert tvdb_norm["origin_country"] == "KR"
    assert tvdb_norm["genres"] == ["Drama", "Mystery"]

    # TMDB normalization
    tmdb = TmdbProviderAdapter()
    tmdb_raw = {
        "id": 123456,
        "title": "French Cinema",
        "original_title": "Cinéma Français",
        "release_date": "2022-05-18",
        "runtime": 95,
        "origin_country": ["FR"],
        "genres": [{"id": 18, "name": "Drama"}]
    }
    tmdb_norm = tmdb.normalize_payload(tmdb_raw)
    assert tmdb_norm["provider_name"] == "TMDB"
    assert tmdb_norm["content_type"] == "MOVIE"
    assert tmdb_norm["production_year"] == 2022
    assert tmdb_norm["runtime_minutes"] == 95
    assert tmdb_norm["origin_country"] == "FR"

    # TMDB with no origin_country should be None, NOT "US"
    tmdb_no_country = tmdb.normalize_payload({"id": 123457, "title": "No Country Film"})
    assert tmdb_no_country["origin_country"] is None

# --------------------------------------------------------------------------
# 3. 4-Level Identity Resolution & Transliteration Matching
# --------------------------------------------------------------------------
def test_w5_identity_resolution_engine():
    catalog_snapshot = [
        {
            "id": "018f6f60-7a00-7000-8000-000000000001",
            "display_id": "MOV-000001",
            "canonical_title": "Parasite",
            "original_title": "기생충",
            "production_year": 2019,
            "production_country": "KR",
            "runtime_minutes": 132,
            "external_ids": {"KOBIS": "20192194", "TMDB": "496243"},
            "_norm_canonical_title": "parasite",
            "_norm_original_title": "기생충"
        },
        {
            "id": "018f6f60-7a00-7000-8000-000000000002",
            "display_id": "MOV-000002",
            "canonical_title": "Oldboy",
            "original_title": "올드보이",
            "production_year": 2003,
            "production_country": "KR",
            "runtime_minutes": 120,
            "external_ids": {"KOBIS": "20030371", "TMDB": "670"},
            "_norm_canonical_title": "oldboy",
            "_norm_original_title": "올드보이"
        }
    ]

    # Level 1: Exact External ID match
    p1 = {"provider_name": "KOBIS", "external_id": "20192194", "canonical_title_proposal": "Parasite", "production_year": 2019}
    state, matched_id, score, rule = identity_resolver.resolve_identity(p1, catalog_snapshot)
    assert state == MatchState.MATCH_EXACT
    assert matched_id == "018f6f60-7a00-7000-8000-000000000001"
    assert score == 1.0

    # Level 2: Canonical ID match
    p2 = {"title_id": "018f6f60-7a00-7000-8000-000000000002", "canonical_title_proposal": "Oldboy"}
    state, matched_id, score, rule = identity_resolver.resolve_identity(p2, catalog_snapshot)
    assert state == MatchState.MATCH_EXACT
    assert matched_id == "018f6f60-7a00-7000-8000-000000000002"

    # Level 3: Deterministic Title + Year match
    p3 = {"provider_name": "NEW_PROV", "external_id": "9999", "canonical_title_proposal": "Parasite", "production_year": 2019}
    state, matched_id, score, rule = identity_resolver.resolve_identity(p3, catalog_snapshot)
    assert state == MatchState.MATCH_EXACT
    assert matched_id == "018f6f60-7a00-7000-8000-000000000001"

    # Level 3: Multilingual Transliteration (Korean Hangul vs Romanization with same year)
    p4 = {"provider_name": "NEW_PROV", "external_id": "8888", "original_title": "기생충", "production_year": 2019}
    state, matched_id, score, rule = identity_resolver.resolve_identity(p4, catalog_snapshot)
    assert state == MatchState.MATCH_EXACT
    assert matched_id == "018f6f60-7a00-7000-8000-000000000001"

    # Unmatched Title -> NO_MATCH
    p5 = {"provider_name": "KOBIS", "external_id": "111111", "canonical_title_proposal": "Brand New Work", "production_year": 2025}
    state, matched_id, score, rule = identity_resolver.resolve_identity(p5, catalog_snapshot)
    assert state == MatchState.NO_MATCH

# --------------------------------------------------------------------------
# 4. Level-1 Preload Failure Resilience (PostgreSQL fallback)
# --------------------------------------------------------------------------
def test_w5_pipeline_level1_preload_failure_resilience():
    async def _test():
        async with AsyncSessionLocal() as session:
            # 1. Create title with unique external ID
            test_ext_id = f"w5-ext-{uuid.uuid4().hex[:8]}"
            title_id = uuid.uuid4()
            t = TitleModel(
                title_id=title_id,
                display_id=f"MOV-W5{uuid.uuid4().hex[:4]}",
                content_type_id="movie",
                canonical_title="Preload Test Film",
                original_title="Preload Test Film",
                production_year=2024,
                status_flag="ACTIVE"
            )
            ext = TitleExternalIdModel(
                mapping_id=uuid.uuid4(),
                title_id=title_id,
                provider_name="KOBIS",
                external_id=test_ext_id
            )
            session.add(t)
            session.add(ext)
            await session.flush()

            # 2. Call _match_canonical_title with external_id_map = None (simulating preload failure)
            run_context = {"external_id_map": None, "catalog_snapshot": None}
            match_status, matched_title_id, score, rule = await pipeline_engine._match_canonical_title(
                db=session,
                provider_name="KOBIS",
                external_id=test_ext_id,
                normalized={"canonical_title_proposal": "Preload Test Film", "production_year": 2024},
                run_context=run_context
            )

            assert match_status == "AUTO_MATCH"
            assert matched_title_id == str(title_id)
            assert score == 1.0

            await session.rollback()

    asyncio.run(_test())

# --------------------------------------------------------------------------
# 5. Truthful Item and Run Status Reporting
# --------------------------------------------------------------------------
def test_w5_truthful_ingestion_run_reporting():
    async def _test():
        async with AsyncSessionLocal() as session:
            valid_ext_id = f"w5-valid-{uuid.uuid4().hex[:6]}"
            invalid_ext_id = f"w5-invalid-{uuid.uuid4().hex[:6]}"

            req = IngestionTriggerRequest(
                provider_name="KOBIS",
                dry_run=True,
                items=[
                    IngestionItemPayload(
                        external_entity_type="MOVIE",
                        external_entity_id=valid_ext_id,
                        raw_payload={
                            "movieCd": valid_ext_id,
                            "movieNm": "Valid Dry Run Movie",
                            "prdtYear": "2024",
                            "showTm": "100"
                        }
                    ),
                    IngestionItemPayload(
                        external_entity_type="MOVIE",
                        external_entity_id=invalid_ext_id,
                        raw_payload={
                            "movieCd": invalid_ext_id,
                            "movieNm": "", # Empty title proposal -> Schema error
                            "prdtYear": "2024"
                        }
                    )
                ]
            )

            result = await pipeline_engine.execute_run(db=session, trigger_req=req)
            assert result["records_seen"] == 2
            assert result["records_valid"] == 1
            assert result["records_rejected"] == 1
            assert result["error_count"] >= 1
            assert result["status"] == "PARTIAL" # 1 valid, 1 rejected -> truthful PARTIAL

            valid_res = next(r for r in result["candidate_results"] if r["external_id"] == valid_ext_id)
            assert valid_res["item_status"] == "DRY_RUN_VALIDATED"

            await session.rollback()

    asyncio.run(_test())

# --------------------------------------------------------------------------
# 6. Movie Re-Ingestion & Duplicate Prevention
# --------------------------------------------------------------------------
def test_w5_duplicate_prevention_on_reingestion():
    async def _test():
        async with AsyncSessionLocal() as session:
            test_ext_id = f"w5-dup-{uuid.uuid4().hex[:8]}"

            item = IngestionItemPayload(
                external_entity_type="MOVIE",
                external_entity_id=test_ext_id,
                raw_payload={
                    "movieCd": test_ext_id,
                    "movieNm": "Duplicate Test Movie",
                    "movieNmEn": "Duplicate Test Movie",
                    "prdtYear": "2024",
                    "showTm": "115",
                    "nationAlt": "한국"
                }
            )

            # 1. First Ingestion: Creates title
            req1 = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=[item])
            res1 = await pipeline_engine.execute_run(db=session, trigger_req=req1)
            assert res1["records_created"] == 1

            # Query database to get title_id
            ext_res = await session.execute(
                select(TitleExternalIdModel).where(
                    TitleExternalIdModel.provider_name == "KOBIS",
                    TitleExternalIdModel.external_id == test_ext_id
                )
            )
            ext_row = ext_res.scalar_one()
            created_title_id = ext_row.title_id

            # 2. Second Ingestion (Refresh): MUST NOT create duplicate title
            req2 = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=[item])
            res2 = await pipeline_engine.execute_run(db=session, trigger_req=req2)
            assert res2["records_created"] == 0
            assert res2["existing_matches"] == 1

            # Check total count of titles with this external ID
            count_res = await session.execute(
                select(func.count()).select_from(TitleExternalIdModel).where(
                    TitleExternalIdModel.provider_name == "KOBIS",
                    TitleExternalIdModel.external_id == test_ext_id
                )
            )
            assert count_res.scalar_one() == 1

            await session.rollback()

    asyncio.run(_test())

# --------------------------------------------------------------------------
# 7. Series & Episode Hierarchy Ingestion & Deduplication
# --------------------------------------------------------------------------
def test_w5_series_and_episodes_hierarchy_ingestion():
    async def _test():
        async with AsyncSessionLocal() as session:
            series_ext_id = f"w5-tv-{uuid.uuid4().hex[:8]}"

            # 1. Ingest Series with Season 1 (Episodes 1 & 2)
            item1 = IngestionItemPayload(
                external_entity_type="TV_SERIES",
                external_entity_id=series_ext_id,
                raw_payload={
                    "id": series_ext_id,
                    "name": "Mystery Series",
                    "originalName": "미스터리 시리즈",
                    "year": 2024,
                    "originalCountry": "kor",
                    "overview": "A suspenseful episodic thriller.",
                    "genres": [{"name": "Mystery"}, {"name": "Thriller"}],
                    "seasons": [
                        {
                            "season_number": 1,
                            "season_name": "Season 1",
                            "overview": "Season 1 Overview",
                            "episodes": [
                                {"episode_number": 1, "episode_name": "Pilot", "air_date": "2024-01-01", "runtime_minutes": 50},
                                {"episode_number": 2, "episode_name": "The Clue", "air_date": "2024-01-08", "runtime_minutes": 52}
                            ]
                        }
                    ]
                }
            )

            req1 = IngestionTriggerRequest(provider_name="TVDB", dry_run=False, items=[item1])
            res1 = await pipeline_engine.execute_run(db=session, trigger_req=req1)
            assert res1["records_created"] == 1

            # Query created series
            ext_res = await session.execute(
                select(TitleExternalIdModel).where(
                    TitleExternalIdModel.provider_name == "TVDB",
                    TitleExternalIdModel.external_id == series_ext_id
                )
            )
            title_id = ext_res.scalar_one().title_id

            # Verify seasons & episodes
            s_res = await session.execute(select(SeasonModel).where(SeasonModel.title_id == title_id))
            seasons = s_res.scalars().all()
            assert len(seasons) == 1
            assert seasons[0].season_number == 1

            ep_res = await session.execute(select(EpisodeModel).where(EpisodeModel.season_id == seasons[0].season_id))
            episodes = ep_res.scalars().all()
            assert len(episodes) == 2

            # 2. Re-ingest with updated/added Episode 3
            item2 = IngestionItemPayload(
                external_entity_type="TV_SERIES",
                external_entity_id=series_ext_id,
                raw_payload={
                    "id": series_ext_id,
                    "name": "Mystery Series",
                    "originalName": "미스터리 시리즈",
                    "year": 2024,
                    "originalCountry": "kor",
                    "seasons": [
                        {
                            "season_number": 1,
                            "season_name": "Season 1",
                            "episodes": [
                                {"episode_number": 1, "episode_name": "Pilot", "air_date": "2024-01-01", "runtime_minutes": 50},
                                {"episode_number": 2, "episode_name": "The Clue", "air_date": "2024-01-08", "runtime_minutes": 52},
                                {"episode_number": 3, "episode_name": "The Reveal", "air_date": "2024-01-15", "runtime_minutes": 55}
                            ]
                        }
                    ]
                }
            )

            req2 = IngestionTriggerRequest(provider_name="TVDB", dry_run=False, items=[item2])
            res2 = await pipeline_engine.execute_run(db=session, trigger_req=req2)
            assert res2["records_created"] == 0
            assert res2["records_updated"] == 1

            # Verify Season count remains 1, and Episodes count is now 3
            s_res2 = await session.execute(select(SeasonModel).where(SeasonModel.title_id == title_id))
            assert len(s_res2.scalars().all()) == 1

            ep_res2 = await session.execute(select(EpisodeModel).where(EpisodeModel.season_id == seasons[0].season_id))
            assert len(ep_res2.scalars().all()) == 3

            await session.rollback()

    asyncio.run(_test())

# --------------------------------------------------------------------------
# 8. Field Provenance & Conflict Detection
# --------------------------------------------------------------------------
def test_w5_provenance_and_conflict_handling():
    async def _test():
        async with AsyncSessionLocal() as session:
            test_ext_id = f"w5-conf-{uuid.uuid4().hex[:8]}"

            # Ingest original title
            item1 = IngestionItemPayload(
                external_entity_type="MOVIE",
                external_entity_id=test_ext_id,
                raw_payload={
                    "movieCd": test_ext_id,
                    "movieNm": "Conflict Film",
                    "prdtYear": "2023",
                    "showTm": "120"
                }
            )
            req1 = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=[item1])
            await pipeline_engine.execute_run(db=session, trigger_req=req1)

            # Ingest conflicting metadata for same title
            item2 = IngestionItemPayload(
                external_entity_type="MOVIE",
                external_entity_id=test_ext_id,
                raw_payload={
                    "movieCd": test_ext_id,
                    "movieNm": "Conflict Film Revised",
                    "prdtYear": "2023",
                    "showTm": "145" # Conflict: 145 vs 120 (>1 min diff)
                }
            )
            req2 = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=[item2])
            res2 = await pipeline_engine.execute_run(db=session, trigger_req=req2)
            assert res2["records_conflicted"] >= 1

            # Verify conflict model recorded
            conf_res = await session.execute(
                select(MetadataConflictModel).where(MetadataConflictModel.source_provider == "KOBIS")
            )
            conflicts = conf_res.scalars().all()
            assert len(conflicts) >= 1
            assert any(c.field_name == "runtime_minutes" for c in conflicts)

            # Verify field provenance recorded
            prov_res = await session.execute(
                select(FieldProvenanceModel).where(FieldProvenanceModel.external_id == test_ext_id)
            )
            provs = prov_res.scalars().all()
            assert len(provs) >= 1

            await session.rollback()

    asyncio.run(_test())

# --------------------------------------------------------------------------
# 9. Personal Data Preservation During Re-Ingestion & Refresh
# --------------------------------------------------------------------------
def test_w5_personal_data_preservation():
    async def _test():
        async with AsyncSessionLocal() as session:
            user_uuid = uuid.uuid4()
            test_ext_id = f"w5-user-pres-{uuid.uuid4().hex[:8]}"

            # 1. Ingest Title
            item = IngestionItemPayload(
                external_entity_type="MOVIE",
                external_entity_id=test_ext_id,
                raw_payload={
                    "movieCd": test_ext_id,
                    "movieNm": "User Protected Film",
                    "prdtYear": "2024",
                    "showTm": "110"
                }
            )
            req = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=[item])
            await pipeline_engine.execute_run(db=session, trigger_req=req)

            ext_res = await session.execute(
                select(TitleExternalIdModel).where(
                    TitleExternalIdModel.provider_name == "KOBIS",
                    TitleExternalIdModel.external_id == test_ext_id
                )
            )
            title_id = ext_res.scalar_one().title_id

            # 2. Attach personal records: Watchlist, Library, Watch Event, Rating, Note, Review
            title_state = UserTitleStateModel(
                user_id=user_uuid,
                title_id=title_id,
                manual_status_override="PLAN_TO_WATCH",
                is_favorite=True
            )
            session.add(title_state)

            lib_entry = LibraryEntryModel(
                user_id=user_uuid,
                title_id=title_id
            )
            session.add(lib_entry)

            watch_ev = WatchEventModel(
                watch_event_id=uuid.uuid4(),
                user_id=user_uuid,
                title_id=title_id,
                watched_at=datetime.now(timezone.utc)
            )
            session.add(watch_ev)

            user_rating = RatingModel(
                rating_id=uuid.uuid4(),
                user_id=user_uuid,
                title_id=title_id,
                rating_value=10
            )
            session.add(user_rating)

            user_note = NoteModel(
                note_id=uuid.uuid4(),
                user_id=user_uuid,
                title_id=title_id,
                note_text="Important personal note about this movie."
            )
            session.add(user_note)

            user_review = ReviewModel(
                review_id=uuid.uuid4(),
                user_id=user_uuid,
                title_id=title_id,
                review_title="Masterpiece",
                review_text="Fantastic cinematic direction.",
                contains_spoilers=False
            )
            session.add(user_review)
            await session.flush()

            # 3. Refresh / Re-Ingest Title multiple times
            refresh_req = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=[item])
            await pipeline_engine.execute_run(db=session, trigger_req=refresh_req)

            # 4. Verify all personal records remain 100% intact
            saved_state = (await session.execute(select(UserTitleStateModel).where(
                UserTitleStateModel.user_id == user_uuid, UserTitleStateModel.title_id == title_id
            ))).scalar_one_or_none()
            assert saved_state is not None
            assert saved_state.manual_status_override == "PLAN_TO_WATCH"
            assert saved_state.is_favorite is True

            saved_lib = (await session.execute(select(LibraryEntryModel).where(
                LibraryEntryModel.user_id == user_uuid, LibraryEntryModel.title_id == title_id
            ))).scalar_one_or_none()
            assert saved_lib is not None

            saved_ev = (await session.execute(select(WatchEventModel).where(
                WatchEventModel.user_id == user_uuid, WatchEventModel.title_id == title_id
            ))).scalar_one_or_none()
            assert saved_ev is not None

            saved_rat = (await session.execute(select(RatingModel).where(
                RatingModel.user_id == user_uuid, RatingModel.title_id == title_id
            ))).scalar_one_or_none()
            assert saved_rat is not None
            assert saved_rat.rating_value == 10

            saved_note = (await session.execute(select(NoteModel).where(
                NoteModel.user_id == user_uuid, NoteModel.title_id == title_id
            ))).scalar_one_or_none()
            assert saved_note is not None
            assert saved_note.note_text == "Important personal note about this movie."

            saved_rev = (await session.execute(select(ReviewModel).where(
                ReviewModel.user_id == user_uuid, ReviewModel.title_id == title_id
            ))).scalar_one_or_none()
            assert saved_rev is not None
            assert saved_rev.review_title == "Masterpiece"

            await session.rollback()

    asyncio.run(_test())

# --------------------------------------------------------------------------
# 10. Operational Control Room Endpoints
# --------------------------------------------------------------------------
def test_w5_control_room_operational_endpoints(client, curator_headers):
    # 1. Sources endpoint
    res_sources = client.get("/internal/v1/ingestion/sources", headers=curator_headers)
    assert res_sources.status_code == 200
    sources = res_sources.json()
    assert "KOBIS" in sources or "kobis" in sources

    # 2. Runs endpoint
    res_runs = client.get("/internal/v1/ingestion/runs", headers=curator_headers)
    assert res_runs.status_code == 200
    runs = res_runs.json()
    assert isinstance(runs, list)

    # 3. Candidates endpoint
    res_cand = client.get("/internal/v1/ingestion/candidates", headers=curator_headers)
    assert res_cand.status_code == 200
    assert isinstance(res_cand.json(), list)

    # 4. Conflicts endpoint
    res_conf = client.get("/internal/v1/reconciliation/conflicts", headers=curator_headers)
    assert res_conf.status_code == 200
    assert isinstance(res_conf.json(), list)
