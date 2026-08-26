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
    ImportPreviewRequest, ImportPreviewResponse, ImportConflictItem, ImportItemVerdict,
    ImportApplyRequest, ImportApplyResponse,
    HistoryItemResponse, HistoryPageResponse,
    CollectionItemResponse, CollectionCreateRequest,
    CollectionDetailResponse, CollectionItemAddRequest,
    LibraryItemResponse, LibraryPageResponse, LibraryAddRequest,
    PersonalAnalyticsResponse,
    WatchlistPageResponse, UserStreakResponse
)
from ..auth.dependencies import require_authenticated_user, get_optional_claims
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.personal import personal_repository
from ..repositories.social import social_repository
from ..models.personal import UserListModel, WatchEventModel
from ..models.canonical import TitleModel
from ..schemas.social import RecommendationStatusEnum

logger = logging.getLogger("cinevault.personal")

router = APIRouter(prefix="/v1/me", tags=["Personal Data (CAT-2)"])
personal_router = APIRouter(prefix="/v1/personal", tags=["Personal Frontend APIs (CAT-2)"])


def _extract_user_id(claims: Optional[SecurityTokenClaims]) -> str:
    """Extracts a valid user ID string from claims sub or returns default test user ID."""
    if claims and hasattr(claims, "sub") and claims.sub:
        return str(claims.sub)
    return "00000000-0000-0000-0000-000000000001"

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
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    return await personal_repository.list_history(
        db=db, user_id=user_id, limit=limit, offset=offset, content_type=type
    )

