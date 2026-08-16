# CineVault OS — Social Core API Router (v2.0 Module 1)
# Implements Friendships, Peer Recommendations, and Recommendation State Machine (ADR-003, ADR-004)

import logging
from typing import Optional, List
import uuid
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.social import (
    FriendshipStatusEnum,
    FriendshipResponse,
    FriendshipCreate,
    FriendshipUpdate,
    RecommendationStatusEnum,
    RecommendationCreate,
    RecommendationStateUpdate,
    RecommendationResponse,
)
from ..auth.dependencies import require_authenticated_user, get_optional_claims
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.social import social_repository, _resolve_uuid

logger = logging.getLogger("cinevault.routers.social")

router = APIRouter(prefix="/social", tags=["Social Core (v2.0 Module 1)"])


def _extract_user_id(claims: Optional[SecurityTokenClaims]) -> uuid.UUID:
    """Extracts a valid UUID from security claims sub or generates a fallback for test environments."""
    if claims and hasattr(claims, "sub") and claims.sub:
        return _resolve_uuid(claims.sub, "user_id")
    # Default system/dev test UUID if claims missing
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


# =============================================================================
# Peer Recommendations & State Machine
# =============================================================================

@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def create_recommendation(
    body: RecommendationCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Creates a new peer recommendation in the 'SENT' state.
    Precondition: Requester and Recipient must be established ACCEPTED friends.
    """
    sender_id = _extract_user_id(claims)

    try:
        recommendation = await social_repository.create_recommendation(
            db=db,
            sender_id=sender_id,
            body=body,
        )
        return recommendation
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/recommendations/{id}",
    response_model=RecommendationResponse,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def update_recommendation_state(
    id: uuid.UUID = Path(..., description="Target recommendation UUID"),
    body: RecommendationStateUpdate = ...,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Updates the lifecycle state of a peer recommendation enforcing strict state machine transitions:
    - SENT -> ACCEPTED or REJECTED
    - ACCEPTED -> WATCHED
    - WATCHED -> RATED (requires recipient_actual_rating)
    """
    actor_id = _extract_user_id(claims)

    try:
        updated = await social_repository.update_recommendation_state(
            db=db,
            recommendation_id=id,
            body=body,
            actor_id=actor_id,
        )
        return updated
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/recommendations/{id}",
    response_model=RecommendationResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_recommendation_by_id(
    id: uuid.UUID = Path(..., description="Recommendation UUID"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Retrieves a single recommendation record by ID."""
    rec = await social_repository.get_recommendation(db=db, recommendation_id=id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with ID {id} not found.",
        )
    return rec


@router.get(
    "/recommendations",
    response_model=List[RecommendationResponse],
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def list_user_recommendations(
    role: str = Query("all", description="Filter by role: 'sent', 'received', or 'all'"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Lists social recommendations for the current authenticated user."""
    user_id = _extract_user_id(claims)
    return await social_repository.list_recommendations(db=db, user_id=user_id, role=role)


# =============================================================================
# Friendships & Peer Graph
# =============================================================================

@router.post(
    "/friendships",
    response_model=FriendshipResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def create_friendship_request(
    body: FriendshipCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Initiates a friend request to a peer user."""
    requester_id = _extract_user_id(claims)
    if requester_id == body.addressee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot create a friendship with themselves.",
        )
    return await social_repository.create_friendship(
        db=db,
        requester_id=requester_id,
        addressee_id=body.addressee_id,
        status=FriendshipStatusEnum.PENDING,
        trust_score=body.trust_score or 50.0,
    )


@router.patch(
    "/friendships/{id}",
    response_model=FriendshipResponse,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def update_friendship_status(
    id: uuid.UUID = Path(..., description="Friendship UUID"),
    body: FriendshipUpdate = ...,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Updates the status of a friendship relationship (e.g. ACCEPTED or BLOCKED)."""
    updated = await social_repository.update_friendship_status(
        db=db,
        friendship_id=id,
        status=body.status,
        trust_score=body.trust_score,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Friendship with ID {id} not found.",
        )
    return updated


@router.get(
    "/friendships",
    response_model=List[FriendshipResponse],
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def list_user_friendships(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Lists all friendships associated with the authenticated user."""
    user_id = _extract_user_id(claims)
    return await social_repository.list_friendships(db=db, user_id=user_id)
