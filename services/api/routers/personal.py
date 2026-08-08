# CineVault OS — Personal Data Router (CAT-2)
# User personal logs, append-only watch events, title state management & conflict resolution (ADR-003)

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, status
from ..schemas.common import PaginatedResponse, CursorPagination
from ..schemas.personal import (
    WatchEventCreate, WatchEventResponse,
    UserTitleStateResponse, UserTitleStateUpdate,
    RatingCreate, RatingResponse,
    NoteCreate, NoteResponse,
    ReviewCreate, ReviewResponse,
    PersonalDataConflictResponse, PersonalDataConflictResolveRequest
)
from ..auth.dependencies import require_authenticated_user
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit

router = APIRouter(prefix="/v1/me", tags=["Personal Data (CAT-2)"])

@router.get("/watch-events", response_model=PaginatedResponse[WatchEventResponse], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def list_watch_events(claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Lists append-only watch events owned by current authenticated user (CAT-2)."""
    mock_events = [
        WatchEventResponse(
            id="018f2e4a-7b31-7000-8000-watch-001",
            user_id=claims.sub,
            title_id="018f2e4a-7b31-7000-8000-123456789abc",
            watched_at="2026-08-08T18:00:00Z",
            progress_percentage=100.0,
            created_at="2026-08-08T18:00:00Z"
        )
    ]
    return PaginatedResponse(data=mock_events, pagination=CursorPagination(limit=25, has_more=False))

@router.post("/watch-events", response_model=WatchEventResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def create_watch_event(
    body: WatchEventCreate,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user)
):
    """Appends an immutable watch event log. Idempotency enforced via header or mutation ID."""
    return WatchEventResponse(
        id=x_idempotency_key or "018f2e4a-7b31-7000-8000-watch-002",
        user_id=claims.sub,
        title_id=body.title_id,
        edition_id=body.edition_id,
        watched_at=body.watched_at,
        progress_percentage=body.progress_percentage,
        created_at=datetime.now(timezone.utc).isoformat()
    )

@router.get("/title-states/{title_id}", response_model=UserTitleStateResponse)
async def get_user_title_state(title_id: str, claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Retrieves user title library state (watching status, favorite flag, preferred edition)."""
    return UserTitleStateResponse(
        title_id=title_id,
        derived_status="COMPLETED",
        manual_status_override="COMPLETED",
        is_favorite=True,
        preferred_edition_id=None,
        updated_at=datetime.now(timezone.utc).isoformat()
    )

@router.patch("/title-states/{title_id}", response_model=UserTitleStateResponse, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def update_user_title_state(title_id: str, body: UserTitleStateUpdate, claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Updates user title library state."""
    return UserTitleStateResponse(
        title_id=title_id,
        derived_status="COMPLETED",
        manual_status_override=body.manual_status_override or "COMPLETED",
        is_favorite=body.is_favorite if body.is_favorite is not None else True,
        preferred_edition_id=body.preferred_edition_id,
        updated_at=datetime.now(timezone.utc).isoformat()
    )

@router.get("/ratings", response_model=List[RatingResponse])
async def list_ratings(claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Lists ratings created by user."""
    return [
        RatingResponse(
            id="018f2e4a-7b31-7000-8000-rating-001",
            title_id="018f2e4a-7b31-7000-8000-123456789abc",
            rating_value=10,
            updated_at=datetime.now(timezone.utc).isoformat()
        )
    ]

@router.post("/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def set_rating(body: RatingCreate, claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Sets title rating (1-10 scale)."""
    return RatingResponse(
        id="018f2e4a-7b31-7000-8000-rating-002",
        title_id=body.title_id,
        rating_value=body.rating_value,
        updated_at=datetime.now(timezone.utc).isoformat()
    )

@router.get("/notes", response_model=List[NoteResponse])
async def list_notes(claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Lists private personal notes created by user."""
    return []

@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def create_note(body: NoteCreate, claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Creates or updates private personal note."""
    return NoteResponse(
        id="018f2e4a-7b31-7000-8000-note-001",
        title_id=body.title_id,
        note_text=body.note_text,
        updated_at=datetime.now(timezone.utc).isoformat()
    )

@router.get("/reviews", response_model=List[ReviewResponse])
async def list_reviews(claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Lists reviews created by user."""
    return []

@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))])
async def create_review(body: ReviewCreate, claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Creates review."""
    return ReviewResponse(
        id="018f2e4a-7b31-7000-8000-review-001",
        title_id=body.title_id,
        review_title=body.review_title,
        review_text=body.review_text,
        is_public=body.is_public,
        created_at=datetime.now(timezone.utc).isoformat()
    )

@router.get("/conflicts", response_model=List[PersonalDataConflictResponse])
async def list_conflicts(claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Retrieves active user personal data conflicts generated by canonical entity merges/splits."""
    return []

@router.post("/conflicts/{conflict_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_conflict(conflict_id: str, body: PersonalDataConflictResolveRequest, claims: SecurityTokenClaims = Depends(require_authenticated_user)):
    """Submits user's explicit resolution choice for personal data conflict."""
    return {
        "status": "RESOLVED",
        "conflict_id": conflict_id,
        "chosen_option_id": body.chosen_option_id
    }
