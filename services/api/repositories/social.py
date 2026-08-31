# CineVault OS — Social Core Repository (v2.0 Module 1 & 2)
# Data access layer supporting PostgreSQL AsyncPG session, pgvector similarity, and in-memory test fallback

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple, Any
import uuid
from sqlalchemy import select, and_, or_, update, func
import secrets
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.social import (
    FriendshipModel, RecommendationModel, UserTasteProfileModel,
    BadgeDefinitionModel, UserBadgeModel,
    InviteTokenModel, ReferralModel,
    PickRoomModel, PickRoomCandidateModel, PickVoteModel,
)
from ..schemas.social import (
    FriendshipStatusEnum,
    FriendshipResponse,
    FriendshipCreate,
    RecommendationStatusEnum,
    RecommendationCreate,
    RecommendationStateUpdate,
    RecommendationResponse,
    TasteMatchResponse,
    CompatibilityResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    BadgeResponse,
    UserBadgesResponse,
    InviteTokenCreateResponse,
    InvitePreviewResponse,
    ReferralResponse,
    ReferralStatsResponse,
    PickRoomCreate,
    CandidateSummary,
    PickRoomDetailResponse,
    PickVoteCreate,
    PickVoteResponse,
    PickRoomCloseResponse,
    RecapGenreStat,
    RecapDirectorStat,
    RecapResponse,
    WatchClubCreate,
    WatchClubResponse,
    ClubMembershipResponse,
    ClubDetailResponse,
    ClubActivityResponse,
    ChallengeCreate,
    ChallengeResponse,
    ChallengeParticipantResponse,
    ChallengeDetailResponse,
    UserTasteProfileUpdate,
    UserTasteProfileResponse,
    ALLOWED_STATE_TRANSITIONS,
)
from ..media_resolver import resolve_poster_url, resolve_backdrop_url

logger = logging.getLogger("cinevault.repositories.social")

# In-memory stores used during tests or offline fallback when db session is None
SEED_FRIENDSHIPS: Dict[uuid.UUID, FriendshipResponse] = {}
SEED_RECOMMENDATIONS: Dict[uuid.UUID, RecommendationResponse] = {}
SEED_TASTE_PROFILES: Dict[uuid.UUID, Dict[str, Any]] = {}
SEED_INVITES: Dict[str, Dict[str, Any]] = {}
SEED_REFERRALS: List[Dict[str, Any]] = []
SEED_PICK_ROOMS: Dict[str, Dict[str, Any]] = {}
SEED_PICK_VOTES: List[Dict[str, Any]] = []
SEED_CLUBS: Dict[str, Dict[str, Any]] = {}
SEED_CLUB_MEMBERSHIPS: List[Dict[str, Any]] = []
SEED_CLUB_ACTIVITIES: List[Dict[str, Any]] = []
SEED_CHALLENGES: Dict[uuid.UUID, Dict[str, Any]] = {}
SEED_CHALLENGE_PARTICIPANTS: List[Dict[str, Any]] = []
SEED_BADGES = [
    {
        "badge_id": uuid.UUID("018f3a00-0000-7000-8000-000000000001"),
        "slug": "first-watch",
        "name": "First Reel",
        "description": "Log your first film or episode watch event",
        "criteria_json": {"type": "watch_count", "threshold": 1},
    },
    {
        "badge_id": uuid.UUID("018f3a00-0000-7000-8000-000000000002"),
        "slug": "century-club",
        "name": "Century Club",
        "description": "Watch and log 100 titles in CineVault",
        "criteria_json": {"type": "watch_count", "threshold": 100},
    },
    {
        "badge_id": uuid.UUID("018f3a00-0000-7000-8000-000000000003"),
        "slug": "seven-day-streak",
        "name": "Dedicated Cinephile",
        "description": "Maintain a continuous 7-day viewing streak",
        "criteria_json": {"type": "streak_days", "threshold": 7},
    },
    {
        "badge_id": uuid.UUID("018f3a00-0000-7000-8000-000000000004"),
        "slug": "inner-circle",
        "name": "Inner Circle",
        "description": "Connect with 5 accepted cinephile friends",
        "criteria_json": {"type": "friend_count", "threshold": 5},
    },
    {
        "badge_id": uuid.UUID("018f3a00-0000-7000-8000-000000000005"),
        "slug": "first-review",
        "name": "Critic in the Making",
        "description": "Publish your first film review or critique",
        "criteria_json": {"type": "review_count", "threshold": 1},
    },
    {
        "badge_id": uuid.UUID("018f3a00-0000-7000-8000-000000000006"),
        "slug": "curator-elite",
        "name": "Curator Elite",
        "description": "Create your first custom film collection",
        "criteria_json": {"type": "collection_count", "threshold": 1},
    },
]



def _resolve_uuid(val: Any, field_name: str = "id") -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"cinevault:{field_name}:{val}")


def resolve_friend_id(requester_id: uuid.UUID, addressee_id: uuid.UUID, caller_id: uuid.UUID) -> Optional[uuid.UUID]:
    """
    Given a friendship's two sides and the caller's own id, returns the
    *other* party -- the caller's friend. Returns None if the caller isn't
    actually one of the two sides (shouldn't happen for rows a correctly
    scoped query returned, but avoids silently returning the wrong id).
    """
    if requester_id == caller_id:
        return addressee_id
    if addressee_id == caller_id:
        return requester_id
    return None


