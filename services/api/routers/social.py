# CineVault OS — Social Core API Router (v2.0 Module 1 & 2)
# Implements Friendships, Peer Recommendations, and Taste Vector Compatibility (ADR-003, ADR-004)

import logging
import math
import random
from typing import Optional, List, Dict, Any
import uuid
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy import select
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
    CompatibilityResponse,
    LeaderboardResponse,
    LeaderboardEntry,
    BadgeResponse,
    UserBadgesResponse,
    InviteTokenCreateResponse,
    InvitePreviewResponse,
    ReferralResponse,
    ReferralStatsResponse,
    PickRoomCreate,
    PickRoomDetailResponse,
    PickVoteCreate,
    PickVoteResponse,
    PickRoomCloseResponse,
    RecapResponse,
    WatchClubCreate,
    WatchClubResponse,
    ClubMembershipResponse,
    ClubDetailResponse,
    ClubActivityResponse,
    ClubActivityCreate,
    ChallengeCreate,
    ChallengeResponse,
    ChallengeParticipantResponse,
    ChallengeDetailResponse,
    UserTasteProfileUpdate,
    UserTasteProfileResponse,
    TasteProfileComputeRequest,
)
from ..media_resolver import resolve_poster_url
from ..auth.dependencies import require_authenticated_user, get_optional_claims
from ..auth.jwt_validator import SecurityTokenClaims
from ..auth.user_directory import resolve_display_names
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.social import social_repository, _resolve_uuid, resolve_friend_id
from ..repositories.canonical import canonical_repository
from ..ai import embedding_service


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
    Only the recipient of the recommendation is authorized to mutate its lifecycle state.
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
    """Retrieves a single recommendation record by ID (authorized for sender or recipient only)."""
    user_id = _extract_user_id(claims)
    rec = await social_repository.get_recommendation(db=db, recommendation_id=id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with ID {id} not found.",
        )
    if rec.sender_id != user_id and rec.recipient_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this recommendation.",
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
                poster_url=resolve_poster_url(title.poster_url) if title else None,
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
    """Updates the status of a friendship relationship (e.g. ACCEPTED or BLOCKED) with strict actor authorization."""
    actor_id = _extract_user_id(claims)
    try:
        updated = await social_repository.update_friendship_status(
            db=db,
            friendship_id=id,
            status=body.status,
            trust_score=body.trust_score,
            actor_id=actor_id,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Friendship with ID {id} not found.",
            )
        return updated
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


