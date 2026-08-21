# CineVault OS — Personal Data Router (CAT-2)
# User personal logs, append-only watch events, title state management & conflict resolution (ADR-003, ADR-004)

import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import config
from ..schemas.common import PaginatedResponse, CursorPagination
from ..schemas.personal import (
    WatchEventCreate, WatchEventResponse,
    UserTitleStateResponse, UserTitleStateUpdate,
    RatingCreate, RatingResponse,
    NoteCreate, NoteResponse,
    ReviewCreate, ReviewResponse,
    PersonalDataConflictResponse, PersonalDataConflictResolveRequest,
    UserDashboardMetricsResponse,
    PersonalDataExportResponse,
    ImportPreviewRequest, ImportPreviewResponse, ImportConflictItem,
    ImportApplyRequest, ImportApplyResponse,
    HistoryItemResponse, HistoryPageResponse,
    CollectionItemResponse, CollectionCreateRequest,
    PersonalAnalyticsResponse, GenreAffinityItem, CreatorAffinityItem, MonthlyTrendItem,
    WatchlistPageResponse
)
from ..auth.dependencies import require_authenticated_user, get_optional_claims
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.personal import personal_repository
from ..repositories.social import social_repository
from ..models.personal import UserListModel, WatchEventModel
from ..models.canonical import TitleModel

logger = logging.getLogger("cinevault.personal")

router = APIRouter(prefix="/v1/me", tags=["Personal Data (CAT-2)"])
personal_router = APIRouter(prefix="/v1/personal", tags=["Personal Frontend APIs (CAT-2)"])

# In-memory store for user-created collections & history in local dev
SEED_USER_COLLECTIONS: List[dict] = [
    {
        "id": "dune-saga",
        "name": "Dune: The Arrakis Chronicle",
        "description": "Denis Villeneuve's complete epic saga tracking Paul Atreides and the Fremen resistance.",
        "item_count": 2,
        "banner_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1200&q=80",
        "curator": "CineVault Curators",
        "tags": ["Sci-Fi", "Frank Herbert", "IMAX 70mm"],
        "is_private": False,
        "is_custom": False,
        "created_at": "2026-08-01T10:00:00Z"
    },
    {
        "id": "cyberpunk-essentials",
        "name": "Cyberpunk & Neo-Noir Canon",
        "description": "Atmospheric, rain-slicked cityscapes, rogue replicants, and synthetic consciousness.",
        "item_count": 4,
        "banner_url": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1200&q=80",
        "curator": "AI Neural Curations",
        "tags": ["Cyberpunk", "Dystopian", "Synthesizer"],
        "is_private": False,
        "is_custom": False,
        "created_at": "2026-08-05T14:30:00Z"
    },
    {
        "id": "nolan-non-linear",
        "name": "Christopher Nolan Chronology",
        "description": "Time dilation, practical in-camera effects, and 70mm cinematic spectacles.",
        "item_count": 5,
        "banner_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
        "curator": "Christopher Nolan Canon",
        "tags": ["Time-Bending", "Hans Zimmer", "70mm"],
        "is_private": False,
        "is_custom": False,
        "created_at": "2026-08-10T09:15:00Z"
    }
]

SEED_USER_HISTORY: List[dict] = [
    {
        "id": "018f2e4a-7b31-7000-8000-000000000001",
        "title_id": "018f2e4a-7b31-7000-8000-123456789abc",
        "canonical_title": "Dune: Part Two",
        "production_year": 2024,
        "content_type": "MOVIE",
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80",
        "watched_at": "2026-08-20T15:15:00Z",
        "rating_value": 5.0,
        "device_type": "Living Room Apple TV 4K",
        "progress_percentage": 100.0
    },
    {
        "id": "018f2e4a-7b31-7000-8000-000000000002",
        "title_id": "018f2e4a-7b31-7000-8000-223456789abc",
        "canonical_title": "Blade Runner 2049",
        "production_year": 2017,
        "content_type": "MOVIE",
        "poster_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&q=80",
        "watched_at": "2026-08-19T16:45:00Z",
        "rating_value": 5.0,
        "device_type": "Home Theater OLED 65\"",
        "progress_percentage": 100.0
    },
    {
        "id": "018f2e4a-7b31-7000-8000-000000000003",
        "title_id": "018f2e4a-7b31-7000-8000-323456789abc",
        "canonical_title": "Severance — S1:E9 'The We We Are'",
        "production_year": 2022,
        "content_type": "TV_SERIES",
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80",
        "watched_at": "2026-08-17T14:30:00Z",
        "rating_value": 5.0,
        "device_type": "iPad Pro",
        "progress_percentage": 100.0
    },
    {
        "id": "018f2e4a-7b31-7000-8000-000000000004",
        "title_id": "018f2e4a-7b31-7000-8000-423456789abc",
        "canonical_title": "Oppenheimer",
        "production_year": 2023,
        "content_type": "MOVIE",
        "poster_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=600&q=80",
        "watched_at": "2026-08-13T12:00:00Z",
        "rating_value": 4.5,
        "device_type": "Plex Server (Living Room)",
        "progress_percentage": 100.0
    }
]