def _compute_cosine_distance(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes cosine distance = 1 - cosine_similarity between two vector embeddings.
    Cosine similarity = (A . B) / (||A|| * ||B||)
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 1.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    similarity = dot_product / (norm_a * norm_b)
    # Cosine distance = 1 - similarity (bounded between 0.0 and 2.0)
    return max(0.0, min(2.0, 1.0 - similarity))


class SocialRepository:
    """Provides async database operations, pgvector cosine similarity, and state machine management."""

    # -------------------------------------------------------------------------
    # Friendship Operations
    # -------------------------------------------------------------------------

    async def are_friends_accepted(
        self, db: Optional[AsyncSession], user_a_id: uuid.UUID, user_b_id: uuid.UUID
    ) -> bool:
        """Verifies if two users possess an active ACCEPTED friendship relationship."""
        user_a = _resolve_uuid(user_a_id, "user_id")
        user_b = _resolve_uuid(user_b_id, "user_id")

        if user_a == user_b:
            return False

        if db is not None:
            stmt = select(FriendshipModel).where(
                and_(
                    FriendshipModel.status == FriendshipStatusEnum.ACCEPTED.value,
                    or_(
                        and_(
                            FriendshipModel.requester_id == user_a,
                            FriendshipModel.addressee_id == user_b,
                        ),
                        and_(
                            FriendshipModel.requester_id == user_b,
                            FriendshipModel.addressee_id == user_a,
                        ),
                    ),
                )
            )
            result = await db.execute(stmt)
            return result.scalars().first() is not None
        else:
            for f in SEED_FRIENDSHIPS.values():
                if f.status == FriendshipStatusEnum.ACCEPTED:
                    if (f.requester_id == user_a and f.addressee_id == user_b) or (
                        f.requester_id == user_b and f.addressee_id == user_a
                    ):
                        return True
            return False

    async def create_friendship(
        self,
        db: Optional[AsyncSession],
        requester_id: uuid.UUID,
        addressee_id: uuid.UUID,
        status: FriendshipStatusEnum = FriendshipStatusEnum.PENDING,
        trust_score: float = 50.0,
    ) -> FriendshipResponse:
        """Creates or initializes a friendship relation."""
        req_uuid = _resolve_uuid(requester_id, "user_id")
        add_uuid = _resolve_uuid(addressee_id, "user_id")
        if req_uuid == add_uuid:
            raise ValueError("Users cannot create a friendship with themselves.")

        now = datetime.now(timezone.utc)
        friendship_id = uuid.uuid4()

        if db is not None:
            # Check existing pairwise relation
            stmt = select(FriendshipModel).where(
                or_(
                    and_(
                        FriendshipModel.requester_id == req_uuid,
                        FriendshipModel.addressee_id == add_uuid,
                    ),
                    and_(
                        FriendshipModel.requester_id == add_uuid,
                        FriendshipModel.addressee_id == req_uuid,
                    ),
                )
            )
            res = await db.execute(stmt)
            existing = res.scalars().first()
            if existing:
                # If already ACCEPTED or BLOCKED, preserve existing relationship
                if existing.status in (FriendshipStatusEnum.ACCEPTED.value, FriendshipStatusEnum.BLOCKED.value):
                    return FriendshipResponse.model_validate(existing)
                # If already PENDING, return existing request without duplicating
                if existing.status == FriendshipStatusEnum.PENDING.value:
                    return FriendshipResponse.model_validate(existing)

                existing.status = status.value
                existing.trust_score = trust_score
                existing.updated_at = now
                await db.flush()
                return FriendshipResponse.model_validate(existing)

            record = FriendshipModel(
                friendship_id=friendship_id,
                requester_id=req_uuid,
                addressee_id=add_uuid,
                status=status.value,
                trust_score=trust_score,
                created_at=now,
                updated_at=now,
            )
            db.add(record)
            await db.flush()
            return FriendshipResponse.model_validate(record)
        else:
            # In-memory fallback
            for fid, f in list(SEED_FRIENDSHIPS.items()):
                if (f.requester_id == req_uuid and f.addressee_id == add_uuid) or (
                    f.requester_id == add_uuid and f.addressee_id == req_uuid
                ):
                    if f.status in (FriendshipStatusEnum.ACCEPTED, FriendshipStatusEnum.BLOCKED, FriendshipStatusEnum.PENDING):
                        return f

                    updated = FriendshipResponse(
                        friendship_id=f.friendship_id,
                        requester_id=f.requester_id,
                        addressee_id=f.addressee_id,
                        status=status,
                        trust_score=trust_score,
                        created_at=f.created_at,
                        updated_at=now,
                    )
                    SEED_FRIENDSHIPS[fid] = updated
                    return updated

            resp = FriendshipResponse(
                friendship_id=friendship_id,
                requester_id=req_uuid,
                addressee_id=add_uuid,
                status=status,
                trust_score=trust_score,
                created_at=now,
                updated_at=now,
            )
            SEED_FRIENDSHIPS[friendship_id] = resp
            return resp

    async def update_friendship_status(
        self,
        db: Optional[AsyncSession],
        friendship_id: uuid.UUID,
        status: FriendshipStatusEnum,
        trust_score: Optional[float] = None,
        actor_id: Optional[uuid.UUID] = None,
    ) -> Optional[FriendshipResponse]:
        """Updates status of a friendship (e.g. ACCEPTED or BLOCKED) with strict actor authorization."""
        fid_uuid = _resolve_uuid(friendship_id, "friendship_id")
        a_uuid = _resolve_uuid(actor_id, "actor_id") if actor_id else None
        now = datetime.now(timezone.utc)

        if db is not None:
            stmt = select(FriendshipModel).where(
                FriendshipModel.friendship_id == fid_uuid
            )
            res = await db.execute(stmt)
            rec = res.scalars().first()
            if not rec:
                return None

            # Authorization checks
            if a_uuid:
                if a_uuid != rec.requester_id and a_uuid != rec.addressee_id:
                    raise PermissionError("You are not a participant in this friendship.")
                if status == FriendshipStatusEnum.ACCEPTED and a_uuid != rec.addressee_id:
                    raise PermissionError("Only the recipient of a friend request can accept it.")
                if status == FriendshipStatusEnum.BLOCKED and a_uuid not in (rec.requester_id, rec.addressee_id):
                    raise PermissionError("Only participants can block a friendship.")

            if rec.status == FriendshipStatusEnum.ACCEPTED.value and status == FriendshipStatusEnum.PENDING:
                raise ValueError("Cannot transition an accepted friendship back to pending.")

            rec.status = status.value
            if trust_score is not None:
                rec.trust_score = trust_score
            rec.updated_at = now
            await db.flush()
            return FriendshipResponse.model_validate(rec)
        else:
            if fid_uuid not in SEED_FRIENDSHIPS:
                return None
            curr = SEED_FRIENDSHIPS[fid_uuid]

            if a_uuid:
                if a_uuid != curr.requester_id and a_uuid != curr.addressee_id:
                    raise PermissionError("You are not a participant in this friendship.")
                if status == FriendshipStatusEnum.ACCEPTED and a_uuid != curr.addressee_id:
                    raise PermissionError("Only the recipient of a friend request can accept it.")

            if curr.status == FriendshipStatusEnum.ACCEPTED and status == FriendshipStatusEnum.PENDING:
                raise ValueError("Cannot transition an accepted friendship back to pending.")

            updated = FriendshipResponse(
                friendship_id=curr.friendship_id,
                requester_id=curr.requester_id,
                addressee_id=curr.addressee_id,
                status=status,
                trust_score=trust_score if trust_score is not None else curr.trust_score,
                created_at=curr.created_at,
                updated_at=now,
            )
            SEED_FRIENDSHIPS[fid_uuid] = updated
            return updated

    async def delete_friendship(
        self,
        db: Optional[AsyncSession],
        friendship_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Deletes / cancels a friendship or pending request. Only participants can delete."""
        fid_uuid = _resolve_uuid(friendship_id, "friendship_id")
        a_uuid = _resolve_uuid(actor_id, "actor_id") if actor_id else None
        if db is not None:
            stmt = select(FriendshipModel).where(FriendshipModel.friendship_id == fid_uuid)
            res = await db.execute(stmt)
            rec = res.scalars().first()
            if not rec:
                return False
            if a_uuid and a_uuid != rec.requester_id and a_uuid != rec.addressee_id:
                raise PermissionError("You are not a participant in this friendship.")
            await db.delete(rec)
            await db.flush()
            return True
        else:
            if fid_uuid not in SEED_FRIENDSHIPS:
                return False
            curr = SEED_FRIENDSHIPS[fid_uuid]
            if a_uuid and a_uuid != curr.requester_id and a_uuid != curr.addressee_id:
                raise PermissionError("You are not a participant in this friendship.")
            del SEED_FRIENDSHIPS[fid_uuid]
            return True

    async def list_friendships(
        self, db: Optional[AsyncSession], user_id: uuid.UUID
    ) -> List[FriendshipResponse]:
        """Lists all friendships associated with a user."""
        u_uuid = _resolve_uuid(user_id, "user_id")

        if db is not None:
            stmt = (
                select(FriendshipModel)
                .where(
                    or_(
                        FriendshipModel.requester_id == u_uuid,
                        FriendshipModel.addressee_id == u_uuid,
                    )
                )
                .order_by(FriendshipModel.created_at.desc())
            )
            res = await db.execute(stmt)
            return [FriendshipResponse.model_validate(r) for r in res.scalars().all()]
        else:
            return [
                f
                for f in SEED_FRIENDSHIPS.values()
                if f.requester_id == u_uuid or f.addressee_id == u_uuid
            ]

    # -------------------------------------------------------------------------
    # Recommendation Operations & State Machine
    # -------------------------------------------------------------------------

    async def create_recommendation(
        self,
        db: Optional[AsyncSession],
        sender_id: uuid.UUID,
        body: RecommendationCreate,
    ) -> RecommendationResponse:
        """
        Creates a new peer recommendation with initial status 'SENT'.
        Precondition: sender and recipient MUST be ACCEPTED friends.
        """
        sender_uuid = _resolve_uuid(sender_id, "user_id")
        recipient_uuid = _resolve_uuid(body.recipient_id, "user_id")
        title_uuid = _resolve_uuid(body.title_id, "title_id")
        if sender_uuid == recipient_uuid:
            raise ValueError("Users cannot send recommendations to themselves.")

        now = datetime.now(timezone.utc)
        rec_id = uuid.uuid4()

        # Enforce friendship check
        are_friends = await self.are_friends_accepted(db, sender_uuid, recipient_uuid)
        if not are_friends:
            raise PermissionError(
                f"Users {sender_uuid} and {recipient_uuid} must be ACCEPTED friends to exchange recommendations."
            )

        if db is not None:
            rec = RecommendationModel(
                recommendation_id=rec_id,
                sender_id=sender_uuid,
                recipient_id=recipient_uuid,
                title_id=title_uuid,
                status=RecommendationStatusEnum.SENT.value,
                sender_predicted_rating=body.sender_predicted_rating,
                recipient_actual_rating=None,
                context_note=body.context_note,
                sent_at=now,
                updated_at=now,
            )
            db.add(rec)
            await db.flush()
            return RecommendationResponse.model_validate(rec)
        else:
            resp = RecommendationResponse(
                recommendation_id=rec_id,
                sender_id=sender_uuid,
                recipient_id=recipient_uuid,
                title_id=title_uuid,
                status=RecommendationStatusEnum.SENT,
                sender_predicted_rating=body.sender_predicted_rating,
                recipient_actual_rating=None,
                context_note=body.context_note,
                sent_at=now,
                updated_at=now,
            )
            SEED_RECOMMENDATIONS[rec_id] = resp
            return resp

    async def get_recommendation(
        self, db: Optional[AsyncSession], recommendation_id: uuid.UUID
    ) -> Optional[RecommendationResponse]:
        """Retrieves a recommendation by ID."""
        rec_uuid = _resolve_uuid(recommendation_id, "recommendation_id")

        if db is not None:
            stmt = select(RecommendationModel).where(
                RecommendationModel.recommendation_id == rec_uuid
            )
            res = await db.execute(stmt)
            rec = res.scalars().first()
            if rec:
                return RecommendationResponse.model_validate(rec)
            return None
        else:
            return SEED_RECOMMENDATIONS.get(rec_uuid)

    async def update_recommendation_state(
        self,
        db: Optional[AsyncSession],
        recommendation_id: uuid.UUID,
        body: RecommendationStateUpdate,
        actor_id: Optional[uuid.UUID] = None,
    ) -> RecommendationResponse:
        """
        Executes a strict state transition for a recommendation.
        State machine:
          SENT -> ACCEPTED / REJECTED
          ACCEPTED -> WATCHED
          WATCHED -> RATED (requires recipient_actual_rating)
        """
        rec_uuid = _resolve_uuid(recommendation_id, "recommendation_id")
        a_uuid = _resolve_uuid(actor_id, "actor_id") if actor_id else None
        now = datetime.now(timezone.utc)

        if db is not None:
            stmt = select(RecommendationModel).where(
                RecommendationModel.recommendation_id == rec_uuid
            )
            res = await db.execute(stmt)
            rec = res.scalars().first()
            if not rec:
                raise KeyError(f"Recommendation with ID {recommendation_id} not found.")

            # Recipient-only mutation authorization
            if a_uuid and rec.recipient_id != a_uuid:
                raise PermissionError("Only the recipient of a recommendation can update its lifecycle state.")

            current_status = RecommendationStatusEnum(rec.status)
            target_status = body.status

            allowed = ALLOWED_STATE_TRANSITIONS.get(current_status, [])
            if target_status not in allowed:
                raise ValueError(
                    f"Invalid state transition from '{current_status.value}' to '{target_status.value}'. "
                    f"Allowed transitions from '{current_status.value}': {[s.value for s in allowed]}."
                )

            if target_status == RecommendationStatusEnum.RATED:
                if body.recipient_actual_rating is None:
                    raise ValueError(
                        "recipient_actual_rating is required when transitioning status to 'RATED'."
                    )
                rec.recipient_actual_rating = body.recipient_actual_rating

            rec.status = target_status.value
            rec.updated_at = now
            await db.flush()
            return RecommendationResponse.model_validate(rec)
        else:
            if rec_uuid not in SEED_RECOMMENDATIONS:
                raise KeyError(f"Recommendation with ID {recommendation_id} not found.")

            curr = SEED_RECOMMENDATIONS[rec_uuid]
            if a_uuid and curr.recipient_id != a_uuid:
                raise PermissionError("Only the recipient of a recommendation can update its lifecycle state.")

            current_status = curr.status
            target_status = body.status

            allowed = ALLOWED_STATE_TRANSITIONS.get(current_status, [])
            if target_status not in allowed:
                raise ValueError(
                    f"Invalid state transition from '{current_status.value}' to '{target_status.value}'. "
                    f"Allowed transitions from '{current_status.value}': {[s.value for s in allowed]}."
                )

            if target_status == RecommendationStatusEnum.RATED:
                if body.recipient_actual_rating is None:
                    raise ValueError(
                        "recipient_actual_rating is required when transitioning status to 'RATED'."
                    )
                actual_rating = body.recipient_actual_rating
            else:
                actual_rating = curr.recipient_actual_rating

            updated = RecommendationResponse(
                recommendation_id=curr.recommendation_id,
                sender_id=curr.sender_id,
                recipient_id=curr.recipient_id,
                title_id=curr.title_id,
                status=target_status,
                sender_predicted_rating=curr.sender_predicted_rating,
                recipient_actual_rating=actual_rating,
                context_note=curr.context_note,
                sent_at=curr.sent_at,
                updated_at=now,
            )
            SEED_RECOMMENDATIONS[rec_uuid] = updated
            return updated

    async def list_recommendations(
        self,
        db: Optional[AsyncSession],
        user_id: uuid.UUID,
        role: str = "all",  # "sent", "received", or "all"
    ) -> List[RecommendationResponse]:
        """Lists recommendations for a given user filtered by role."""
        u_uuid = _resolve_uuid(user_id, "user_id")

        if db is not None:
            if role == "sent":
                filter_cond = RecommendationModel.sender_id == u_uuid
            elif role == "received":
                filter_cond = RecommendationModel.recipient_id == u_uuid
            else:
                filter_cond = or_(
                    RecommendationModel.sender_id == u_uuid,
                    RecommendationModel.recipient_id == u_uuid,
                )

            stmt = (
                select(RecommendationModel)
                .where(filter_cond)
                .order_by(RecommendationModel.sent_at.desc())
            )
            res = await db.execute(stmt)
            return [RecommendationResponse.model_validate(r) for r in res.scalars().all()]
        else:
            results = []
            for r in SEED_RECOMMENDATIONS.values():
                if role == "sent" and r.sender_id == u_uuid:
                    results.append(r)
                elif role == "received" and r.recipient_id == u_uuid:
                    results.append(r)
                elif role == "all" and (r.sender_id == u_uuid or r.recipient_id == u_uuid):
                    results.append(r)
            return sorted(results, key=lambda x: x.sent_at, reverse=True)

    # -------------------------------------------------------------------------
    # Taste Profile & Vector Operations (v2.0 Module 2)
    # -------------------------------------------------------------------------

    async def upsert_taste_profile(
        self,
        db_or_user_id: Any = None,
        user_id_or_vector: Any = None,
        taste_vector: Optional[List[float]] = None,
        db: Optional[AsyncSession] = None,
        user_id: Optional[uuid.UUID] = None,
        vector_data: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Creates or updates a user's 384-dimensional taste vector profile.
        Supports both (db, user_id, taste_vector) and (user_id, vector_data) calling conventions.
        """
        session: Optional[AsyncSession] = db
        target_user_id: Optional[Any] = user_id
        target_vector: Optional[List[float]] = vector_data or taste_vector

        if isinstance(db_or_user_id, AsyncSession) or (db_or_user_id is None and user_id_or_vector is not None and taste_vector is not None):
            session = db_or_user_id
            target_user_id = user_id_or_vector
            target_vector = taste_vector
        elif isinstance(db_or_user_id, (uuid.UUID, str)):
            target_user_id = db_or_user_id
            if user_id_or_vector is not None and isinstance(user_id_or_vector, (list, tuple)):
                target_vector = list(user_id_or_vector)
        elif db_or_user_id is not None and target_user_id is None:
            target_user_id = db_or_user_id

        if target_user_id is None:
            raise ValueError("user_id is required to upsert taste profile.")
        if target_vector is None:
            raise ValueError("taste_vector is required to upsert taste profile.")

        u_uuid = _resolve_uuid(target_user_id, "user_id")
        now = datetime.now(timezone.utc)

        if session is not None:
            stmt = select(UserTasteProfileModel).where(UserTasteProfileModel.user_id == u_uuid)
            res = await session.execute(stmt)
            existing = res.scalars().first()
            if existing:
                existing.taste_vector = target_vector
                existing.last_computed_at = now
                await session.flush()
                return {
                    "user_id": existing.user_id,
                    "taste_vector": list(existing.taste_vector) if existing.taste_vector is not None else None,
                    "last_computed_at": existing.last_computed_at,
                    "dimension": len(target_vector),
                }
            else:
                record = UserTasteProfileModel(
                    user_id=u_uuid,
                    taste_vector=target_vector,
                    last_computed_at=now,
                )
                session.add(record)
                await session.flush()
                return {
                    "user_id": record.user_id,
                    "taste_vector": list(record.taste_vector) if record.taste_vector is not None else None,
                    "last_computed_at": record.last_computed_at,
                    "dimension": len(target_vector),
                }
        else:
            profile_data = {
                "user_id": u_uuid,
                "taste_vector": list(target_vector),
                "last_computed_at": now,
                "dimension": len(target_vector),
            }
            SEED_TASTE_PROFILES[u_uuid] = profile_data
            return profile_data

    async def get_taste_profile(
        self,
        db: Optional[AsyncSession],
        user_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """Retrieves a user's taste profile including taste_vector and metadata."""
        u_uuid = _resolve_uuid(user_id, "user_id")

        if db is not None:
            stmt = select(UserTasteProfileModel).where(UserTasteProfileModel.user_id == u_uuid)
            res = await db.execute(stmt)
            profile = res.scalars().first()
            if profile and profile.taste_vector is not None:
                return {
                    "user_id": profile.user_id,
                    "taste_vector": list(profile.taste_vector),
                    "last_computed_at": profile.last_computed_at,
                    "dimension": len(profile.taste_vector),
                }
            return None
        else:
            return SEED_TASTE_PROFILES.get(u_uuid)


    async def get_taste_compatibility(
        self,
        db_or_user_id: Any = None,
        user_id_or_limit: Any = None,
        limit: int = 5,
        db: Optional[AsyncSession] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[TasteMatchResponse]:
        """
        Calculates cosine similarity / distance between user_id and all ACCEPTED friends.
        Orders results by highest taste compatibility (lowest cosine distance).
        Formula: compatibility_score = (1 - cosine_distance) * 100
        """
        session: Optional[AsyncSession] = db
        target_user_id: Optional[Any] = user_id
        target_limit: int = limit

        if isinstance(db_or_user_id, AsyncSession) or (db_or_user_id is None and user_id_or_limit is not None and not isinstance(user_id_or_limit, int)):
            session = db_or_user_id
            target_user_id = user_id_or_limit
            target_limit = limit
        elif isinstance(db_or_user_id, (uuid.UUID, str)):
            target_user_id = db_or_user_id
            if isinstance(user_id_or_limit, int):
                target_limit = user_id_or_limit
        elif db_or_user_id is not None and target_user_id is None:
            target_user_id = db_or_user_id

        if target_user_id is None:
            return []

        u_uuid = _resolve_uuid(target_user_id, "user_id")

        if session is not None:
            # 1. Fetch user's taste profile
            stmt_user = select(UserTasteProfileModel).where(UserTasteProfileModel.user_id == u_uuid)
            res_user = await session.execute(stmt_user)
            user_profile = res_user.scalars().first()
            if not user_profile or user_profile.taste_vector is None:
                return []

            target_vector = user_profile.taste_vector

            # 2. Query all ACCEPTED friendships
            stmt_friends = select(FriendshipModel).where(
                and_(
                    FriendshipModel.status == FriendshipStatusEnum.ACCEPTED.value,
                    or_(
                        FriendshipModel.requester_id == u_uuid,
                        FriendshipModel.addressee_id == u_uuid,
                    ),
                )
            )
            res_friends = await session.execute(stmt_friends)
            friend_records = res_friends.scalars().all()

            friend_ids: List[uuid.UUID] = [
                fid for fid in (
                    resolve_friend_id(f.requester_id, f.addressee_id, u_uuid) for f in friend_records
                ) if fid is not None
            ]

            if not friend_ids:
                return []

            # 3. Query pgvector cosine distance: UserTasteProfileModel.taste_vector.cosine_distance(target_vector)
            dist_expr = UserTasteProfileModel.taste_vector.cosine_distance(target_vector)
            stmt_matches = (
                select(
                    UserTasteProfileModel.user_id,
                    dist_expr.label("distance"),
                )
                .where(
                    and_(
                        UserTasteProfileModel.user_id.in_(friend_ids),
                        UserTasteProfileModel.taste_vector.is_not(None),
                    )
                )
                .order_by(dist_expr.asc())
                .limit(target_limit)
            )
            res_matches = await session.execute(stmt_matches)
            results: List[TasteMatchResponse] = []
            for f_id, dist in res_matches.all():
                d_val = float(dist) if dist is not None else 1.0
                score = max(0.0, min(100.0, round((1.0 - d_val) * 100.0, 2)))
                results.append(
                    TasteMatchResponse(
                        friend_id=f_id,
                        compatibility_score=score,
                    )
                )
            return results
        else:
            # In-memory fallback
            if u_uuid not in SEED_TASTE_PROFILES or not SEED_TASTE_PROFILES[u_uuid].get("taste_vector"):
                return []

            target_vector = SEED_TASTE_PROFILES[u_uuid]["taste_vector"]

            # Find accepted friends
            friend_ids: List[uuid.UUID] = [
                fid for fid in (
                    resolve_friend_id(f.requester_id, f.addressee_id, u_uuid)
                    for f in SEED_FRIENDSHIPS.values()
                    if f.status == FriendshipStatusEnum.ACCEPTED
                ) if fid is not None
            ]

            if not friend_ids:
                return []

            matches = []
            for f_id in friend_ids:
                if f_id in SEED_TASTE_PROFILES and SEED_TASTE_PROFILES[f_id].get("taste_vector"):
                    f_vector = SEED_TASTE_PROFILES[f_id]["taste_vector"]
                    cos_dist = _compute_cosine_distance(target_vector, f_vector)
                    score = max(0.0, min(100.0, round((1.0 - cos_dist) * 100.0, 2)))
                    matches.append((f_id, cos_dist, score))

            matches.sort(key=lambda x: x[1])

            return [
                TasteMatchResponse(friend_id=item[0], compatibility_score=item[2])
                for item in matches[:target_limit]
            ]

    async def get_head_to_head_compatibility(
        self,
        db: Optional[AsyncSession],
        user_id: uuid.UUID,
        friend_id: uuid.UUID,
    ) -> CompatibilityResponse:
        """
        Computes detailed head-to-head compatibility metrics between user_id and friend_id.
        Includes pgvector cosine similarity score, taste tier, overlapping genres,
        shared directors, and mutually loved/watched titles.
        """
        u_uuid = _resolve_uuid(user_id, "user_id")
        f_uuid = _resolve_uuid(friend_id, "friend_id")

        now = datetime.now(timezone.utc)
        score = 0.0
        shared_genres: List[str] = []
        shared_directors: List[str] = []
        shared_favorite_titles: List[str] = []

        if db is not None:
            # 1. Cosine similarity via taste vectors
            stmt_vec = select(UserTasteProfileModel).where(
                UserTasteProfileModel.user_id.in_([u_uuid, f_uuid])
            )
            res_vec = await db.execute(stmt_vec)
            profiles = {p.user_id: p for p in res_vec.scalars().all()}
            u_prof = profiles.get(u_uuid)
            f_prof = profiles.get(f_uuid)

            if u_prof and f_prof and u_prof.taste_vector is not None and f_prof.taste_vector is not None:
                dist_expr = UserTasteProfileModel.taste_vector.cosine_distance(u_prof.taste_vector)
                stmt_dist = (
                    select(dist_expr)
                    .where(UserTasteProfileModel.user_id == f_uuid)
                )
                res_dist = await db.execute(stmt_dist)
                dist_val = res_dist.scalar_one_or_none()
                if dist_val is not None:
                    score = max(0.0, min(100.0, round((1.0 - float(dist_val)) * 100.0, 1)))

            # 2. Extract watched & favorite title IDs for both users
            from ..models.personal import WatchEventModel, UserTitleStateModel
            from ..models.canonical import TitleModel, TitleGenreModel, GenreModel, CreditModel, PersonModel

            stmt_u_titles = select(WatchEventModel.title_id).where(
                and_(WatchEventModel.user_id == u_uuid, WatchEventModel.is_tombstoned == False)
            )
            res_u_titles = await db.execute(stmt_u_titles)
            u_title_ids = set(res_u_titles.scalars().all())

            stmt_f_titles = select(WatchEventModel.title_id).where(
                and_(WatchEventModel.user_id == f_uuid, WatchEventModel.is_tombstoned == False)
            )
            res_f_titles = await db.execute(stmt_f_titles)
            f_title_ids = set(res_f_titles.scalars().all())

            # Shared watched titles
            common_title_ids = list(u_title_ids.intersection(f_title_ids))

            # Shared favorites / high ratings (rating >= 8 or is_favorite)
            stmt_u_favs = select(UserTitleStateModel.title_id).where(
                and_(UserTitleStateModel.user_id == u_uuid, UserTitleStateModel.is_favorite == True)
            )
            res_u_favs = await db.execute(stmt_u_favs)
            u_fav_ids = set(res_u_favs.scalars().all())

            stmt_f_favs = select(UserTitleStateModel.title_id).where(
                and_(UserTitleStateModel.user_id == f_uuid, UserTitleStateModel.is_favorite == True)
            )
            res_f_favs = await db.execute(stmt_f_favs)
            f_fav_ids = set(res_f_favs.scalars().all())

            common_fav_ids = list(u_fav_ids.intersection(f_fav_ids))
            if not common_fav_ids and common_title_ids:
                common_fav_ids = common_title_ids[:5]

            if common_fav_ids:
                stmt_fav_names = select(TitleModel.canonical_title).where(
                    TitleModel.title_id.in_(common_fav_ids[:5])
                )
                res_fav_names = await db.execute(stmt_fav_names)
                shared_favorite_titles = [name for name in res_fav_names.scalars().all() if name]

            # 3. Intersecting top genres
            if u_title_ids and f_title_ids:
                stmt_u_genres = (
                    select(GenreModel.name, func.count(TitleGenreModel.title_id).label("cnt"))
                    .join(TitleGenreModel, GenreModel.genre_id == TitleGenreModel.genre_id)
                    .where(TitleGenreModel.title_id.in_(u_title_ids))
                    .group_by(GenreModel.name)
                    .order_by(func.count(TitleGenreModel.title_id).desc())
                )
                res_u_genres = await db.execute(stmt_u_genres)
                u_genres = {row[0]: row[1] for row in res_u_genres.all()}

                stmt_f_genres = (
                    select(GenreModel.name, func.count(TitleGenreModel.title_id).label("cnt"))
                    .join(TitleGenreModel, GenreModel.genre_id == TitleGenreModel.genre_id)
                    .where(TitleGenreModel.title_id.in_(f_title_ids))
                    .group_by(GenreModel.name)
                    .order_by(func.count(TitleGenreModel.title_id).desc())
                )
                res_f_genres = await db.execute(stmt_f_genres)
                f_genres = {row[0]: row[1] for row in res_f_genres.all()}

                overlap_genres = sorted(
                    set(u_genres.keys()).intersection(set(f_genres.keys())),
                    key=lambda g: u_genres[g] + f_genres[g],
                    reverse=True
                )
                shared_genres = overlap_genres[:5]

            # 4. Intersecting top directors
            if u_title_ids and f_title_ids:
                stmt_dirs = (
                    select(PersonModel.canonical_name)
                    .join(CreditModel, PersonModel.person_id == CreditModel.person_id)
                    .where(
                        and_(
                            CreditModel.title_id.in_(u_title_ids),
                            CreditModel.credit_role_id == "DIRECTOR"
                        )
                    )
                )
                res_u_dirs = await db.execute(stmt_dirs)
                u_dirs = set(res_u_dirs.scalars().all())

                stmt_f_dirs = (
                    select(PersonModel.canonical_name)
                    .join(CreditModel, PersonModel.person_id == CreditModel.person_id)
                    .where(
                        and_(
                            CreditModel.title_id.in_(f_title_ids),
                            CreditModel.credit_role_id == "DIRECTOR"
                        )
                    )
                )
                res_f_dirs = await db.execute(stmt_f_dirs)
                f_dirs = set(res_f_dirs.scalars().all())

                shared_directors = list(u_dirs.intersection(f_dirs))[:5]

        else:
            # In-memory test fallback
            if (
                u_uuid in SEED_TASTE_PROFILES
                and f_uuid in SEED_TASTE_PROFILES
                and SEED_TASTE_PROFILES[u_uuid].get("taste_vector")
                and SEED_TASTE_PROFILES[f_uuid].get("taste_vector")
            ):
                cos_dist = _compute_cosine_distance(
                    SEED_TASTE_PROFILES[u_uuid]["taste_vector"],
                    SEED_TASTE_PROFILES[f_uuid]["taste_vector"]
                )
                score = max(0.0, min(100.0, round((1.0 - cos_dist) * 100.0, 1)))

        # Tier calculation
        if score >= 75.0:
            taste_tier = "Oracle"
        elif score >= 50.0:
            taste_tier = "Critic"
        elif score >= 25.0:
            taste_tier = "Regular"
        else:
            taste_tier = "Curious"

        return CompatibilityResponse(
            user_id=u_uuid,
            friend_id=f_uuid,
            compatibility_score=score,
            taste_tier=taste_tier,
            shared_genres=shared_genres,
            shared_directors=shared_directors,
            shared_favorite_titles=shared_favorite_titles,
            calculated_at=now,
        )

    async def get_friend_leaderboard(
        self,
        db: Optional[AsyncSession],
        user_id: uuid.UUID,
        period: str = "weekly",
    ) -> LeaderboardResponse:
        """
        Computes viewing activity leaderboard across the user's accepted friendships.
        Aggregates watch_event counts and viewing duration in hours for the specified period.
        """
        u_uuid = _resolve_uuid(user_id, "user_id")
        now = datetime.now(timezone.utc)

        if period == "weekly":
            start_dt = now - timedelta(days=7)
        elif period == "monthly":
            start_dt = now - timedelta(days=30)
        else:
            start_dt = None

        if db is not None:
            # 1. Discover all accepted friends
            stmt_friends = select(FriendshipModel).where(
                and_(
                    FriendshipModel.status == FriendshipStatusEnum.ACCEPTED.value,
                    or_(
                        FriendshipModel.requester_id == u_uuid,
                        FriendshipModel.addressee_id == u_uuid,
                    ),
                )
            )
            res_friends = await db.execute(stmt_friends)
            friend_records = res_friends.scalars().all()

            circle_user_ids: List[uuid.UUID] = [u_uuid]
            for f in friend_records:
                fid = resolve_friend_id(f.requester_id, f.addressee_id, u_uuid)
                if fid is not None and fid not in circle_user_ids:
                    circle_user_ids.append(fid)

            # 2. Query watch events for all circle users
            from ..models.personal import WatchEventModel
            from ..models.canonical import EditionModel

            filter_conds = [
                WatchEventModel.user_id.in_(circle_user_ids),
                WatchEventModel.is_tombstoned == False,  # noqa: E712
            ]
            if start_dt is not None:
                filter_conds.append(WatchEventModel.watched_at >= start_dt)

            stmt_events = (
                select(
                    WatchEventModel.user_id,
                    func.count(WatchEventModel.watch_event_id).label("event_count"),
                    func.coalesce(func.sum(EditionModel.runtime_minutes), func.count(WatchEventModel.watch_event_id) * 120).label("total_mins"),
                )
                .outerjoin(EditionModel, WatchEventModel.edition_id == EditionModel.edition_id)
                .where(and_(*filter_conds))
                .group_by(WatchEventModel.user_id)
            )
            res_events = await db.execute(stmt_events)
            metrics_by_user = {row[0]: (int(row[1]), round(float(row[2]) / 60.0, 1)) for row in res_events.all()}

            # 3. Assemble leaderboard list with 0-filled users
            raw_entries = []
            for uid in circle_user_ids:
                count, hours = metrics_by_user.get(uid, (0, 0.0))
                raw_entries.append((uid, count, hours))

            # 4. Sort: highest count -> highest hours -> user_id
            raw_entries.sort(key=lambda x: (x[1], x[2], str(x[0])), reverse=True)

            entries: List[LeaderboardEntry] = []
            for rank_idx, (uid, count, hours) in enumerate(raw_entries, start=1):
                entries.append(
                    LeaderboardEntry(
                        user_id=uid,
                        name=None,
                        username=None,
                        watch_count=count,
                        watch_hours=hours,
                        rank=rank_idx,
                        is_current_user=(uid == u_uuid),
                    )
                )

            return LeaderboardResponse(
                period=period,
                entries=entries,
                calculated_at=now,
            )
        else:
            # In-memory test fallback
            circle_user_ids = [u_uuid]
            for f in SEED_FRIENDSHIPS.values():
                if f.status == FriendshipStatusEnum.ACCEPTED:
                    fid = resolve_friend_id(f.requester_id, f.addressee_id, u_uuid)
                    if fid and fid not in circle_user_ids:
                        circle_user_ids.append(fid)

            entries = [
                LeaderboardEntry(
                    user_id=uid,
                    name=None,
                    username=None,
                    watch_count=1 if uid == u_uuid else 0,
                    watch_hours=2.0 if uid == u_uuid else 0.0,
                    rank=idx,
                    is_current_user=(uid == u_uuid),
                )
                for idx, uid in enumerate(circle_user_ids, start=1)
            ]
            return LeaderboardResponse(
                period=period,
                entries=entries,
                calculated_at=now,
            )

    async def list_user_badges(
        self,
        db: Optional[AsyncSession],
        user_id: uuid.UUID,
    ) -> UserBadgesResponse:
        """Retrieves all badge definitions with earned status and timestamp for a user."""
        u_uuid = _resolve_uuid(user_id, "user_id")

        if db is not None:
            stmt_defs = select(BadgeDefinitionModel).order_by(BadgeDefinitionModel.created_at.asc())
            res_defs = await db.execute(stmt_defs)
            all_defs = res_defs.scalars().all()

            stmt_user = select(UserBadgeModel).where(UserBadgeModel.user_id == u_uuid)
            res_user = await db.execute(stmt_user)
            earned_map = {b.badge_id: b for b in res_user.scalars().all()}

            badges = []
            for b_def in all_defs:
                earned = earned_map.get(b_def.badge_id)
                badges.append(
                    BadgeResponse(
                        badge_id=b_def.badge_id,
                        slug=b_def.slug,
                        name=b_def.name,
                        description=b_def.description,
                        icon_url=b_def.icon_url,
                        is_earned=earned is not None,
                        earned_at=earned.earned_at if earned else None,
                        context_json=earned.context_json if earned else None,
                    )
                )

            return UserBadgesResponse(
                user_id=u_uuid,
                badges=badges,
                total_earned=len(earned_map),
            )
        else:
            # In-memory test fallback
            badges = [
                BadgeResponse(
                    badge_id=b["badge_id"],
                    slug=b["slug"],
                    name=b["name"],
                    description=b["description"],
                    icon_url=None,
                    is_earned=False,
                    earned_at=None,
                    context_json=None,
                )
                for b in SEED_BADGES
            ]
            return UserBadgesResponse(
                user_id=u_uuid,
                badges=badges,
                total_earned=0,
            )

    async def evaluate_user_badges(
        self,
        db: Optional[AsyncSession],
        user_id: uuid.UUID,
    ) -> UserBadgesResponse:
        """
        Evaluates criteria for all unearned badges and automatically grants unlocked badges.
        Evaluates watch volume, continuous streaks, friend count, reviews, and custom lists.
        """
        u_uuid = _resolve_uuid(user_id, "user_id")
        if db is None:
            return await self.list_user_badges(db, u_uuid)

        # 1. Fetch definitions and earned map
        stmt_defs = select(BadgeDefinitionModel)
        all_defs = (await db.execute(stmt_defs)).scalars().all()

        stmt_user = select(UserBadgeModel).where(UserBadgeModel.user_id == u_uuid)
        earned_ids = {b.badge_id for b in (await db.execute(stmt_user)).scalars().all()}

        unearned = [b for b in all_defs if b.badge_id not in earned_ids]
        if not unearned:
            return await self.list_user_badges(db, u_uuid)

        # 2. Gather metrics on-demand
        from ..models.personal import WatchEventModel, UserStreakModel, ReviewModel, UserListModel

        # Watch count
        stmt_wc = select(func.count(WatchEventModel.watch_event_id)).where(
            and_(
                WatchEventModel.user_id == u_uuid,
                WatchEventModel.is_tombstoned == False,  # noqa: E712
            )
        )
        watch_count = (await db.execute(stmt_wc)).scalar_one() or 0

        # Streak metrics
        stmt_streak = select(UserStreakModel).where(UserStreakModel.user_id == u_uuid)
        streak_row = (await db.execute(stmt_streak)).scalar_one_or_none()
        longest_streak = max(streak_row.longest_streak, streak_row.current_streak) if streak_row else 0

        # Friend count
        stmt_fc = select(func.count(FriendshipModel.friendship_id)).where(
            and_(
                FriendshipModel.status == FriendshipStatusEnum.ACCEPTED.value,
                or_(
                    FriendshipModel.requester_id == u_uuid,
                    FriendshipModel.addressee_id == u_uuid,
                ),
            )
        )
        friend_count = (await db.execute(stmt_fc)).scalar_one() or 0

        # Review count
        stmt_rc = select(func.count(ReviewModel.review_id)).where(ReviewModel.user_id == u_uuid)
        review_count = (await db.execute(stmt_rc)).scalar_one() or 0

        # Collection count
        stmt_cc = select(func.count(UserListModel.list_id)).where(UserListModel.user_id == u_uuid)
        collection_count = (await db.execute(stmt_cc)).scalar_one() or 0

        now = datetime.now(timezone.utc)
        newly_earned = []

        for b in unearned:
            crit = b.criteria_json or {}
            c_type = crit.get("type")
            threshold = crit.get("threshold", 1)

            qualifies = False
            context = {}

            if c_type == "watch_count" and watch_count >= threshold:
                qualifies = True
                context = {"watch_count": watch_count, "threshold": threshold}
            elif c_type == "streak_days" and longest_streak >= threshold:
                qualifies = True
                context = {"longest_streak": longest_streak, "threshold": threshold}
            elif c_type == "friend_count" and friend_count >= threshold:
                qualifies = True
                context = {"friend_count": friend_count, "threshold": threshold}
            elif c_type == "review_count" and review_count >= threshold:
                qualifies = True
                context = {"review_count": review_count, "threshold": threshold}
            elif c_type == "collection_count" and collection_count >= threshold:
                qualifies = True
                context = {"collection_count": collection_count, "threshold": threshold}

            if qualifies:
                new_badge = UserBadgeModel(
                    user_id=u_uuid,
                    badge_id=b.badge_id,
                    earned_at=now,
                    context_json=context,
                )
                db.add(new_badge)
                newly_earned.append(new_badge)

        if newly_earned:
            await db.flush()

        return await self.list_user_badges(db, u_uuid)

    async def create_invite_token(
        self,
        db: Optional[AsyncSession],
        inviter_id: uuid.UUID,
        base_url: str = "http://localhost:3000",
    ) -> InviteTokenCreateResponse:
        """Generates a shareable viral invite token with a baked taste profile snapshot."""
        u_uuid = _resolve_uuid(inviter_id, "user_id")
        token = secrets.token_urlsafe(12)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=30)

        preview_data = {
            "top_genres": ["Sci-Fi", "Drama", "Thriller"],
            "recent_watched_titles": [],
            "total_watched_count": 0,
        }

        if db is not None:
            from ..models.personal import WatchEventModel
            from ..models.canonical import TitleModel, TitleGenreModel, GenreModel

            # 1. Total watched count
            stmt_wc = select(func.count(WatchEventModel.watch_event_id)).where(
                and_(
                    WatchEventModel.user_id == u_uuid,
                    WatchEventModel.is_tombstoned == False,  # noqa: E712
                )
            )
            total_watches = (await db.execute(stmt_wc)).scalar_one() or 0

            # 2. Recent 3 titles
            stmt_recents = (
                select(TitleModel.canonical_title)
                .join(WatchEventModel, TitleModel.title_id == WatchEventModel.title_id)
                .where(
                    and_(
                        WatchEventModel.user_id == u_uuid,
                        WatchEventModel.is_tombstoned == False,  # noqa: E712
                    )
                )
                .order_by(WatchEventModel.watched_at.desc())
                .limit(3)
            )
            recent_titles = list((await db.execute(stmt_recents)).scalars().all())

            # 3. Top 3 genres
            stmt_genres = (
                select(GenreModel.name, func.count(WatchEventModel.watch_event_id))
                .join(TitleGenreModel, GenreModel.genre_id == TitleGenreModel.genre_id)
                .join(TitleModel, TitleGenreModel.title_id == TitleModel.title_id)
                .join(WatchEventModel, TitleModel.title_id == WatchEventModel.title_id)
                .where(
                    and_(
                        WatchEventModel.user_id == u_uuid,
                        WatchEventModel.is_tombstoned == False,  # noqa: E712
                    )
                )
                .group_by(GenreModel.name)
                .order_by(func.count(WatchEventModel.watch_event_id).desc())
                .limit(3)
            )
            top_genres = [r[0] for r in (await db.execute(stmt_genres)).all()]
            if not top_genres:
                top_genres = ["Cinema", "Sci-Fi", "Drama"]

            preview_data = {
                "top_genres": top_genres,
                "recent_watched_titles": recent_titles,
                "total_watched_count": total_watches,
            }

            token_orm = InviteTokenModel(
                token=token,
                inviter_id=u_uuid,
                preview_data_json=preview_data,
                expires_at=expires_at,
                created_at=now,
            )
            db.add(token_orm)
            await db.flush()
        else:
            SEED_INVITES[token] = {
                "token": token,
                "inviter_id": u_uuid,
                "preview_data": preview_data,
                "expires_at": expires_at,
                "converted_user_id": None,
                "created_at": now,
            }

        return InviteTokenCreateResponse(
            token=token,
            invite_url=f"{base_url}/invite/{token}",
            inviter_id=u_uuid,
            preview_data=preview_data,
            expires_at=expires_at,
            created_at=now,
        )

    async def get_invite_preview(
        self,
        db: Optional[AsyncSession],
        token: str,
    ) -> Optional[InvitePreviewResponse]:
        """Fetches public taste preview snapshot for an invite token."""
        if db is not None:
            stmt = select(InviteTokenModel).where(InviteTokenModel.token == token)
            token_orm = (await db.execute(stmt)).scalar_one_or_none()
            if not token_orm:
                return None

            now = datetime.now(timezone.utc)
            is_expired = token_orm.expires_at is not None and token_orm.expires_at < now
            is_converted = token_orm.converted_user_id is not None
            prev = token_orm.preview_data_json or {}

            return InvitePreviewResponse(
                token=token,
                inviter_id=token_orm.inviter_id,
                inviter_name=None,
                inviter_username=None,
                top_genres=prev.get("top_genres", []),
                recent_watched_titles=prev.get("recent_watched_titles", []),
                total_watched_count=prev.get("total_watched_count", 0),
                is_expired=is_expired,
                is_converted=is_converted,
                created_at=token_orm.created_at,
            )
        else:
            token_data = SEED_INVITES.get(token)
            if not token_data:
                return None
            prev = token_data.get("preview_data", {})
            return InvitePreviewResponse(
                token=token,
                inviter_id=token_data["inviter_id"],
                inviter_name="Cinephile Host",
                inviter_username="cinephile",
                top_genres=prev.get("top_genres", ["Sci-Fi", "Drama"]),
                recent_watched_titles=prev.get("recent_watched_titles", []),
                total_watched_count=prev.get("total_watched_count", 0),
                is_expired=False,
                is_converted=token_data.get("converted_user_id") is not None,
                created_at=token_data.get("created_at", datetime.now(timezone.utc)),
            )

    async def accept_invite_token(
        self,
        db: Optional[AsyncSession],
        token: str,
        invitee_id: uuid.UUID,
    ) -> Tuple[Any, Any]:
        """
        Consumes an invite token, connects mutual accepted friendship, and logs referral record.
        """
        i_uuid = _resolve_uuid(invitee_id, "user_id")

        if db is not None:
            stmt = select(InviteTokenModel).where(InviteTokenModel.token == token)
            token_orm = (await db.execute(stmt)).scalar_one_or_none()
            if not token_orm:
                raise ValueError("Invite token not found.")

            now = datetime.now(timezone.utc)
            if token_orm.expires_at and token_orm.expires_at < now:
                raise ValueError("Invite token has expired.")

            if token_orm.inviter_id == i_uuid:
                raise ValueError("Users cannot accept their own invite token.")

            # Mark converted
            if not token_orm.converted_user_id:
                token_orm.converted_user_id = i_uuid

            # Check if friendship already exists
            f_stmt = select(FriendshipModel).where(
                or_(
                    and_(FriendshipModel.requester_id == token_orm.inviter_id, FriendshipModel.addressee_id == i_uuid),
                    and_(FriendshipModel.requester_id == i_uuid, FriendshipModel.addressee_id == token_orm.inviter_id),
                )
            )
            friendship = (await db.execute(f_stmt)).scalar_one_or_none()
            if not friendship:
                friendship = FriendshipModel(
                    friendship_id=uuid.uuid4(),
                    requester_id=token_orm.inviter_id,
                    addressee_id=i_uuid,
                    status=FriendshipStatusEnum.ACCEPTED.value,
                    trust_score=75.0,
                    created_at=now,
                    updated_at=now,
                )
                db.add(friendship)

            # Record referral
            r_stmt = select(ReferralModel).where(
                and_(
                    ReferralModel.inviter_id == token_orm.inviter_id,
                    ReferralModel.invitee_id == i_uuid,
                )
            )
            referral = (await db.execute(r_stmt)).scalar_one_or_none()
            if not referral:
                referral = ReferralModel(
                    referral_id=uuid.uuid4(),
                    inviter_id=token_orm.inviter_id,
                    invitee_id=i_uuid,
                    status="PENDING",
                    created_at=now,
                )
                db.add(referral)

            await db.flush()
            return token_orm, friendship
        else:
            token_data = SEED_INVITES.get(token)
            if not token_data:
                raise ValueError("Invite token not found.")
            if token_data["inviter_id"] == i_uuid:
                raise ValueError("Users cannot accept their own invite token.")
            token_data["converted_user_id"] = i_uuid
            fid = uuid.uuid4()
            friendship = FriendshipResponse(
                friendship_id=fid,
                requester_id=token_data["inviter_id"],
                addressee_id=i_uuid,
                status=FriendshipStatusEnum.ACCEPTED,
                trust_score=75.0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            SEED_FRIENDSHIPS[fid] = friendship
            ref_id = uuid.uuid4()
            SEED_REFERRALS.append({
                "referral_id": ref_id,
                "inviter_id": token_data["inviter_id"],
                "invitee_id": i_uuid,
                "status": "PENDING",
                "milestone_reached_at": None,
                "reward_issued": False,
                "created_at": datetime.now(timezone.utc),
            })
            token_orm = InviteTokenModel(
                token=token,
                inviter_id=token_data["inviter_id"],
                preview_data_json=token_data.get("preview_data", {}),
                expires_at=token_data.get("expires_at"),
                converted_user_id=i_uuid,
                created_at=token_data.get("created_at", datetime.now(timezone.utc)),
            )
            return token_orm, friendship

    async def get_referral_stats(
        self,
        db: Optional[AsyncSession],
        user_id: uuid.UUID,
    ) -> ReferralStatsResponse:
        """Retrieves aggregated referral analytics and conversions list for a user."""
        u_uuid = _resolve_uuid(user_id, "user_id")

        if db is not None:
            stmt_invites = select(func.count(InviteTokenModel.token)).where(InviteTokenModel.inviter_id == u_uuid)
            total_invites = (await db.execute(stmt_invites)).scalar_one() or 0

            stmt_refs = select(ReferralModel).where(ReferralModel.inviter_id == u_uuid).order_by(ReferralModel.created_at.desc())
            refs = (await db.execute(stmt_refs)).scalars().all()

            referrals = [
                ReferralResponse(
                    referral_id=r.referral_id,
                    inviter_id=r.inviter_id,
                    invitee_id=r.invitee_id,
                    status=r.status,
                    milestone_reached_at=r.milestone_reached_at,
                    reward_issued=r.reward_issued,
                    created_at=r.created_at,
                )
                for r in refs
            ]

            total_conversions = len(referrals)
            qualified = sum(1 for r in refs if r.status in ("QUALIFIED", "REWARDED") or r.reward_issued)

            return ReferralStatsResponse(
                inviter_id=u_uuid,
                total_invites_sent=total_invites,
                total_conversions=total_conversions,
                qualified_referrals=qualified,
                referrals=referrals,
            )
        else:
            user_refs = [r for r in SEED_REFERRALS if r["inviter_id"] == u_uuid]
            referrals = [
                ReferralResponse(
                    referral_id=r["referral_id"],
                    inviter_id=r["inviter_id"],
                    invitee_id=r["invitee_id"],
                    status=r["status"],
                    milestone_reached_at=r["milestone_reached_at"],
                    reward_issued=r["reward_issued"],
                    created_at=r["created_at"],
                )
                for r in user_refs
            ]
            invites_count = sum(1 for inv in SEED_INVITES.values() if inv["inviter_id"] == u_uuid)
            return ReferralStatsResponse(
                inviter_id=u_uuid,
                total_invites_sent=invites_count,
                total_conversions=len(referrals),
                qualified_referrals=sum(1 for r in user_refs if r["status"] in ("QUALIFIED", "REWARDED") or r["reward_issued"]),
                referrals=referrals,
            )

    # ── Group Pick Room & Async Voting (Part 2 — Item 2.8) ──────────────────────────

    async def create_pick_room(
        self,
        db: Optional[AsyncSession],
        host_id: uuid.UUID,
        data: PickRoomCreate,
    ) -> PickRoomDetailResponse:
        """
        Creates a new shareable group-pick ballot room with nominated candidate titles.
        """
        h_uuid = _resolve_uuid(host_id, "host_id")
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=data.expires_in_hours or 48)
        slug = f"pick-{secrets.token_hex(4)}"

        if db is not None:
            room_id = uuid.uuid4()
            room = PickRoomModel(
                room_id=room_id,
                host_id=h_uuid,
                slug=slug,
                title=data.title,
                constraints_json=data.constraints_json or {},
                status="OPEN",
                expires_at=expires_at,
                created_at=now,
            )
            db.add(room)
            await db.flush()

            for title_id in set(data.candidate_title_ids):
                t_uuid = _resolve_uuid(title_id, "title_id")
                db.add(PickRoomCandidateModel(room_id=room_id, title_id=t_uuid))
            await db.flush()

            res = await self.get_pick_room_by_slug(db, slug)
            if not res:
                raise ValueError("Failed to retrieve created pick room")
            return res
        else:
            room_id = uuid.uuid4()
            SEED_PICK_ROOMS[slug] = {
                "room_id": room_id,
                "host_id": h_uuid,
                "slug": slug,
                "title": data.title,
                "constraints_json": data.constraints_json or {},
                "status": "OPEN",
                "winning_title_id": None,
                "expires_at": expires_at,
                "created_at": now,
                "candidate_title_ids": [str(t) for t in data.candidate_title_ids],
            }
            res = await self.get_pick_room_by_slug(None, slug)
            if not res:
                raise ValueError("Failed to retrieve created pick room")
            return res

    async def get_pick_room_by_slug(
        self,
        db: Optional[AsyncSession],
        slug: str,
    ) -> Optional[PickRoomDetailResponse]:
        """
        Fetches full room details, candidates, and current vote counts by slug.
        """
        if db is not None:
            from ..models.canonical import TitleModel

            stmt_room = select(PickRoomModel).where(PickRoomModel.slug == slug)
            room = (await db.execute(stmt_room)).scalar_one_or_none()
            if not room:
                return None

            # Get candidate titles
            stmt_cand = (
                select(PickRoomCandidateModel.title_id, TitleModel)
                .join(TitleModel, PickRoomCandidateModel.title_id == TitleModel.title_id)
                .where(PickRoomCandidateModel.room_id == room.room_id)
            )
            cand_rows = (await db.execute(stmt_cand)).all()

            # Get all votes for this room
            stmt_votes = select(PickVoteModel).where(PickVoteModel.room_id == room.room_id)
            votes = (await db.execute(stmt_votes)).scalars().all()

            # Map votes per candidate
            vote_map: Dict[uuid.UUID, List[str]] = {}
            for v in votes:
                if v.vote_type == "UPVOTE":
                    name = v.guest_name or "Circle Member"
                    vote_map.setdefault(v.title_id, []).append(name)

            candidates: List[CandidateSummary] = []
            for tid, tmodel in cand_rows:
                voters = vote_map.get(tid, [])
                candidates.append(
                    CandidateSummary(
                        title_id=tid,
                        canonical_title=tmodel.canonical_title,
                        original_title=tmodel.original_title,
                        production_year=tmodel.production_year,
                        poster_url=resolve_poster_url(tmodel.poster_url),
                        backdrop_url=resolve_backdrop_url(tmodel.backdrop_url),
                        upvotes=len(voters),
                        voter_names=voters,
                    )
                )

            # Sort candidates by upvotes descending
            candidates.sort(key=lambda c: c.upvotes, reverse=True)

            winning_name = None
            if room.winning_title_id:
                stmt_w = select(TitleModel.canonical_title).where(TitleModel.title_id == room.winning_title_id)
                winning_name = (await db.execute(stmt_w)).scalar_one_or_none()

            now = datetime.now(timezone.utc)
            is_expired = room.expires_at is not None and room.expires_at < now

            return PickRoomDetailResponse(
                room_id=room.room_id,
                host_id=room.host_id,
                host_name=None,
                host_username=None,
                slug=room.slug,
                title=room.title,
                status=room.status,
                winning_title_id=room.winning_title_id,
                winning_title_name=winning_name,
                total_votes=len(votes),
                candidates=candidates,
                expires_at=room.expires_at,
                is_expired=is_expired,
                created_at=room.created_at,
            )
        else:
            room = SEED_PICK_ROOMS.get(slug)
            if not room:
                return None
            room_votes = [v for v in SEED_PICK_VOTES if v["room_id"] == room["room_id"]]
            candidates = []
            for tid_str in room.get("candidate_title_ids", []):
                tid = uuid.UUID(tid_str) if isinstance(tid_str, str) else tid_str
                voters = [v.get("guest_name", "Guest") for v in room_votes if v["title_id"] == tid and v["vote_type"] == "UPVOTE"]
                candidates.append(
                    CandidateSummary(
                        title_id=tid,
                        canonical_title="Candidate Movie",
                        production_year=2024,
                        poster_url=None,
                        upvotes=len(voters),
                        voter_names=voters,
                    )
                )
            candidates.sort(key=lambda c: c.upvotes, reverse=True)
            return PickRoomDetailResponse(
                room_id=room["room_id"],
                host_id=room["host_id"],
                host_name="Host Member",
                host_username="host",
                slug=room["slug"],
                title=room["title"],
                status=room["status"],
                winning_title_id=room["winning_title_id"],
                winning_title_name="Candidate Movie" if room["winning_title_id"] else None,
                total_votes=len(room_votes),
                candidates=candidates,
                expires_at=room["expires_at"],
                is_expired=False,
                created_at=room["created_at"],
            )

    async def cast_pick_vote(
        self,
        db: Optional[AsyncSession],
        slug: str,
        voter_user_id: Optional[uuid.UUID],
        data: PickVoteCreate,
    ) -> PickVoteResponse:
        """
        Casts or updates an async vote for a candidate title in a pick room.
        """
        t_uuid = _resolve_uuid(data.title_id, "title_id")
        u_uuid = _resolve_uuid(voter_user_id, "voter_user_id") if voter_user_id else None
        fingerprint = data.voter_fingerprint or (str(u_uuid) if u_uuid else secrets.token_hex(8))
        voter_name = data.guest_name or ("Circle Member" if u_uuid else "Guest Voter")
        now = datetime.now(timezone.utc)

        if db is not None:
            stmt_room = select(PickRoomModel).where(PickRoomModel.slug == slug)
            room = (await db.execute(stmt_room)).scalar_one_or_none()
            if not room:
                raise ValueError("Pick room not found.")

            if room.status != "OPEN":
                raise ValueError(f"Cannot vote on a room with status '{room.status}'.")

            if room.expires_at and room.expires_at < now:
                raise ValueError("This pick room voting window has expired.")

            # Validate candidate belongs to room
            stmt_cand = select(PickRoomCandidateModel).where(
                and_(
                    PickRoomCandidateModel.room_id == room.room_id,
                    PickRoomCandidateModel.title_id == t_uuid,
                )
            )
            cand = (await db.execute(stmt_cand)).scalar_one_or_none()
            if not cand:
                raise ValueError("Specified title is not a candidate in this pick room.")

            # Check for existing vote by this fingerprint & candidate
            stmt_existing = select(PickVoteModel).where(
                and_(
                    PickVoteModel.room_id == room.room_id,
                    PickVoteModel.voter_fingerprint == fingerprint,
                    PickVoteModel.title_id == t_uuid,
                )
            )
            vote_orm = (await db.execute(stmt_existing)).scalar_one_or_none()
            if vote_orm:
                vote_orm.vote_type = data.vote_type
                vote_orm.guest_name = voter_name
                vote_orm.user_id = u_uuid
            else:
                vote_orm = PickVoteModel(
                    vote_id=uuid.uuid4(),
                    room_id=room.room_id,
                    user_id=u_uuid,
                    guest_name=voter_name,
                    voter_fingerprint=fingerprint,
                    title_id=t_uuid,
                    vote_type=data.vote_type,
                    created_at=now,
                )
                db.add(vote_orm)

            await db.flush()
            return PickVoteResponse(
                vote_id=vote_orm.vote_id,
                room_id=room.room_id,
                title_id=t_uuid,
                voter_name=voter_name,
                vote_type=vote_orm.vote_type,
                created_at=vote_orm.created_at,
            )
        else:
            room = SEED_PICK_ROOMS.get(slug)
            if not room:
                raise ValueError("Pick room not found.")
            if room["status"] != "OPEN":
                raise ValueError(f"Cannot vote on a room with status '{room['status']}'.")
            vote_id = uuid.uuid4()
            SEED_PICK_VOTES.append({
                "vote_id": vote_id,
                "room_id": room["room_id"],
                "user_id": u_uuid,
                "guest_name": voter_name,
                "voter_fingerprint": fingerprint,
                "title_id": t_uuid,
                "vote_type": data.vote_type,
                "created_at": now,
            })
            return PickVoteResponse(
                vote_id=vote_id,
                room_id=room["room_id"],
                title_id=t_uuid,
                voter_name=voter_name,
                vote_type=data.vote_type,
                created_at=now,
            )

    async def close_pick_room(
        self,
        db: Optional[AsyncSession],
        slug: str,
        host_id: uuid.UUID,
    ) -> PickRoomCloseResponse:
        """
        Host closes voting ballot and declares winning title by majority vote.
        """
        h_uuid = _resolve_uuid(host_id, "host_id")

        if db is not None:
            from ..models.canonical import TitleModel

            stmt_room = select(PickRoomModel).where(PickRoomModel.slug == slug)
            room = (await db.execute(stmt_room)).scalar_one_or_none()
            if not room:
                raise ValueError("Pick room not found.")

            if room.host_id != h_uuid:
                raise PermissionError("Only the room host can close voting and finalize winner.")

            # Tally votes per candidate
            stmt_tally = (
                select(PickVoteModel.title_id, func.count(PickVoteModel.vote_id))
                .where(
                    and_(
                        PickVoteModel.room_id == room.room_id,
                        PickVoteModel.vote_type == "UPVOTE",
                    )
                )
                .group_by(PickVoteModel.title_id)
                .order_by(func.count(PickVoteModel.vote_id).desc())
            )
            tallies = (await db.execute(stmt_tally)).all()

            winning_title_id = None
            winning_name = None
            if tallies:
                winning_title_id = tallies[0][0]
                stmt_w = select(TitleModel.canonical_title).where(TitleModel.title_id == winning_title_id)
                winning_name = (await db.execute(stmt_w)).scalar_one_or_none()
            else:
                # If no votes, pick the first candidate
                stmt_first = select(PickRoomCandidateModel.title_id).where(
                    PickRoomCandidateModel.room_id == room.room_id
                ).limit(1)
                winning_title_id = (await db.execute(stmt_first)).scalar_one_or_none()
                if winning_title_id:
                    stmt_w = select(TitleModel.canonical_title).where(TitleModel.title_id == winning_title_id)
                    winning_name = (await db.execute(stmt_w)).scalar_one_or_none()

            room.status = "RESOLVED"
            room.winning_title_id = winning_title_id
            await db.flush()

            stmt_count = select(func.count(PickVoteModel.vote_id)).where(PickVoteModel.room_id == room.room_id)
            total_votes = (await db.execute(stmt_count)).scalar_one() or 0

            return PickRoomCloseResponse(
                room_id=room.room_id,
                slug=room.slug,
                status="RESOLVED",
                winning_title_id=winning_title_id,
                winning_title_name=winning_name,
                total_votes_cast=total_votes,
            )
        else:
            room = SEED_PICK_ROOMS.get(slug)
            if not room:
                raise ValueError("Pick room not found.")
            if room["host_id"] != h_uuid:
                raise PermissionError("Only the room host can close voting and finalize winner.")
            room["status"] = "RESOLVED"
            candidates = room.get("candidate_title_ids", [])
            winner_id = uuid.UUID(candidates[0]) if candidates else uuid.uuid4()
            room["winning_title_id"] = winner_id
            room_votes = [v for v in SEED_PICK_VOTES if v["room_id"] == room["room_id"]]
            return PickRoomCloseResponse(
                room_id=room["room_id"],
                slug=room["slug"],
                status="RESOLVED",
                winning_title_id=winner_id,
                winning_title_name="Winning Movie",
                total_votes_cast=len(room_votes),
            )

    # ── Wrapped-Style Cinema Recap (Part 2 — Item 2.9) ──────────────────────────

    async def get_user_recap(
        self,
        db: Optional[AsyncSession],
        user_id: uuid.UUID,
        period: str = "yearly",
        year: Optional[int] = None,
    ) -> RecapResponse:
        """
        Aggregates annual or monthly cinema viewing analytics, top genres, directors,
        longest streak, friend circle percentile, and cinema personality archetype.
        """
        u_uuid = _resolve_uuid(user_id, "user_id")
        now = datetime.now(timezone.utc)
        target_year = year or now.year

        if period == "yearly":
            start_date = datetime(target_year, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(target_year + 1, 1, 1, tzinfo=timezone.utc)
        elif period == "monthly":
            start_date = datetime(target_year, now.month, 1, tzinfo=timezone.utc)
            if now.month == 12:
                end_date = datetime(target_year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end_date = datetime(target_year, now.month + 1, 1, tzinfo=timezone.utc)
        else:  # all_time
            start_date = datetime(1970, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(2100, 1, 1, tzinfo=timezone.utc)

        if db is not None:
            from ..models.personal import WatchEventModel, UserStreakModel
            from ..models.canonical import TitleModel, TitleGenreModel, GenreModel, CreditModel, PersonModel, EditionModel

            # 1. Total titles watched & watch event ids
            stmt_watches = (
                select(WatchEventModel.watch_event_id, WatchEventModel.title_id, WatchEventModel.edition_id)
                .where(
                    and_(
                        WatchEventModel.user_id == u_uuid,
                        WatchEventModel.is_tombstoned == False,  # noqa: E712
                        WatchEventModel.watched_at >= start_date,
                        WatchEventModel.watched_at < end_date,
                    )
                )
            )
            watch_rows = (await db.execute(stmt_watches)).all()
            total_watched = len(watch_rows)
            title_ids = list({r[1] for r in watch_rows if r[1] is not None})
            edition_ids = list({r[2] for r in watch_rows if r[2] is not None})

            # 2. Total runtime minutes
            total_runtime = 0
            if edition_ids:
                stmt_rt = select(func.coalesce(func.sum(EditionModel.runtime_minutes), 0)).where(EditionModel.edition_id.in_(edition_ids))
                total_runtime = int((await db.execute(stmt_rt)).scalar_one() or 0)
            uncounted_watches = total_watched - len([r for r in watch_rows if r[2] is not None])
            if uncounted_watches > 0:
                total_runtime += uncounted_watches * 110

            # 3. Longest streak
            stmt_streak = select(UserStreakModel.longest_streak).where(UserStreakModel.user_id == u_uuid)
            longest_streak = (await db.execute(stmt_streak)).scalar_one_or_none() or 0

            # 4. Top Genres
            top_genres: List[RecapGenreStat] = []
            if title_ids:
                stmt_genres = (
                    select(GenreModel.name, func.count(WatchEventModel.watch_event_id))
                    .join(TitleGenreModel, GenreModel.genre_id == TitleGenreModel.genre_id)
                    .join(WatchEventModel, TitleGenreModel.title_id == WatchEventModel.title_id)
                    .where(
                        and_(
                            WatchEventModel.user_id == u_uuid,
                            WatchEventModel.is_tombstoned == False,  # noqa: E712
                            WatchEventModel.watched_at >= start_date,
                            WatchEventModel.watched_at < end_date,
                        )
                    )
                    .group_by(GenreModel.name)
                    .order_by(func.count(WatchEventModel.watch_event_id).desc())
                    .limit(5)
                )
                genre_rows = (await db.execute(stmt_genres)).all()
                total_genre_hits = sum(r[1] for r in genre_rows) or 1
                top_genres = [
                    RecapGenreStat(
                        genre=r[0],
                        count=r[1],
                        percentage=round((r[1] / total_genre_hits) * 100, 1),
                    )
                    for r in genre_rows
                ]

            # 5. Top Directors
            top_directors: List[RecapDirectorStat] = []
            if title_ids:
                stmt_dirs = (
                    select(PersonModel.canonical_name, func.count(WatchEventModel.watch_event_id))
                    .join(CreditModel, PersonModel.person_id == CreditModel.person_id)
                    .join(WatchEventModel, CreditModel.title_id == WatchEventModel.title_id)
                    .where(
                        and_(
                            WatchEventModel.user_id == u_uuid,
                            WatchEventModel.is_tombstoned == False,  # noqa: E712
                            CreditModel.credit_role_id == "DIRECTOR",
                            WatchEventModel.watched_at >= start_date,
                            WatchEventModel.watched_at < end_date,
                        )
                    )
                    .group_by(PersonModel.canonical_name)
                    .order_by(func.count(WatchEventModel.watch_event_id).desc())
                    .limit(3)
                )
                top_directors = [
                    RecapDirectorStat(director=r[0], count=r[1])
                    for r in (await db.execute(stmt_dirs)).all()
                ]

            # 6. Favorite Release Era (average production year)
            favorite_era = "Contemporary Cinema (2020s)"
            if title_ids:
                stmt_years = select(func.avg(TitleModel.production_year)).where(TitleModel.title_id.in_(title_ids))
                avg_year = (await db.execute(stmt_years)).scalar_one_or_none()
                if avg_year:
                    if avg_year < 1980:
                        favorite_era = "Golden Age & Classic Hollywood (Pre-1980)"
                    elif avg_year < 2000:
                        favorite_era = "Retro & Blockbuster Era (80s–90s)"
                    elif avg_year < 2015:
                        favorite_era = "Turn of the Millennium (2000–2014)"
                    else:
                        favorite_era = "Modern Cinema (2015–Present)"

            # 7. Friend Circle Percentile
            stmt_f = select(FriendshipModel).where(
                and_(
                    or_(FriendshipModel.requester_id == u_uuid, FriendshipModel.addressee_id == u_uuid),
                    FriendshipModel.status == FriendshipStatusEnum.ACCEPTED.value,
                )
            )
            friendships = (await db.execute(stmt_f)).scalars().all()
            friend_ids = [
                f.addressee_id if f.requester_id == u_uuid else f.requester_id
                for f in friendships
            ]

            circle_percentile = 75.0
            if friend_ids:
                stmt_friend_counts = (
                    select(WatchEventModel.user_id, func.count(WatchEventModel.watch_event_id))
                    .where(
                        and_(
                            WatchEventModel.user_id.in_(friend_ids),
                            WatchEventModel.is_tombstoned == False,  # noqa: E712
                            WatchEventModel.watched_at >= start_date,
                            WatchEventModel.watched_at < end_date,
                        )
                    )
                    .group_by(WatchEventModel.user_id)
                )
                friend_counts = dict((await db.execute(stmt_friend_counts)).all())
                all_volumes = [friend_counts.get(fid, 0) for fid in friend_ids] + [total_watched]
                lower_count = sum(1 for v in all_volumes if v <= total_watched)
                circle_percentile = round((lower_count / len(all_volumes)) * 100, 1)

            # 8. Cinema Archetype Classification
            dominant_genre = top_genres[0].genre if top_genres else "General"
            archetype = "The Cinephile Explorer"
            description = "A versatile viewer with an insatiable appetite for cinematic journeys across genres."

            if "Sci-Fi" in dominant_genre or "Science Fiction" in dominant_genre:
                archetype = "The Sci-Fi Visionary"
                description = "Always drawn toward futuristic frontiers, mind-bending speculative worldbuilding, and cosmic epics."
            elif "Drama" in dominant_genre:
                archetype = "The Humanist Critic"
                description = "Drawn to emotional resonance, complex characters, and poignant character-driven storytelling."
            elif "Action" in dominant_genre or "Adventure" in dominant_genre:
                archetype = "The Kinetic Thrillseeker"
                description = "Thriving on high-octane set-pieces, kinetic choreography, and heart-pumping spectacle."
            elif "Horror" in dominant_genre or "Thriller" in dominant_genre:
                archetype = "The Midnight Auteur"
                description = "Feasting on atmospheric dread, psychological suspense, and boundary-pushing tension."
            elif total_watched >= 30:
                archetype = "The Marathon Cineaste"
                description = "An unstoppable cinema lover devouring entire filmographies with tireless passion."

            return RecapResponse(
                user_id=u_uuid,
                period=period,
                year=target_year,
                total_titles_watched=total_watched,
                total_runtime_minutes=total_runtime,
                longest_streak_days=longest_streak,
                top_genres=top_genres,
                top_directors=top_directors,
                favorite_release_era=favorite_era,
                circle_percentile=circle_percentile,
                cinema_archetype=archetype,
                archetype_description=description,
                generated_at=now,
            )
        else:
            top_genres = [
                RecapGenreStat(genre="Sci-Fi", count=8, percentage=50.0),
                RecapGenreStat(genre="Drama", count=5, percentage=31.2),
                RecapGenreStat(genre="Thriller", count=3, percentage=18.8),
            ]
            top_directors = [
                RecapDirectorStat(director="Denis Villeneuve", count=4),
                RecapDirectorStat(director="Christopher Nolan", count=3),
            ]
            return RecapResponse(
                user_id=u_uuid,
                user_name="Cinephile Pioneer",
                user_username="cinephile",
                period=period,
                year=target_year,
                total_titles_watched=16,
                total_runtime_minutes=2140,
                longest_streak_days=7,
                top_genres=top_genres,
                top_directors=top_directors,
                favorite_release_era="Modern Cinema (2015–Present)",
                circle_percentile=85.0,
                cinema_archetype="The Sci-Fi Visionary",
                archetype_description="Always drawn toward futuristic frontiers, mind-bending speculative worldbuilding, and cosmic epics.",
                generated_at=now,
            )

    # ── Watch Clubs (Part 2 — Item 2.10) ─────────────────────────────────────────

    async def create_watch_club(
        self, db: Optional[AsyncSession], creator_id: uuid.UUID, payload: WatchClubCreate,
    ) -> WatchClubResponse:
        """Create a new watch club and add the creator as OWNER."""
        c_uuid = _resolve_uuid(creator_id, "creator_id")
        now = datetime.now(timezone.utc)
        slug = payload.name.lower().replace(" ", "-")[:100] + "-" + uuid.uuid4().hex[:6]

        if db is not None:
            from ..models.social import WatchClubModel, ClubMembershipModel
            club = WatchClubModel(
                name=payload.name, slug=slug, created_by=c_uuid,
                avatar_url=payload.avatar_url, description=payload.description,
                member_count=1, created_at=now,
            )
            db.add(club)
            await db.flush()
            membership = ClubMembershipModel(
                club_id=club.club_id, user_id=c_uuid, role="OWNER", joined_at=now,
            )
            db.add(membership)
            await db.commit()
            return WatchClubResponse(
                club_id=club.club_id, name=club.name, slug=club.slug,
                created_by=c_uuid, member_count=1, created_at=now,
            )
        else:
            club_id = uuid.uuid4()
            rec = {
                "club_id": club_id, "name": payload.name, "slug": slug,
                "created_by": c_uuid, "avatar_url": payload.avatar_url,
                "description": payload.description, "member_count": 1, "created_at": now,
            }
            SEED_CLUBS[slug] = rec
            SEED_CLUB_MEMBERSHIPS.append({"club_id": club_id, "user_id": c_uuid, "role": "OWNER", "joined_at": now})
            return WatchClubResponse(**rec)

    async def get_watch_club(
        self, db: Optional[AsyncSession], slug: str,
    ) -> ClubDetailResponse:
        """Retrieve a watch club by slug with members list."""
        if db is not None:
            from ..models.social import WatchClubModel, ClubMembershipModel
            stmt = select(WatchClubModel).where(WatchClubModel.slug == slug)
            club = (await db.execute(stmt)).scalar_one_or_none()
            if not club:
                raise ValueError("Watch club not found.")
            stmt_m = select(ClubMembershipModel).where(ClubMembershipModel.club_id == club.club_id)
            members = (await db.execute(stmt_m)).scalars().all()
            return ClubDetailResponse(
                club=WatchClubResponse(
                    club_id=club.club_id, name=club.name, slug=club.slug,
                    created_by=club.created_by, member_count=club.member_count,
                    avatar_url=club.avatar_url, description=club.description,
                    created_at=club.created_at,
                ),
                members=[
                    ClubMembershipResponse(
                        club_id=m.club_id, user_id=m.user_id, role=m.role, joined_at=m.joined_at,
                    ) for m in members
                ],
            )
        else:
            rec = SEED_CLUBS.get(slug)
            if not rec:
                raise ValueError("Watch club not found.")
            members = [
                ClubMembershipResponse(**m) for m in SEED_CLUB_MEMBERSHIPS if m["club_id"] == rec["club_id"]
            ]
            return ClubDetailResponse(club=WatchClubResponse(**rec), members=members)

    async def join_watch_club(
        self, db: Optional[AsyncSession], slug: str, user_id: uuid.UUID,
    ) -> ClubMembershipResponse:
        """Add a user to a watch club idempotently."""
        u_uuid = _resolve_uuid(user_id, "user_id")
        now = datetime.now(timezone.utc)
        if db is not None:
            from ..models.social import WatchClubModel, ClubMembershipModel
            stmt = select(WatchClubModel).where(WatchClubModel.slug == slug)
            club = (await db.execute(stmt)).scalar_one_or_none()
            if not club:
                raise ValueError("Watch club not found.")

            stmt_m = select(ClubMembershipModel).where(
                and_(
                    ClubMembershipModel.club_id == club.club_id,
                    ClubMembershipModel.user_id == u_uuid,
                )
            )
            existing_m = (await db.execute(stmt_m)).scalar_one_or_none()
            if existing_m:
                return ClubMembershipResponse(
                    club_id=existing_m.club_id,
                    user_id=existing_m.user_id,
                    role=existing_m.role,
                    joined_at=existing_m.joined_at,
                )

            membership = ClubMembershipModel(
                club_id=club.club_id, user_id=u_uuid, role="MEMBER", joined_at=now,
            )
            db.add(membership)
            club.member_count += 1
            await db.flush()
            return ClubMembershipResponse(
                club_id=club.club_id, user_id=u_uuid, role="MEMBER", joined_at=now,
            )
        else:
            rec = SEED_CLUBS.get(slug)
            if not rec:
                raise ValueError("Watch club not found.")
            for m in SEED_CLUB_MEMBERSHIPS:
                if m["club_id"] == rec["club_id"] and m["user_id"] == u_uuid:
                    return ClubMembershipResponse(**m)
            m = {"club_id": rec["club_id"], "user_id": u_uuid, "role": "MEMBER", "joined_at": now}
            SEED_CLUB_MEMBERSHIPS.append(m)
            rec["member_count"] = rec.get("member_count", 1) + 1
            return ClubMembershipResponse(**m)

    async def list_user_clubs(
        self, db: Optional[AsyncSession], user_id: uuid.UUID,
    ) -> List[WatchClubResponse]:
        """List all clubs a user belongs to."""
        u_uuid = _resolve_uuid(user_id, "user_id")
        if db is not None:
            from ..models.social import WatchClubModel, ClubMembershipModel
            stmt = (
                select(WatchClubModel)
                .join(ClubMembershipModel, WatchClubModel.club_id == ClubMembershipModel.club_id)
                .where(ClubMembershipModel.user_id == u_uuid)
            )
            clubs = (await db.execute(stmt)).scalars().all()
            return [
                WatchClubResponse(
                    club_id=c.club_id, name=c.name, slug=c.slug,
                    created_by=c.created_by, member_count=c.member_count,
                    avatar_url=c.avatar_url, description=c.description,
                    created_at=c.created_at,
                ) for c in clubs
            ]
        else:
            my_club_ids = {m["club_id"] for m in SEED_CLUB_MEMBERSHIPS if m["user_id"] == u_uuid}
            return [WatchClubResponse(**c) for c in SEED_CLUBS.values() if c["club_id"] in my_club_ids]

    # ── Club Activity Feed (Part 2 — Item 2.12) ─────────────────────────────────

    async def post_club_activity(
        self, db: Optional[AsyncSession], club_id: uuid.UUID, user_id: uuid.UUID,
        activity_type: str, reference_id: Optional[uuid.UUID] = None, metadata: Optional[dict] = None,
    ) -> ClubActivityResponse:
        """Post an activity event to a club feed."""
        c_uuid = _resolve_uuid(club_id, "club_id")
        u_uuid = _resolve_uuid(user_id, "user_id")
        now = datetime.now(timezone.utc)
        if db is not None:
            from ..models.social import ClubActivityModel
            act = ClubActivityModel(
                club_id=c_uuid, user_id=u_uuid, activity_type=activity_type,
                reference_id=reference_id, metadata_json=metadata or {}, created_at=now,
            )
            db.add(act)
            await db.flush()
            return ClubActivityResponse(
                activity_id=act.activity_id, club_id=c_uuid, user_id=u_uuid,
                activity_type=activity_type, reference_id=reference_id,
                metadata_json=metadata, created_at=now,
            )
        else:
            aid = uuid.uuid4()
            rec = {
                "activity_id": aid, "club_id": c_uuid, "user_id": u_uuid,
                "activity_type": activity_type, "reference_id": reference_id,
                "metadata_json": metadata or {}, "created_at": now,
            }
            SEED_CLUB_ACTIVITIES.append(rec)
            return ClubActivityResponse(**rec)

    async def get_club_activity_feed(
        self, db: Optional[AsyncSession], slug: str, limit: int = 20,
    ) -> List[ClubActivityResponse]:
        """Retrieve the latest activity feed for a club."""
        if db is not None:
            from ..models.social import WatchClubModel, ClubActivityModel
            stmt_club = select(WatchClubModel.club_id).where(WatchClubModel.slug == slug)
            club_id = (await db.execute(stmt_club)).scalar_one_or_none()
            if not club_id:
                raise ValueError("Watch club not found.")
            stmt = (
                select(ClubActivityModel)
                .where(ClubActivityModel.club_id == club_id)
                .order_by(ClubActivityModel.created_at.desc())
                .limit(limit)
            )
            activities = (await db.execute(stmt)).scalars().all()
            return [
                ClubActivityResponse(
                    activity_id=a.activity_id, club_id=a.club_id, user_id=a.user_id,
                    activity_type=a.activity_type, reference_id=a.reference_id,
                    metadata_json=a.metadata_json, created_at=a.created_at,
                ) for a in activities
            ]
        else:
            rec = SEED_CLUBS.get(slug)
            if not rec:
                raise ValueError("Watch club not found.")
            feed = [a for a in SEED_CLUB_ACTIVITIES if a["club_id"] == rec["club_id"]]
            feed.sort(key=lambda x: x["created_at"], reverse=True)
            return [ClubActivityResponse(**a) for a in feed[:limit]]

    # ── Monthly Challenges (Part 2 — Item 2.13) ─────────────────────────────────

    async def create_challenge(
        self, db: Optional[AsyncSession], payload: ChallengeCreate,
    ) -> ChallengeResponse:
        """Create a new viewing challenge."""
        now = datetime.now(timezone.utc)
        if db is not None:
            from ..models.social import ChallengeModel
            ch = ChallengeModel(
                title=payload.title, description=payload.description,
                challenge_type=payload.challenge_type, club_id=payload.club_id,
                criteria_json=payload.criteria_json or {}, goal_count=payload.goal_count,
                starts_at=payload.starts_at, ends_at=payload.ends_at, created_at=now,
            )
            db.add(ch)
            await db.flush()
            return ChallengeResponse(
                challenge_id=ch.challenge_id, title=ch.title, description=ch.description,
                challenge_type=ch.challenge_type, club_id=ch.club_id,
                criteria_json=ch.criteria_json, goal_count=ch.goal_count,
                starts_at=ch.starts_at, ends_at=ch.ends_at, created_at=now,
            )
        else:
            ch_id = uuid.uuid4()
            rec = {
                "challenge_id": ch_id, "title": payload.title, "description": payload.description,
                "challenge_type": payload.challenge_type, "club_id": payload.club_id,
                "criteria_json": payload.criteria_json or {}, "goal_count": payload.goal_count,
                "starts_at": payload.starts_at, "ends_at": payload.ends_at,
                "created_at": now, "participant_count": 0,
            }
            SEED_CHALLENGES[ch_id] = rec
            return ChallengeResponse(**rec)

    async def join_challenge(
        self, db: Optional[AsyncSession], challenge_id: uuid.UUID, user_id: uuid.UUID,
    ) -> ChallengeParticipantResponse:
        """Join a challenge as a participant idempotently."""
        ch_uuid = _resolve_uuid(challenge_id, "challenge_id")
        u_uuid = _resolve_uuid(user_id, "user_id")
        now = datetime.now(timezone.utc)
        if db is not None:
            from ..models.social import ChallengeParticipantModel
            stmt_p = select(ChallengeParticipantModel).where(
                and_(
                    ChallengeParticipantModel.challenge_id == ch_uuid,
                    ChallengeParticipantModel.user_id == u_uuid,
                )
            )
            existing_p = (await db.execute(stmt_p)).scalar_one_or_none()
            if existing_p:
                return ChallengeParticipantResponse(
                    challenge_id=existing_p.challenge_id,
                    user_id=existing_p.user_id,
                    progress=existing_p.progress,
                    completed=existing_p.completed,
                    completed_at=existing_p.completed_at,
                    joined_at=existing_p.joined_at,
                )

            p = ChallengeParticipantModel(
                challenge_id=ch_uuid, user_id=u_uuid, progress=0, completed=False, joined_at=now,
            )
            db.add(p)
            await db.flush()
            return ChallengeParticipantResponse(
                challenge_id=ch_uuid, user_id=u_uuid, progress=0, completed=False, joined_at=now,
            )
        else:
            if ch_uuid not in SEED_CHALLENGES:
                raise ValueError("Challenge not found.")
            for p in SEED_CHALLENGE_PARTICIPANTS:
                if p["challenge_id"] == ch_uuid and p["user_id"] == u_uuid:
                    return ChallengeParticipantResponse(**p)
            rec = {"challenge_id": ch_uuid, "user_id": u_uuid, "progress": 0, "completed": False, "completed_at": None, "joined_at": now}
            SEED_CHALLENGE_PARTICIPANTS.append(rec)
            SEED_CHALLENGES[ch_uuid]["participant_count"] = SEED_CHALLENGES[ch_uuid].get("participant_count", 0) + 1
            return ChallengeParticipantResponse(**rec)

    async def update_challenge_progress(
        self, db: Optional[AsyncSession], challenge_id: uuid.UUID, user_id: uuid.UUID, increment: int = 1,
    ) -> ChallengeParticipantResponse:
        """Increment a participant's challenge progress with active time window validation."""
        ch_uuid = _resolve_uuid(challenge_id, "challenge_id")
        u_uuid = _resolve_uuid(user_id, "user_id")
        now = datetime.now(timezone.utc)
        if db is not None:
            from ..models.social import ChallengeParticipantModel, ChallengeModel
            # Validate challenge exists and is active
            goal_stmt = select(ChallengeModel).where(ChallengeModel.challenge_id == ch_uuid)
            ch = (await db.execute(goal_stmt)).scalar_one_or_none()
            if not ch:
                raise ValueError("Challenge not found.")
            if now < ch.starts_at or now >= ch.ends_at:
                raise ValueError("Cannot update progress on an inactive or expired challenge.")

            stmt = select(ChallengeParticipantModel).where(
                and_(ChallengeParticipantModel.challenge_id == ch_uuid, ChallengeParticipantModel.user_id == u_uuid)
            )
            p = (await db.execute(stmt)).scalar_one_or_none()
            if not p:
                raise ValueError("Not a participant in this challenge.")
            p.progress += increment
            goal = ch.goal_count or 1
            if p.progress >= goal and not p.completed:
                p.completed = True
                p.completed_at = now
            await db.flush()
            return ChallengeParticipantResponse(
                challenge_id=ch_uuid, user_id=u_uuid, progress=p.progress,
                completed=p.completed, completed_at=p.completed_at, joined_at=p.joined_at,
            )
        else:
            ch = SEED_CHALLENGES.get(ch_uuid)
            if not ch:
                raise ValueError("Challenge not found.")
            if now < ch["starts_at"] or now >= ch["ends_at"]:
                raise ValueError("Cannot update progress on an inactive or expired challenge.")

            for rec in SEED_CHALLENGE_PARTICIPANTS:
                if rec["challenge_id"] == ch_uuid and rec["user_id"] == u_uuid:
                    rec["progress"] += increment
                    if rec["progress"] >= ch.get("goal_count", 1) and not rec["completed"]:
                        rec["completed"] = True
                        rec["completed_at"] = now
                    return ChallengeParticipantResponse(**rec)
            raise ValueError("Not a participant in this challenge.")

    async def get_challenge_detail(
        self, db: Optional[AsyncSession], challenge_id: uuid.UUID,
    ) -> ChallengeDetailResponse:
        """Get full challenge details with participants."""
        ch_uuid = _resolve_uuid(challenge_id, "challenge_id")
        if db is not None:
            from ..models.social import ChallengeModel, ChallengeParticipantModel
            stmt = select(ChallengeModel).where(ChallengeModel.challenge_id == ch_uuid)
            ch = (await db.execute(stmt)).scalar_one_or_none()
            if not ch:
                raise ValueError("Challenge not found.")
            stmt_p = select(ChallengeParticipantModel).where(ChallengeParticipantModel.challenge_id == ch_uuid)
            participants = (await db.execute(stmt_p)).scalars().all()
            return ChallengeDetailResponse(
                challenge=ChallengeResponse(
                    challenge_id=ch.challenge_id, title=ch.title, description=ch.description,
                    challenge_type=ch.challenge_type, club_id=ch.club_id,
                    criteria_json=ch.criteria_json, goal_count=ch.goal_count,
                    starts_at=ch.starts_at, ends_at=ch.ends_at, created_at=ch.created_at,
                    participant_count=len(participants),
                ),
                participants=[
                    ChallengeParticipantResponse(
                        challenge_id=p.challenge_id, user_id=p.user_id, progress=p.progress,
                        completed=p.completed, completed_at=p.completed_at, joined_at=p.joined_at,
                    ) for p in participants
                ],
            )
        else:
            ch = SEED_CHALLENGES.get(ch_uuid)
            if not ch:
                raise ValueError("Challenge not found.")
            participants = [
                ChallengeParticipantResponse(**p) for p in SEED_CHALLENGE_PARTICIPANTS if p["challenge_id"] == ch_uuid
            ]
            ch_resp = ChallengeResponse(**ch)
            ch_resp.participant_count = len(participants)
            return ChallengeDetailResponse(challenge=ch_resp, participants=participants)

    async def list_active_challenges(
        self, db: Optional[AsyncSession], user_id: Optional[uuid.UUID] = None,
    ) -> List[ChallengeResponse]:
        """List all currently active challenges, with the caller's own
        progress attached (my_progress/my_completed) when user_id is given."""
        now = datetime.now(timezone.utc)
        if db is not None:
            from ..models.social import ChallengeModel, ChallengeParticipantModel
            stmt = (
                select(ChallengeModel)
                .where(and_(ChallengeModel.starts_at <= now, ChallengeModel.ends_at > now))
                .order_by(ChallengeModel.ends_at.asc())
            )
            challenges = (await db.execute(stmt)).scalars().all()

            # Real participant counts, one grouped query for the whole page
            # rather than N+1 -- previously omitted entirely here (unlike
            # get_challenge_detail, which does compute it), so every
            # challenge always showed "0 Cinephiles" on the list/browse view
            # regardless of how many people had actually joined.
            count_map: Dict[uuid.UUID, int] = {}
            # Caller's own progress per challenge -- previously nothing in
            # this list response carried per-user progress at all, so the
            # frontend's "goal progress" bar was a hardcoded 40%-width div
            # (explicitly commented "Progress Bar Demo") for every challenge,
            # every user, regardless of anyone's real progress.
            my_progress_map: Dict[uuid.UUID, Tuple[int, bool]] = {}
            if challenges:
                challenge_ids = [c.challenge_id for c in challenges]
                count_stmt = (
                    select(ChallengeParticipantModel.challenge_id, func.count())
                    .where(ChallengeParticipantModel.challenge_id.in_(challenge_ids))
                    .group_by(ChallengeParticipantModel.challenge_id)
                )
                count_map = dict((await db.execute(count_stmt)).all())

                if user_id is not None:
                    my_stmt = select(
                        ChallengeParticipantModel.challenge_id,
                        ChallengeParticipantModel.progress,
                        ChallengeParticipantModel.completed,
                    ).where(
                        and_(
                            ChallengeParticipantModel.challenge_id.in_(challenge_ids),
                            ChallengeParticipantModel.user_id == user_id,
                        )
                    )
                    my_progress_map = {
                        row[0]: (row[1], row[2]) for row in (await db.execute(my_stmt)).all()
                    }

            return [
                ChallengeResponse(
                    challenge_id=c.challenge_id, title=c.title, description=c.description,
                    challenge_type=c.challenge_type, club_id=c.club_id,
                    criteria_json=c.criteria_json, goal_count=c.goal_count,
                    starts_at=c.starts_at, ends_at=c.ends_at, created_at=c.created_at,
                    participant_count=count_map.get(c.challenge_id, 0),
                    my_progress=my_progress_map.get(c.challenge_id, (None, False))[0],
                    my_completed=my_progress_map.get(c.challenge_id, (None, False))[1],
                ) for c in challenges
            ]
        else:
            # Seed-fallback dicts already carry participant_count (kept in
            # sync by join_challenge's seed branch above), so **c picks it
            # up correctly here -- only the real-DB path above was missing it.
            active = [
                ChallengeResponse(**c) for c in SEED_CHALLENGES.values()
                if c["starts_at"] <= now < c["ends_at"]
            ]
            if user_id is not None:
                for resp in active:
                    for p in SEED_CHALLENGE_PARTICIPANTS:
                        if p["challenge_id"] == resp.challenge_id and p["user_id"] == user_id:
                            resp.my_progress = p["progress"]
                            resp.my_completed = p["completed"]
                            break
            return active


social_repository = SocialRepository()