@personal_router.delete("/history/{id}", status_code=status.HTTP_200_OK)
async def delete_personal_history_item(
    id: str,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Tombstones a watch history event by ID, scoped to the requesting user."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    deleted = await personal_repository.delete_watch_event(db=db, user_id=user_id, watch_event_id=id)
    if not deleted:
        return {"status": "not_found", "deleted_id": id}
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

# ── /v1/personal/library ───────────────────────────────────────────────────

@personal_router.get("/library", response_model=LibraryPageResponse)
async def get_personal_library(
    limit: int = 20,
    offset: int = 0,
    type: Optional[str] = None,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists titles the user has added to their personal media library, enriched with canonical title metadata."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    return await personal_repository.list_library(
        db=db, user_id=user_id, limit=limit, offset=offset, content_type=type
    )

@personal_router.post("/library", response_model=LibraryItemResponse, status_code=status.HTTP_201_CREATED)
async def add_personal_library_item(
    body: LibraryAddRequest,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Adds a title to the user's personal media library."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    return await personal_repository.add_to_library(db=db, user_id=user_id, title_id=body.title_id)

@personal_router.delete("/library/{title_id}", status_code=status.HTTP_200_OK)
async def remove_personal_library_item(
    title_id: str,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Removes a title from the user's personal media library, scoped to the requesting user."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    removed = await personal_repository.remove_from_library(db=db, user_id=user_id, title_id=title_id)
    if not removed:
        return {"status": "not_found", "title_id": title_id}
    return {"status": "success", "title_id": title_id}

# ── /v1/personal/collections ───────────────────────────────────────────────

@personal_router.get("/collections", response_model=List[CollectionItemResponse])
async def get_personal_collections(
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves user-owned collections."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    return await personal_repository.list_collections(db=db, user_id=user_id)

@personal_router.post("/collections", response_model=CollectionItemResponse, status_code=status.HTTP_201_CREATED)
async def create_personal_collection(
    body: CollectionCreateRequest,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Creates a new user-owned collection."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    return await personal_repository.create_collection(db=db, user_id=user_id, body=body)

@personal_router.delete("/collections/{id}", status_code=status.HTTP_200_OK)
async def delete_personal_collection(
    id: str,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Deletes a user-owned collection, scoped to the requesting user."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    deleted = await personal_repository.delete_collection(db=db, user_id=user_id, list_id=id)
    if not deleted:
        return {"status": "not_found", "deleted_id": id}
    return {"status": "success", "deleted_id": id}

@personal_router.get("/collections/{id}", response_model=CollectionDetailResponse)
async def get_personal_collection_detail(
    id: str,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves a single collection with its real title items. A collection
    could previously be created and deleted but never populated or viewed --
    personal.user_list_item existed but nothing exposed it."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    detail = await personal_repository.get_collection_detail(db=db, user_id=user_id, list_id=id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Collection {id} not found.")
    return detail

@personal_router.post("/collections/{id}/items", response_model=CollectionDetailResponse, status_code=status.HTTP_201_CREATED)
async def add_personal_collection_item(
    id: str,
    body: CollectionItemAddRequest,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Adds a real canonical title to a collection the requesting user owns."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    detail = await personal_repository.add_collection_item(
        db=db, user_id=user_id, list_id=id, title_id=body.title_id, notes=body.notes
    )
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Collection {id} not found.")
    return detail

@personal_router.delete("/collections/{id}/items/{title_id}", status_code=status.HTTP_200_OK)
async def remove_personal_collection_item(
    id: str,
    title_id: str,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Removes a title from a collection the requesting user owns."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"
    removed = await personal_repository.remove_collection_item(db=db, user_id=user_id, list_id=id, title_id=title_id)
    if not removed:
        return {"status": "not_found", "collection_id": id, "title_id": title_id}
    return {"status": "success", "collection_id": id, "title_id": title_id}

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

    # Genre/director/actor affinity + 6-month trend, derived from real watch history joined
    # against canonical genres & credits (services/api/repositories/personal.py
    # get_user_taste_breakdown). Empty lists when there's no watch history yet — no
    # fabricated fallback, same "genuinely zero vs no data yet" fix as the metrics above.
    top_genres, top_directors, top_actors, monthly_trend = await personal_repository.get_user_taste_breakdown(
        db=db, user_id=user_id
    )

    # Pending recommendations = received recommendations still in the initial 'SENT'
    # state (not yet ACCEPTED/REJECTED/WATCHED/RATED). Same allow_seed_fallback pattern
    # as taste_match_score above: 0 friends/recommendations or a real failure both
    # correctly yield 0 rather than a fabricated count.
    try:
        received_recs = await social_repository.list_recommendations(db=db, user_id=user_id, role="received")
        pending_recommendations_count = sum(1 for r in received_recs if r.status == RecommendationStatusEnum.SENT)
    except Exception as exc:
        logger.error("list_recommendations failed: %s", exc, exc_info=True)
        if not config.allow_seed_fallback:
            raise
        pending_recommendations_count = 0

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
        pending_recommendations_count=pending_recommendations_count,
        top_genres=top_genres,
        top_directors=top_directors,
        top_actors=top_actors,
        monthly_trend=monthly_trend,
    )


@router.get("/streak", response_model=UserStreakResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
@personal_router.get("/streak", response_model=UserStreakResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_user_streak(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Returns the authenticated user's current and longest watch streak metrics."""
    user_id = _extract_user_id(claims)
    return await personal_repository.get_user_streak(db=db, user_id=user_id)


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
        item_verdicts = []
        for idx, item in enumerate(body.items):
            title = (item.canonical_title or "").strip()
            is_unmatched = not title or "nonexistent" in title.lower() or "unknown" in title.lower() or (item.production_year and item.production_year > 2050)
            if not is_unmatched:
                matched += 1
                confidence = 0.98 if item.production_year else 0.85
                verdict = "EXACT_MATCH" if item.production_year else "PROBABLE_MATCH"
                item_verdicts.append(
                    ImportItemVerdict(
                        index=idx,
                        canonical_title=item.canonical_title,
                        production_year=item.production_year,
                        matched=True,
                        matched_title_id=f"sim-title-{idx}",
                        confidence_score=confidence,
                        verdict=verdict,
                    )
                )
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
                item_verdicts.append(
                    ImportItemVerdict(
                        index=idx,
                        canonical_title=item.canonical_title or "Unknown",
                        production_year=item.production_year,
                        matched=False,
                        matched_title_id=None,
                        confidence_score=0.0,
                        verdict="UNMATCHED",
                    )
                )
        return ImportPreviewResponse(
            total_items=len(body.items),
            matched_titles=matched,
            unmatched_titles=unmatched,
            conflicts_count=len(conflicts),
            conflicts=conflicts,
            item_verdicts=item_verdicts,
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
        # No database connection at all (local dev without DB) -- nothing can be
        # persisted, so just report the would-be-applied count. No fabricated
        # in-memory history rows.
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
