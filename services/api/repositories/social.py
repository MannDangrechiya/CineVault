# CineVault OS — Social Core Repository (v2.0 Module 1)
# Data access layer supporting PostgreSQL AsyncPG session and in-memory test fallback

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple, Any
import uuid
from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.social import FriendshipModel, RecommendationModel
from ..schemas.social import (
    FriendshipStatusEnum,
    FriendshipResponse,
    FriendshipCreate,
    RecommendationStatusEnum,
    RecommendationCreate,
    RecommendationStateUpdate,
    RecommendationResponse,
    ALLOWED_STATE_TRANSITIONS,
)

logger = logging.getLogger("cinevault.repositories.social")

# In-memory stores used during tests or offline fallback when db session is None
SEED_FRIENDSHIPS: Dict[uuid.UUID, FriendshipResponse] = {}
SEED_RECOMMENDATIONS: Dict[uuid.UUID, RecommendationResponse] = {}


def _resolve_uuid(val: Any, field_name: str = "id") -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"cinevault:{field_name}:{val}")


class SocialRepository:
    """Provides async database operations and state machine management for social relationships and recommendations."""

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


social_repository = SocialRepository()
