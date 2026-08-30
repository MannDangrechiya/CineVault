# CineVault OS — Personal Data Router (CAT-2)
# User personal logs, append-only watch events, title state management & conflict resolution (ADR-003, ADR-004)

import io
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, Query, Response, status
from pypdf import PdfReader
from pypdf.errors import PdfReadError
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
    ImportPreviewRequest, ImportPreviewResponse,
    ImportApplyRequest, ImportApplyResponse, PdfExtractResponse,
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
from ..personal.export_service import (
    build_json_export, build_csv_zip_export, build_excel_export, build_markdown_export
)
from ..personal.mapping import (
    parse_csv_content, parse_json_content, parse_xlsx_content, parse_unstructured_text_content,
    convert_raw_dict_to_import_payload
)

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

@personal_router.post("/import/extract-pdf", response_model=PdfExtractResponse)
async def extract_pdf_text_for_import(
    file: UploadFile = File(...),
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
):
    """
    Extracts raw text from an uploaded PDF for the Import Wizard's parse pipeline.
    Uses pypdf's embedded-text-layer extraction — this covers text-based PDFs
    (typed notes, exported lists, Letterboxd/Trakt PDF exports) but does NOT run
    OCR, so scanned/photographed pages with no text layer yield no content for
    that page rather than silently fabricating text; callers should fall back to
    a plain-text export for those. The returned text is handed to the same
    parseImportText → preview/apply pipeline already used for pasted notes.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .pdf files are supported by this endpoint.")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
    except PdfReadError as exc:
        logger.warning("Failed to open uploaded PDF for import: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read this PDF — it may be corrupted or password-protected.",
        ) from exc

    if reader.is_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password-protected PDFs are not supported.")

    page_texts: List[str] = []
    empty_pages = 0
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            logger.warning("Failed to extract text from a page of uploaded PDF: %s", exc)
            text = ""
        if text.strip():
            page_texts.append(text)
        else:
            empty_pages += 1

    extracted_text = "\n\n".join(page_texts).strip()
    warning: Optional[str] = None
    if empty_pages:
        warning = (
            f"{empty_pages} of {len(reader.pages)} page(s) had no extractable text layer "
            "(likely scanned images) and were skipped — OCR is not supported yet."
        )

    if not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=warning or "No text could be extracted from this PDF.",
        )

    return PdfExtractResponse(
        extracted_text=extracted_text,
        page_count=len(reader.pages),
        warning=warning,
    )


@personal_router.post("/import/preview", response_model=ImportPreviewResponse)
async def preview_personal_import(
    body: ImportPreviewRequest,
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Previews personal library import, validating matches and detecting conflicts."""
    user_id = claims.sub if claims else "00000000-0000-0000-0000-000000000001"

    # No `db is None` branch here: get_db() only ever yields None when
    # config.allow_seed_fallback is explicitly enabled (local dev without
    # Docker). preview_user_import already handles db=None honestly by
    # returning zero matches/conflicts -- it never fabricates simulated
    # title matches or confidence scores.
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

    # No `db is None` branch here: get_db() only ever yields None when
    # config.allow_seed_fallback is explicitly enabled (local dev without
    # Docker). apply_user_import already handles db=None honestly by
    # reporting applied_count=0 -- it never fabricates persisted rows.
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
@personal_router.get("/watch-events", response_model=PaginatedResponse[WatchEventResponse], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def list_watch_events(
    title_id: Optional[str] = None,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists append-only watch events owned by current authenticated user (CAT-2), optionally filtered by title_id."""
    events = await personal_repository.list_watch_events(db=db, user_id=claims.sub, title_id=title_id)
    return PaginatedResponse(data=events, pagination=CursorPagination(limit=25, has_more=False))

@router.post("/watch-events", response_model=WatchEventResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
@personal_router.post("/watch-events", response_model=WatchEventResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
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
@personal_router.get("/title-states/{title_id}", response_model=UserTitleStateResponse)
async def get_user_title_state(
    title_id: str,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves user title library state (watching status, favorite flag, preferred edition)."""
    return await personal_repository.get_user_title_state(db=db, user_id=claims.sub, title_id=title_id)

@router.patch("/title-states/{title_id}", response_model=UserTitleStateResponse, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
@personal_router.patch("/title-states/{title_id}", response_model=UserTitleStateResponse, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
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
@personal_router.get("/ratings", response_model=List[RatingResponse])
async def list_ratings(
    title_id: Optional[str] = None,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists ratings created by user, optionally filtered by title_id."""
    return await personal_repository.list_ratings(db=db, user_id=claims.sub, title_id=title_id)

@router.post("/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
@personal_router.post("/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def set_rating(
    body: RatingCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Sets title rating (1-10 scale)."""
    return await personal_repository.set_rating(db=db, user_id=claims.sub, body=body)

@router.delete("/ratings/{title_id}", status_code=status.HTTP_200_OK)
@personal_router.delete("/ratings/{title_id}", status_code=status.HTTP_200_OK)
async def delete_rating(
    title_id: str,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Deletes user's rating for a title."""
    deleted = await personal_repository.delete_rating(db=db, user_id=claims.sub, title_id=title_id)
    if not deleted:
        return {"status": "not_found", "title_id": title_id}
    return {"status": "success", "title_id": title_id}

@router.get("/notes", response_model=List[NoteResponse])
@personal_router.get("/notes", response_model=List[NoteResponse])
async def list_notes(
    title_id: Optional[str] = None,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists private personal notes created by user, optionally filtered by title_id."""
    return await personal_repository.list_notes(db=db, user_id=claims.sub, title_id=title_id)

@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
@personal_router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def create_note(
    body: NoteCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Creates or updates private personal note."""
    return await personal_repository.create_note(db=db, user_id=claims.sub, body=body)

@router.delete("/notes/{note_id}", status_code=status.HTTP_200_OK)
@personal_router.delete("/notes/{note_id}", status_code=status.HTTP_200_OK)
async def delete_note(
    note_id: str,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Deletes a private personal note owned by the user."""
    deleted = await personal_repository.delete_note(db=db, user_id=claims.sub, note_id=note_id)
    if not deleted:
        return {"status": "not_found", "note_id": note_id}
    return {"status": "success", "note_id": note_id}

@router.get("/reviews", response_model=List[ReviewResponse])
@personal_router.get("/reviews", response_model=List[ReviewResponse])
async def list_reviews(
    title_id: Optional[str] = None,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists reviews created by user, optionally filtered by title_id."""
    return await personal_repository.list_reviews(db=db, user_id=claims.sub, title_id=title_id)

@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
@personal_router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def create_review(
    body: ReviewCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Creates review."""
    return await personal_repository.create_review(db=db, user_id=claims.sub, body=body)

@router.delete("/reviews/{review_id}", status_code=status.HTTP_200_OK)
@personal_router.delete("/reviews/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    review_id: str,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Deletes a review owned by the user."""
    deleted = await personal_repository.delete_review(db=db, user_id=claims.sub, review_id=review_id)
    if not deleted:
        return {"status": "not_found", "review_id": review_id}
    return {"status": "success", "review_id": review_id}

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

@router.get("/export", dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
@personal_router.get("/export", dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def export_personal_data(
    format: str = Query("json", description="Export format: json, csv, excel, xlsx, markdown, md"),
    download: bool = Query(False, description="Whether to trigger file attachment download"),
    scope: Optional[str] = None,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Exports personal library data (watch history, ratings, title states, notes, custom lists) for portability."""
    raw_data = await personal_repository.export_user_data(
        db=db,
        user_id=claims.sub,
        export_format=format,
        scope=scope
    )
    fmt = format.lower().strip()
    ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if fmt == "json":
        if not download:
            return raw_data
        json_content = build_json_export(raw_data)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="cinevault_export_{ts_str}.json"'}
        )
    elif fmt == "csv":
        zip_bytes = build_csv_zip_export(raw_data)
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="cinevault_export_{ts_str}.zip"'}
        )
    elif fmt in ("excel", "xlsx"):
        xlsx_bytes = build_excel_export(raw_data)
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="cinevault_export_{ts_str}.xlsx"'}
        )
    elif fmt in ("markdown", "md"):
        md_text = build_markdown_export(raw_data)
        return Response(
            content=md_text,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="cinevault_export_{ts_str}.md"'}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{format}'. Supported formats are: json, csv, excel, xlsx, markdown, md."
        )

@router.post("/import/upload", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
@personal_router.post("/import/upload", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def upload_import_file(
    file: UploadFile = File(...),
    claims: SecurityTokenClaims = Depends(require_authenticated_user)
):
    """Uploads and parses CSV, Excel (.xlsx), JSON, or text documents into normalized import candidate items."""
    MAX_FILE_SIZE = 25 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds maximum allowed size of 25MB."
        )

    filename = (file.filename or "").lower()
    raw_rows: List[Dict[str, Any]] = []

    try:
        if filename.endswith(".xlsx"):
            raw_rows = parse_xlsx_content(content)
        elif filename.endswith(".json"):
            text = content.decode("utf-8", errors="replace")
            raw_rows = parse_json_content(text)
        elif filename.endswith(".csv"):
            text = content.decode("utf-8", errors="replace")
            raw_rows = parse_csv_content(text)
        elif filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(content))
            extracted_pages = []
            for p in reader.pages:
                t = p.extract_text()
                if t:
                    extracted_pages.append(t)
            full_text = "\n".join(extracted_pages)
            raw_rows = parse_unstructured_text_content(full_text)
        else:
            text = content.decode("utf-8", errors="replace")
            if "," in text and "\n" in text:
                raw_rows = parse_csv_content(text)
            if not raw_rows:
                raw_rows = parse_unstructured_text_content(text)
    except Exception as exc:
        logger.error("Failed to parse uploaded import file %s: %s", file.filename, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse import file '{file.filename}'. Please verify file integrity and format."
        )

    items = [convert_raw_dict_to_import_payload(r) for r in raw_rows]
    valid_items = [it for it in items if it.get("canonical_title") or it.get("title_id")]

    return {
        "filename": file.filename,
        "total_parsed": len(valid_items),
        "items": valid_items
    }

@router.post("/import/preview", response_model=ImportPreviewResponse, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
@personal_router.post("/import/preview", response_model=ImportPreviewResponse, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
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
@personal_router.post("/import/apply", response_model=ImportApplyResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
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
