# CineVault OS — Social Core API Router (v2.0 Module 1 & 2)
# Implements Friendships, Peer Recommendations, and Taste Vector Compatibility (ADR-003, ADR-004)

import logging
import math
import random
from typing import Optional, List, Dict, Any
import uuid
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.social import (
    FriendshipStatusEnum,
    FriendshipResponse,
    FriendshipCreate,
    FriendshipUpdate,
    EnrichedFriendshipResponse,
    RecommendationStatusEnum,
    RecommendationCreate,
    RecommendationStateUpdate,
    RecommendationResponse,
    EnrichedRecommendationResponse,
    TasteMatchResponse,
    UserTasteProfileUpdate,
    UserTasteProfileResponse,
    TasteProfileComputeRequest,
)
from ..auth.dependencies import require_authenticated_user, get_optional_claims
from ..auth.jwt_validator import SecurityTokenClaims
from ..auth.user_directory import resolve_display_names
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.social import social_repository, _resolve_uuid, resolve_friend_id
from ..repositories.canonical import canonical_repository
from ..ai.ollama_client import OllamaClient


logger = logging.getLogger("cinevault.routers.social")

router = APIRouter(prefix="/social", tags=["Social Core (v2.0 Module 1 & 2)"])


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
    response_model=List[EnrichedRecommendationResponse],
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def list_user_recommendations(
    role: str = Query("all", description="Filter by role: 'sent', 'received', or 'all'"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Lists social recommendations for the current authenticated user, enriched
    with joined canonical.title metadata and best-effort sender/recipient
    display names (PLAN.md 1.2 — the raw RecommendationResponse only carried
    UUIDs, which rendered as "Unknown Title" / "Anonymous" on the frontend).
    """
    user_id = _extract_user_id(claims)
    recommendations = await social_repository.list_recommendations(db=db, user_id=user_id, role=role)
    if not recommendations:
        return []

    title_map = await canonical_repository.get_titles_map(db, list({r.title_id for r in recommendations}))
    name_map = resolve_display_names(
        {uid for r in recommendations for uid in (r.sender_id, r.recipient_id)}
    )

    enriched: List[EnrichedRecommendationResponse] = []
    for r in recommendations:
        title = title_map.get(r.title_id)
        sender_name, sender_username = name_map[str(r.sender_id)]
        recipient_name, recipient_username = name_map[str(r.recipient_id)]
        enriched.append(
            EnrichedRecommendationResponse(
                **r.model_dump(),
                canonical_title=title.canonical_title if title else None,
                poster_url=title.poster_url if title else None,
                production_year=title.production_year if title else None,
                sender_name=sender_name,
                sender_username=sender_username,
                recipient_name=recipient_name,
                recipient_username=recipient_username,
            )
        )
    return enriched


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
    response_model=List[EnrichedFriendshipResponse],
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def list_user_friendships(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Lists all friendships associated with the authenticated user, enriched
    with the caller-relative `friend_id` and a best-effort display name —
    the raw FriendshipResponse only carries requester_id/addressee_id, which
    the frontend's getFriendships() has always assumed came back resolved.
    """
    user_id = _extract_user_id(claims)
    friendships = await social_repository.list_friendships(db=db, user_id=user_id)

    resolved_friend_ids: Dict[uuid.UUID, uuid.UUID] = {}
    for f in friendships:
        fid = resolve_friend_id(f.requester_id, f.addressee_id, user_id)
        if fid is None:
            # Shouldn't happen -- list_friendships is already scoped to rows
            # where the caller is one of the two sides -- but skip rather
            # than emit a row with a nonsensical friend_id.
            logger.warning("Friendship %s doesn't include caller %s on either side", f.friendship_id, user_id)
            continue
        resolved_friend_ids[f.friendship_id] = fid
    name_map = resolve_display_names(resolved_friend_ids.values())

    enriched: List[EnrichedFriendshipResponse] = []
    for f in friendships:
        friend_id = resolved_friend_ids.get(f.friendship_id)
        if friend_id is None:
            continue
        friend_name, friend_username = name_map[str(friend_id)]
        enriched.append(
            EnrichedFriendshipResponse(
                **f.model_dump(),
                friend_id=friend_id,
                friend_name=friend_name,
                friend_username=friend_username,
                avatar_url=None,
            )
        )
    return enriched


# =============================================================================
# Vector Taste Engine & Profile Endpoints (v2.0 Module 2)
# =============================================================================

@router.get(
    "/taste-matches",
    response_model=List[TasteMatchResponse],
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_taste_matches(
    limit: int = Query(5, ge=1, le=50, description="Max number of taste matches to return"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Returns a list of ACCEPTED friends sorted by semantic taste compatibility
    calculated via pgvector cosine distance on 384-dimensional taste vectors.
    """
    user_id = _extract_user_id(claims)
    return await social_repository.get_taste_compatibility(
        db=db,
        user_id=user_id,
        limit=limit,
    )


@router.put(
    "/taste-profile/mock-compute",
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def mock_compute_taste_profile(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Temporary utility for testing before Module 3.
    Generates a random 384-dimensional unit vector for the current user and persists it.
    """
    user_id = _extract_user_id(claims)

    # Generate 384-dimensional random vector
    raw_vector = [random.uniform(-1.0, 1.0) for _ in range(384)]
    norm = math.sqrt(sum(x * x for x in raw_vector))
    normalized_vector = [round(x / norm, 6) for x in raw_vector] if norm > 0 else raw_vector

    result = await social_repository.upsert_taste_profile(
        db=db,
        user_id=user_id,
        taste_vector=normalized_vector,
    )
    return {
        "status": "success",
        "user_id": str(user_id),
        "dimension": 384,
        "message": "Taste profile mock-computed successfully",
        "last_computed_at": result.get("last_computed_at"),
    }


@router.put(
    "/taste-profile",
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def update_taste_profile(
    body: UserTasteProfileUpdate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Updates or creates a user's 384-dimensional taste vector profile.
    """
    user_id = _extract_user_id(claims)
    result = await social_repository.upsert_taste_profile(
        db=db,
        user_id=user_id,
        taste_vector=body.taste_vector,
    )
    return {
        "status": "success",
        "user_id": str(user_id),
        "dimension": len(body.taste_vector),
        "last_computed_at": result.get("last_computed_at"),
    }


@router.post(
    "/taste-profile/compute",
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def compute_taste_profile_from_summary(
    body: TasteProfileComputeRequest,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Generates a 384-dimensional dense vector embedding from natural language preferences
    via the Ollama AI Brain (all-minilm) and persists it to the user's taste profile.
    """
    user_id = _extract_user_id(claims)

    try:
        ollama = OllamaClient()
        embedding = await ollama.generate_embedding(body.taste_summary)
    except Exception as exc:
        logger.error(f"Failed to generate embedding from Ollama: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama embedding computation failed: {str(exc)}",
        ) from exc

    result = await social_repository.upsert_taste_profile(
        db=db,
        user_id=user_id,
        taste_vector=embedding,
    )

    return {
        "status": "success",
        "user_id": str(user_id),
        "dimension": len(embedding),
        "message": "Taste profile computed and persisted successfully via Ollama AI Brain",
        "last_computed_at": result.get("last_computed_at"),
    }

