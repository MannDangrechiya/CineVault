# CineVault OS — Social Core Repository (v2.0 Module 1 & 2)
# Data access layer supporting PostgreSQL AsyncPG session, pgvector similarity, and in-memory test fallback

import logging
import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple, Any
import uuid
from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.social import FriendshipModel, RecommendationModel, UserTasteProfileModel
from ..schemas.social import (
    FriendshipStatusEnum,
    FriendshipResponse,
    FriendshipCreate,
    RecommendationStatusEnum,
    RecommendationCreate,
    RecommendationStateUpdate,
    RecommendationResponse,
    TasteMatchResponse,
    UserTasteProfileUpdate,
    UserTasteProfileResponse,
    ALLOWED_STATE_TRANSITIONS,
)

logger = logging.getLogger("cinevault.repositories.social")

# In-memory stores used during tests or offline fallback when db session is None
SEED_FRIENDSHIPS: Dict[uuid.UUID, FriendshipResponse] = {}
SEED_RECOMMENDATIONS: Dict[uuid.UUID, RecommendationResponse] = {}
SEED_TASTE_PROFILES: Dict[uuid.UUID, Dict[str, Any]] = {}


def _resolve_uuid(val: Any, field_name: str = "id") -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"cinevault:{field_name}:{val}")


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
        now = datetime.now(timezone.utc)
        friendship_id = uuid.uuid4()

        if db is not None:
            # Check existing
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
    ) -> Optional[FriendshipResponse]:
        """Updates status of a friendship (e.g. ACCEPTED or BLOCKED)."""
        fid_uuid = _resolve_uuid(friendship_id, "friendship_id")
        now = datetime.now(timezone.utc)

        if db is not None:
            stmt = select(FriendshipModel).where(
                FriendshipModel.friendship_id == fid_uuid
            )
            res = await db.execute(stmt)
            rec = res.scalars().first()
            if not rec:
                return None
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
        now = datetime.now(timezone.utc)

        if db is not None:
            stmt = select(RecommendationModel).where(
                RecommendationModel.recommendation_id == rec_uuid
            )
            res = await db.execute(stmt)
            rec = res.scalars().first()
            if not rec:
                raise KeyError(f"Recommendation with ID {recommendation_id} not found.")

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

            friend_ids: List[uuid.UUID] = []
            for f in friend_records:
                if f.requester_id == u_uuid:
                    friend_ids.append(f.addressee_id)
                elif f.addressee_id == u_uuid:
                    friend_ids.append(f.requester_id)

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
            friend_ids: List[uuid.UUID] = []
            for f in SEED_FRIENDSHIPS.values():
                if f.status == FriendshipStatusEnum.ACCEPTED:
                    if f.requester_id == u_uuid:
                        friend_ids.append(f.addressee_id)
                    elif f.addressee_id == u_uuid:
                        friend_ids.append(f.requester_id)

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


social_repository = SocialRepository()