# ── /v1/personal/history ───────────────────────────────────────────────────

@personal_router.get("/history", response_model=HistoryPageResponse)
async def get_personal_history(
    limit: int = 20,
    offset: int = 0,
    type: Optional[str] = None,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves paginated personal watch history with enriched title metadata."""
    items = list(SEED_USER_HISTORY)
    if type and type != "ALL":
        items = [i for i in items if i.get("content_type") == type]
    
    total = len(items)
    paged = items[offset: offset + limit]
    return HistoryPageResponse(
        items=[HistoryItemResponse(**i) for i in paged],
        total=total,
        limit=limit,
        offset=offset
    )

@personal_router.delete("/history/{id}", status_code=status.HTTP_200_OK)
async def delete_personal_history_item(
    id: str,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Deletes a watch history event by ID."""
    global SEED_USER_HISTORY
    SEED_USER_HISTORY = [i for i in SEED_USER_HISTORY if i["id"] != id]
    return {"status": "success", "deleted_id": id}

# ── /v1/personal/watchlist ─────────────────────────────────────────────────

@personal_router.get("/watchlist", response_model=WatchlistPageResponse)
async def get_personal_watchlist(
    limit: int = 20,
    offset: int = 0,
    sort: str = "added_at_desc",
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists titles the user has marked plan-to-watch, enriched with canonical title metadata."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    return await personal_repository.list_watchlist(
        db=db, user_id=user_id, limit=limit, offset=offset, sort=sort
    )

# ── /v1/personal/collections ───────────────────────────────────────────────

@personal_router.get("/collections", response_model=List[CollectionItemResponse])
async def get_personal_collections(
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves user curated and franchise collections."""
    return [CollectionItemResponse(**c) for c in SEED_USER_COLLECTIONS]

@personal_router.post("/collections", response_model=CollectionItemResponse, status_code=status.HTTP_201_CREATED)
async def create_personal_collection(
    body: CollectionCreateRequest,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Creates a new user-curated collection list."""
    new_col = {
        "id": f"custom-{len(SEED_USER_COLLECTIONS) + 1}",
        "name": body.name,
        "description": body.description or "User curated film set",
        "item_count": 0,
        "banner_url": body.banner_url or "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80",
        "curator": "My Collection",
        "tags": body.tags or ["Personal"],
        "is_private": body.is_private,
        "is_custom": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    SEED_USER_COLLECTIONS.insert(0, new_col)
    return CollectionItemResponse(**new_col)

@personal_router.delete("/collections/{id}", status_code=status.HTTP_200_OK)
async def delete_personal_collection(
    id: str,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Deletes a custom collection."""
    global SEED_USER_COLLECTIONS
    SEED_USER_COLLECTIONS = [c for c in SEED_USER_COLLECTIONS if c["id"] != id]
    return {"status": "success", "deleted_id": id}

# ── /v1/personal/analytics ─────────────────────────────────────────────────

@personal_router.get("/analytics", response_model=PersonalAnalyticsResponse)
async def get_personal_analytics(
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves live aggregate viewing analytics and taste affinity breakdown."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    metrics = await personal_repository.get_user_dashboard_metrics(db=db, user_id=user_id)

    # Aggregate taste_match_score = mean per-friend compatibility (cosine similarity
    # over UserTasteProfileModel.taste_vector), reusing the same computation the
    # social layer's friend-compatibility feature is built on (services/api/repositories/social.py).
    # No fabricated fallback: 0 friends or no taste vector yet both correctly yield 0.0,
    # same "genuinely zero vs no data yet" fix as the metrics fields below.
    # Mirrors the exact fallback style used throughout personal_repository
    # (e.g. update_user_title_state, list_watchlist): fall back to an empty
    # result in local dev, but re-raise in production instead of silently
    # masking a real failure (e.g. a regression of the "social schema not
    # migrated" bug this session fixed) as taste_match_score=0.0.
    try:
        taste_matches = await social_repository.get_taste_compatibility(db=db, user_id=user_id, limit=1000)
    except Exception as exc:
        logger.error("get_taste_compatibility failed: %s", exc, exc_info=True)
        if not config.allow_seed_fallback:
            raise
        taste_matches = []
    taste_match_score = (
        round(sum(m.compatibility_score for m in taste_matches) / len(taste_matches), 1)
        if taste_matches else 0.0
    )

    return PersonalAnalyticsResponse(
        total_watch_hours=metrics.total_watch_hours,
        watched_count=metrics.watched_count,
        total_titles=metrics.total_titles,
        monthly_watch_count=metrics.monthly_watch_count,
        annual_watch_count=metrics.annual_watch_count,
        watch_streak_days=metrics.watch_streak_days,
        taste_match_score=taste_match_score,
        movies_watched=metrics.movies_watched,
        series_completed=metrics.series_completed,
        anime_completed=metrics.anime_completed,
        # TODO(PLAN.md 1.4 follow-up): pending_recommendations_count and the
        # top_genres/top_directors/top_actors/monthly_trend breakdowns below are
        # still fully fabricated literals with no backing computation at all (not
        # even a real-metric-that-happens-to-be-zero) — out of scope for this fix,
        # flagged separately since it's a bigger lift (genre/credit joins).
        pending_recommendations_count=5,
        top_genres=[
            GenreAffinityItem(genre="Sci-Fi", count=48, percentage=33.8),
            GenreAffinityItem(genre="Cyberpunk / Neo-Noir", count=32, percentage=22.5),
            GenreAffinityItem(genre="Drama / Psychological", count=28, percentage=19.7),
            GenreAffinityItem(genre="Thriller", count=20, percentage=14.1),
            GenreAffinityItem(genre="Anime / Animation", count=14, percentage=9.9),
        ],
        top_directors=[
            CreatorAffinityItem(name="Denis Villeneuve", role="Director", count=9),
            CreatorAffinityItem(name="Christopher Nolan", role="Director", count=8),
            CreatorAffinityItem(name="Ridley Scott", role="Director", count=7),
            CreatorAffinityItem(name="David Fincher", role="Director", count=6),
            CreatorAffinityItem(name="Hayao Miyazaki", role="Director", count=5),
        ],
        top_actors=[
            CreatorAffinityItem(name="Timothée Chalamet", role="Actor", count=6),
            CreatorAffinityItem(name="Ryan Gosling", role="Actor", count=5),
            CreatorAffinityItem(name="Cillian Murphy", role="Actor", count=5),
            CreatorAffinityItem(name="Rebecca Ferguson", role="Actor", count=4),
            CreatorAffinityItem(name="Christian Bale", role="Actor", count=4),
        ],
        monthly_trend=[
            MonthlyTrendItem(month="Mar", count=12, hours=28.0),
            MonthlyTrendItem(month="Apr", count=15, hours=34.5),
            MonthlyTrendItem(month="May", count=19, hours=42.0),
            MonthlyTrendItem(month="Jun", count=14, hours=31.0),
            MonthlyTrendItem(month="Jul", count=22, hours=51.5),
            MonthlyTrendItem(month="Aug", count=18, hours=41.0),
        ]
    )

# ── /v1/personal/import ────────────────────────────────────────────────────

@personal_router.post("/import/preview", response_model=ImportPreviewResponse)
async def preview_personal_import(
    body: ImportPreviewRequest,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Previews personal library import, validating matches and detecting conflicts."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    
    # If DB is not connected, provide a rich matching preview simulation
    if db is None:
        matched = 0
        unmatched = 0
        conflicts = []
        for idx, item in enumerate(body.items):
            if item.canonical_title:
                matched += 1
                # If rating is 5 and title mentions dune or oppenheimer, simulate a possible conflict for demo
                if item.rating_value and item.rating_value == 5 and "dune" in item.canonical_title.lower():
                    conflicts.append(
                        ImportConflictItem(
                            title_id=f"sim-{idx}",
                            canonical_title=item.canonical_title,
                            field_name="rating_value",
                            existing_value=4,
                            imported_value=5
                        )
                    )
            else:
                unmatched += 1
        return ImportPreviewResponse(
            total_items=len(body.items),
            matched_titles=matched,
            unmatched_titles=unmatched,
            conflicts_count=len(conflicts),
            conflicts=conflicts
        )

    return await personal_repository.preview_user_import(
        db=db,
        user_id=user_id,
        items=body.items
    )

@personal_router.post("/import/apply", response_model=ImportApplyResponse, status_code=status.HTTP_200_OK)
async def apply_personal_import(
    body: ImportApplyRequest,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Applies imported personal library records using chosen conflict resolution strategy."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"

    if db is None:
        # Update in-memory seed history
        for item in body.items:
            if item.canonical_title:
                SEED_USER_HISTORY.insert(0, {
                    "id": f"imp-{len(SEED_USER_HISTORY) + 1}",
                    "title_id": item.title_id or f"imp-title-{len(SEED_USER_HISTORY) + 1}",
                    "canonical_title": item.canonical_title,
                    "production_year": item.production_year or 2024,
                    "content_type": "MOVIE",
                    "poster_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&q=80",
                    "watched_at": item.watched_at or datetime.now(timezone.utc).isoformat(),
                    "rating_value": float(item.rating_value) if item.rating_value else None,
                    "device_type": "Imported Record",
                    "progress_percentage": item.progress_percentage or 100.0
                })
        return ImportApplyResponse(
            applied_count=len(body.items),
            conflicts_resolved=0,
            strategy_applied=body.conflict_strategy.value,
            applied_at=datetime.now(timezone.utc).isoformat()
        )

    return await personal_repository.apply_user_import(
        db=db,
        user_id=user_id,
        items=body.items,
        conflict_strategy=body.conflict_strategy.value
    )

# ── Standard /v1/me Routes ─────────────────────────────────────────────────



@router.get("/dashboard", response_model=UserDashboardMetricsResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_dashboard_metrics(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves comprehensive personal media metrics and analytics dynamically for authenticated user."""
    return await personal_repository.get_user_dashboard_metrics(db=db, user_id=claims.sub)

@router.get("/watch-events", response_model=PaginatedResponse[WatchEventResponse], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def list_watch_events(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists append-only watch events owned by current authenticated user (CAT-2)."""
    events = await personal_repository.list_watch_events(db=db, user_id=claims.sub)
    return PaginatedResponse(data=events, pagination=CursorPagination(limit=25, has_more=False))

@router.post("/watch-events", response_model=WatchEventResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def create_watch_event(
    body: WatchEventCreate,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Appends an immutable watch event log. Idempotency enforced via header or mutation ID."""
    return await personal_repository.create_watch_event(
        db=db,
        user_id=claims.sub,
        body=body,
        idempotency_key=x_idempotency_key
    )

@router.get("/title-states/{title_id}", response_model=UserTitleStateResponse)
async def get_user_title_state(
    title_id: str,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves user title library state (watching status, favorite flag, preferred edition)."""
    return await personal_repository.get_user_title_state(db=db, user_id=claims.sub, title_id=title_id)

@router.patch("/title-states/{title_id}", response_model=UserTitleStateResponse, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def update_user_title_state(
    title_id: str,
    body: UserTitleStateUpdate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Updates user title library state."""
    return await personal_repository.update_user_title_state(
        db=db,
        user_id=claims.sub,
        title_id=title_id,
        body=body
    )

@router.get("/ratings", response_model=List[RatingResponse])
async def list_ratings(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists ratings created by user."""
    return await personal_repository.list_ratings(db=db, user_id=claims.sub)

@router.post("/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def set_rating(
    body: RatingCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Sets title rating (1-10 scale)."""
    return await personal_repository.set_rating(db=db, user_id=claims.sub, body=body)

@router.get("/notes", response_model=List[NoteResponse])
async def list_notes(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists private personal notes created by user."""
    return await personal_repository.list_notes(db=db, user_id=claims.sub)

@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def create_note(
    body: NoteCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Creates or updates private personal note."""
    return await personal_repository.create_note(db=db, user_id=claims.sub, body=body)

@router.get("/reviews", response_model=List[ReviewResponse])
async def list_reviews(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists reviews created by user."""
    return await personal_repository.list_reviews(db=db, user_id=claims.sub)

@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def create_review(
    body: ReviewCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Creates review."""
    return await personal_repository.create_review(db=db, user_id=claims.sub, body=body)

@router.get("/conflicts", response_model=List[PersonalDataConflictResponse])
async def list_conflicts(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves active user personal data conflicts generated by canonical entity merges/splits."""
    return await personal_repository.list_conflicts(db=db, user_id=claims.sub)

@router.post("/conflicts/{conflict_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_conflict(
    conflict_id: str,
    body: PersonalDataConflictResolveRequest,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Submits user's explicit resolution choice for personal data conflict."""
    return {
        "status": "RESOLVED",
        "conflict_id": conflict_id,
        "chosen_option_id": body.chosen_option_id
    }

@router.get("/export", response_model=PersonalDataExportResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def export_personal_data(
    format: str = "json",
    scope: Optional[str] = None,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Exports personal library data (watch history, ratings, title states, notes, custom lists) for portability."""
    return await personal_repository.export_user_data(
        db=db,
        user_id=claims.sub,
        export_format=format,
        scope=scope
    )

@router.post("/import/preview", response_model=ImportPreviewResponse, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def preview_personal_data_import(
    body: ImportPreviewRequest,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Validates imported records, matches canonical titles, and detects existing conflicts before applying."""
    return await personal_repository.preview_user_import(
        db=db,
        user_id=claims.sub,
        items=body.items
    )

@router.post("/import/apply", response_model=ImportApplyResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def apply_personal_data_import(
    body: ImportApplyRequest,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Applies imported personal library records using the user's chosen conflict resolution strategy."""
    return await personal_repository.apply_user_import(
        db=db,
        user_id=claims.sub,
        items=body.items,
        conflict_strategy=body.conflict_strategy.value
    )
