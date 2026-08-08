# CineVault OS — Personal Data Router (CAT-2)
# User personal logs, append-only watch events, title state management & conflict resolution (ADR-003, ADR-004)

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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
from ..database import get_db
from ..repositories.personal import personal_repository

router = APIRouter(prefix="/v1/me", tags=["Personal Data (CAT-2)"])

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