@router.delete(
    "/friendships/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def delete_friendship(
    id: uuid.UUID = Path(..., description="Friendship UUID"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Cancels a pending request or removes an existing friendship (unfriend)."""
    actor_id = _extract_user_id(claims)
    try:
        deleted = await social_repository.delete_friendship(
            db=db,
            friendship_id=id,
            actor_id=actor_id,
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Friendship with ID {id} not found.",
            )
        return None
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


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


@router.get(
    "/friendships/{friend_id}/compatibility",
    response_model=CompatibilityResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
@router.get(
    "/compatibility/{friend_id}",
    response_model=CompatibilityResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_friend_compatibility(
    friend_id: uuid.UUID = Path(..., description="Target friend UUID"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Returns head-to-head taste compatibility between the authenticated user and an accepted friend.
    Includes pgvector cosine similarity score, taste tier, and overlapping genres/directors/favorites.
    """
    user_id = _extract_user_id(claims)

    # Verify friendship exists
    friendships = await social_repository.list_friendships(db=db, user_id=user_id)
    is_friend = any(
        f.status == FriendshipStatusEnum.ACCEPTED
        and (f.requester_id == friend_id or f.addressee_id == friend_id)
        for f in friendships
    )
    if not is_friend:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User {friend_id} is not an accepted friend of the requester.",
        )

    res = await social_repository.get_head_to_head_compatibility(
        db=db,
        user_id=user_id,
        friend_id=friend_id,
    )

    # Enrich with friend display name
    name_map = resolve_display_names([friend_id])
    friend_name, friend_username = name_map.get(str(friend_id), (None, None))
    res.friend_name = friend_name
    res.friend_username = friend_username

    return res


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_social_leaderboard(
    period: str = Query("weekly", pattern="^(weekly|monthly|all_time)$", description="Leaderboard time window"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Returns viewing activity leaderboard across the user's accepted friends for the specified period.
    """
    user_id = _extract_user_id(claims)
    leaderboard = await social_repository.get_friend_leaderboard(
        db=db,
        user_id=user_id,
        period=period,
    )

    # Enrich with display names for all circle members
    uids = [e.user_id for e in leaderboard.entries]
    name_map = resolve_display_names(uids)

    for entry in leaderboard.entries:
        name, username = name_map.get(str(entry.user_id), (None, None))
        entry.name = name
        entry.username = username

    return leaderboard


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
    via a self-hosted sentence-transformers model (all-MiniLM-L6-v2) and persists it
    to the user's taste profile.
    """
    user_id = _extract_user_id(claims)

    try:
        embedding = await embedding_service.generate_embedding(body.taste_summary)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(f"Failed to generate embedding: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding computation failed: {str(exc)}",
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
        "message": "Taste profile computed and persisted successfully",
        "last_computed_at": result.get("last_computed_at"),
    }


# ── /social/badges (Part 2 Item 2.5) ───────────────────────────────────────

@router.get(
    "/badges",
    response_model=UserBadgesResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_my_badges(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Retrieves all badge definitions with earned status and timestamp for the caller."""
    user_id = _extract_user_id(claims)
    return await social_repository.list_user_badges(db=db, user_id=user_id)


@router.get(
    "/badges/{target_user_id}",
    response_model=UserBadgesResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_user_badges(
    target_user_id: uuid.UUID = Path(..., description="Target user ID to inspect earned badges"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Retrieves all badge definitions with earned status and timestamp for a target user."""
    return await social_repository.list_user_badges(db=db, user_id=target_user_id)


@router.post(
    "/badges/evaluate",
    response_model=UserBadgesResponse,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def evaluate_badges(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Evaluates criteria for unearned badges and automatically grants unlocked badges."""
    user_id = _extract_user_id(claims)
    return await social_repository.evaluate_user_badges(db=db, user_id=user_id)


# ── /social/invites & /social/referrals (Part 2 Phase 2 Items 2.6 & 2.7) ───

@router.post(
    "/invites",
    response_model=InviteTokenCreateResponse,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def create_invite(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Generates a shareable viral invite token with a baked snapshot of the inviter's taste profile."""
    user_id = _extract_user_id(claims)
    res = await social_repository.create_invite_token(db=db, inviter_id=user_id)
    user_map = resolve_display_names([user_id])
    name, username = user_map.get(str(user_id), (None, None))
    res.inviter_name = name
    res.inviter_username = username
    return res


@router.get(
    "/invites/{token}/preview",
    response_model=InvitePreviewResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_invite_preview(
    token: str = Path(..., description="16-character shareable invite token"),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Public unauthenticated endpoint to preview an inviter's taste snapshot."""
    res = await social_repository.get_invite_preview(db=db, token=token)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invite token '{token}' does not exist.",
        )
    user_map = resolve_display_names([res.inviter_id])
    name, username = user_map.get(str(res.inviter_id), (None, None))
    res.inviter_name = name
    res.inviter_username = username
    return res


@router.post(
    "/invites/{token}/accept",
    response_model=FriendshipResponse,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def accept_invite(
    token: str = Path(..., description="Invite token to accept"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Accepts an invite token, auto-connects an ACCEPTED friendship, and logs referral milestone."""
    user_id = _extract_user_id(claims)
    try:
        _, friendship = await social_repository.accept_invite_token(
            db=db, token=token, invitee_id=user_id
        )
        return friendship
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/referrals",
    response_model=ReferralStatsResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_referral_stats(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Retrieves aggregated referral reward analytics and converted peer records."""
    user_id = _extract_user_id(claims)
    res = await social_repository.get_referral_stats(db=db, user_id=user_id)
    invitee_ids = [r.invitee_id for r in res.referrals]
    if invitee_ids:
        user_map = resolve_display_names(invitee_ids)
        for r in res.referrals:
            name, username = user_map.get(str(r.invitee_id), (None, None))
            r.invitee_name = name
            r.invitee_username = username
    return res


@router.post(
    "/pick-rooms",
    response_model=PickRoomDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def create_pick_room(
    body: PickRoomCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Creates a new shareable group-pick ballot room with nominated candidate titles."""
    host_id = _extract_user_id(claims)
    res = await social_repository.create_pick_room(
        db=db, host_id=host_id, data=body
    )
    user_map = resolve_display_names([host_id])
    name, username = user_map.get(str(host_id), (None, None))
    res.host_name = name
    res.host_username = username
    return res


@router.get(
    "/pick-rooms/{slug}",
    response_model=PickRoomDetailResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_pick_room(
    slug: str = Path(..., description="Pick room unique slug"),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Retrieves current state, nominated titles, and live vote tallies for a pick room."""
    res = await social_repository.get_pick_room_by_slug(db=db, slug=slug)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pick room not found.",
        )
    user_map = resolve_display_names([res.host_id])
    name, username = user_map.get(str(res.host_id), (None, None))
    res.host_name = name
    res.host_username = username
    return res


@router.post(
    "/pick-rooms/{slug}/vote",
    response_model=PickVoteResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def cast_pick_vote(
    slug: str = Path(..., description="Pick room unique slug"),
    body: PickVoteCreate = ...,
    optional_claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Casts an async vote on a candidate title within a pick room."""
    voter_user_id = _extract_user_id(optional_claims) if optional_claims else None

    try:
        return await social_repository.cast_pick_vote(
            db=db, slug=slug, voter_user_id=voter_user_id, data=body
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/pick-rooms/{slug}/close",
    response_model=PickRoomCloseResponse,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def close_pick_room(
    slug: str = Path(..., description="Pick room unique slug"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Host closes voting on a pick room and locks the winning title."""
    host_id = _extract_user_id(claims)
    try:
        return await social_repository.close_pick_room(
            db=db, slug=slug, host_id=host_id
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/recap",
    response_model=RecapResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_cinema_recap(
    period: str = Query("yearly", pattern="^(yearly|monthly|all_time)$"),
    year: Optional[int] = Query(None, ge=1900, le=2100),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Generates a wrapped-style cinema year-in-review / recap card."""
    user_id = _extract_user_id(claims)
    res = await social_repository.get_user_recap(
        db=db, user_id=user_id, period=period, year=year
    )
    user_map = resolve_display_names([user_id])
    name, username = user_map.get(str(user_id), (None, None))
    res.user_name = name
    res.user_username = username
    return res


# ── Phase 3: Watch Clubs (2.10) ──────────────────────────────────────────────

@router.post(
    "/clubs",
    response_model=WatchClubResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("SOCIAL_WRITE"))],
)
async def create_watch_club(
    payload: WatchClubCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Create a new watch club."""
    user_id = _extract_user_id(claims)
    club = await social_repository.create_watch_club(db=db, creator_id=user_id, payload=payload)
    name, username = resolve_display_names([user_id]).get(str(user_id), (None, None))
    club.creator_name = name
    club.creator_username = username
    return club


@router.get(
    "/clubs/{slug}",
    response_model=ClubDetailResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_watch_club(
    slug: str,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Retrieve a watch club by slug with members."""
    try:
        detail = await social_repository.get_watch_club(db=db, slug=slug)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    # Resolve creator + every member's display name in one batch -- this
    # endpoint (and list_my_clubs/create_watch_club below) never called
    # resolve_display_names at all, unlike every other social endpoint in
    # this file (recap, pick-rooms, recommendations, invites...), so every
    # club creator and member always rendered as the generic "CineVault
    # Member" / "Club Member" fallback on the frontend.
    ids_to_resolve = [detail.club.created_by] + [m.user_id for m in detail.members]
    name_map = resolve_display_names(ids_to_resolve)
    c_name, c_username = name_map.get(str(detail.club.created_by), (None, None))
    detail.club.creator_name = c_name
    detail.club.creator_username = c_username
    for m in detail.members:
        m_name, m_username = name_map.get(str(m.user_id), (None, None))
        m.user_name = m_name
        m.user_username = m_username
    return detail


@router.post(
    "/clubs/{slug}/join",
    response_model=ClubMembershipResponse,
    dependencies=[Depends(enforce_rate_limit("SOCIAL_WRITE"))],
)
async def join_watch_club(
    slug: str,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Join an existing watch club."""
    user_id = _extract_user_id(claims)
    try:
        return await social_repository.join_watch_club(db=db, slug=slug, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/clubs",
    response_model=List[WatchClubResponse],
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def list_my_clubs(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """List all watch clubs the authenticated user belongs to."""
    user_id = _extract_user_id(claims)
    clubs = await social_repository.list_user_clubs(db=db, user_id=user_id)
    if clubs:
        name_map = resolve_display_names([c.created_by for c in clubs])
        for c in clubs:
            name, username = name_map.get(str(c.created_by), (None, None))
            c.creator_name = name
            c.creator_username = username
    return clubs


# ── Phase 3: Club Activity Feed (2.12) ──────────────────────────────────────

@router.get(
    "/clubs/{slug}/feed",
    response_model=List[ClubActivityResponse],
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_club_feed(
    slug: str,
    limit: int = Query(20, ge=1, le=100),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Get the activity feed for a watch club."""
    try:
        return await social_repository.get_club_activity_feed(db=db, slug=slug, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/clubs/{slug}/activities",
    response_model=ClubActivityResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("SOCIAL_WRITE"))],
)
async def post_club_activity(
    slug: str,
    payload: ClubActivityCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Post an activity event to a club feed."""
    user_id = _extract_user_id(claims)
    if db is not None:
        from ..models.social import WatchClubModel
        stmt = select(WatchClubModel.club_id).where(WatchClubModel.slug == slug)
        club_id = (await db.execute(stmt)).scalar_one_or_none()
    else:
        from ..repositories.social import SEED_CLUBS
        rec = SEED_CLUBS.get(slug)
        club_id = rec["club_id"] if rec else None

    if not club_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch club not found.")

    return await social_repository.post_club_activity(
        db=db,
        club_id=club_id,
        user_id=user_id,
        activity_type=payload.activity_type,
        reference_id=payload.reference_id,
        metadata=payload.metadata,
    )


# ── Phase 3: Monthly Challenges (2.13) ──────────────────────────────────────

@router.post(
    "/challenges",
    response_model=ChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("SOCIAL_WRITE"))],
)
async def create_challenge(
    payload: ChallengeCreate,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Create a new viewing challenge (global or club-scoped)."""
    return await social_repository.create_challenge(db=db, payload=payload)


@router.get(
    "/challenges",
    response_model=List[ChallengeResponse],
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def list_active_challenges(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """List all currently active challenges."""
    user_id = _extract_user_id(claims)
    return await social_repository.list_active_challenges(db=db, user_id=user_id)


@router.get(
    "/challenges/{challenge_id}",
    response_model=ChallengeDetailResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_challenge_detail(
    challenge_id: uuid.UUID,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Get challenge details with participant list."""
    try:
        return await social_repository.get_challenge_detail(db=db, challenge_id=challenge_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/challenges/{challenge_id}/join",
    response_model=ChallengeParticipantResponse,
    dependencies=[Depends(enforce_rate_limit("SOCIAL_WRITE"))],
)
async def join_challenge(
    challenge_id: uuid.UUID,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Join a challenge as a participant."""
    user_id = _extract_user_id(claims)
    try:
        return await social_repository.join_challenge(db=db, challenge_id=challenge_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/challenges/{challenge_id}/progress",
    response_model=ChallengeParticipantResponse,
    dependencies=[Depends(enforce_rate_limit("SOCIAL_WRITE"))],
)
async def update_challenge_progress(
    challenge_id: uuid.UUID,
    increment: int = Query(1, ge=1),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """Increment challenge progress for the authenticated user."""
    user_id = _extract_user_id(claims)
    try:
        return await social_repository.update_challenge_progress(
            db=db, challenge_id=challenge_id, user_id=user_id, increment=increment
        )
    except ValueError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc







