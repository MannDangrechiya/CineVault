# CineVault OS — Social Core Schemas (v2.0 Module 1 & 2)
# Request and response models for Friendships, Recommendations, and Taste Profiles (ADR-003, ADR-004)

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator


# =========================================================================
# Enumerations
# =========================================================================

class FriendshipStatusEnum(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    BLOCKED = "BLOCKED"


class RecommendationStatusEnum(str, Enum):
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WATCHED = "WATCHED"
    RATED = "RATED"


# State Machine Transition Rules
# SENT -> ACCEPTED / REJECTED
# ACCEPTED -> WATCHED
# WATCHED -> RATED
ALLOWED_STATE_TRANSITIONS: Dict[RecommendationStatusEnum, List[RecommendationStatusEnum]] = {
    RecommendationStatusEnum.SENT: [
        RecommendationStatusEnum.ACCEPTED,
        RecommendationStatusEnum.REJECTED,
    ],
    RecommendationStatusEnum.ACCEPTED: [
        RecommendationStatusEnum.WATCHED,
    ],
    RecommendationStatusEnum.WATCHED: [
        RecommendationStatusEnum.RATED,
    ],
    RecommendationStatusEnum.REJECTED: [],
    RecommendationStatusEnum.RATED: [],
}


# =========================================================================
# Recommendation Schemas
# =========================================================================

class RecommendationCreate(BaseModel):
    recipient_id: uuid.UUID = Field(..., description="Target user recipient UUID")
    title_id: uuid.UUID = Field(..., description="Canonical title UUID")
    context_note: Optional[str] = Field(None, max_length=1000, description="Optional personal note or reasoning")
    sender_predicted_rating: Optional[float] = Field(
        None, ge=1.0, le=10.0, description="Predicted rating on a 1-10 scale"
    )


class RecommendationStateUpdate(BaseModel):
    status: RecommendationStatusEnum = Field(
        ..., description="Target lifecycle state (ACCEPTED, REJECTED, WATCHED, RATED)"
    )
    recipient_actual_rating: Optional[float] = Field(
        None, ge=1.0, le=10.0, description="Actual rating given by recipient (required when transitioning to RATED)"
    )

    @model_validator(mode="after")
    def validate_rated_state(self) -> "RecommendationStateUpdate":
        if self.status == RecommendationStatusEnum.RATED and self.recipient_actual_rating is None:
            raise ValueError("recipient_actual_rating is required when transitioning status to 'RATED'.")
        return self


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recommendation_id: uuid.UUID
    sender_id: uuid.UUID
    recipient_id: uuid.UUID
    title_id: uuid.UUID
    status: RecommendationStatusEnum
    sender_predicted_rating: Optional[float] = None
    recipient_actual_rating: Optional[float] = None
    context_note: Optional[str] = None
    sent_at: datetime
    updated_at: datetime


class EnrichedRecommendationResponse(RecommendationResponse):
    """
    GET /social/recommendations response shape (PLAN.md 1.2): adds joined
    canonical.title metadata and best-effort sender/recipient display names on
    top of the raw RecommendationResponse fields, which are kept as-is so
    other callers (services/api/routers/automation.py) are unaffected.

    Display name resolution has a real limit: this system has no user-profile
    table at all (identity is a JWT `sub` hashed to a UUID, see PLAN.md Part 2
    grounding notes) — names are only resolvable for the fixed local-dev
    accounts in services/api/routers/auth.py's credential store. Real
    Keycloak-issued users resolve to null here; the frontend must render a
    sensible fallback, not fabricate a name.
    """
    canonical_title: Optional[str] = None
    poster_url: Optional[str] = None
    production_year: Optional[int] = None
    sender_name: Optional[str] = None
    sender_username: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_username: Optional[str] = None


# =========================================================================
# Friendship Schemas
# =========================================================================

class FriendshipCreate(BaseModel):
    addressee_id: uuid.UUID = Field(..., description="Target peer user UUID to connect with")
    trust_score: Optional[float] = Field(50.0, ge=0.0, le=100.0, description="Initial trust score")


class FriendshipUpdate(BaseModel):
    status: FriendshipStatusEnum = Field(..., description="Target status: ACCEPTED or BLOCKED")
    trust_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Updated trust score")


class FriendshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    friendship_id: uuid.UUID
    requester_id: uuid.UUID
    addressee_id: uuid.UUID
    status: FriendshipStatusEnum
    trust_score: float
    created_at: datetime
    updated_at: datetime


class EnrichedFriendshipResponse(FriendshipResponse):
    """
    GET /social/friendships response shape: adds the caller-relative
    `friend_id` (whichever of requester_id/addressee_id isn't the caller) plus
    a best-effort display name, same resolution limits as
    EnrichedRecommendationResponse above.
    """
    friend_id: uuid.UUID
    friend_name: Optional[str] = None
    friend_username: Optional[str] = None
    avatar_url: Optional[str] = None


# =========================================================================
# Vector Taste Profile & Compatibility Schemas (v2.0 Module 2)
# =========================================================================

class TasteMatchResponse(BaseModel):
    """Represents peer taste compatibility derived from pgvector cosine similarity."""
    model_config = ConfigDict(from_attributes=True)

    friend_id: uuid.UUID = Field(..., description="Target friend user UUID")
    compatibility_score: float = Field(
        ..., ge=0.0, le=100.0, description="Taste compatibility percentage score (0.0 to 100.0)"
    )


class UserTasteProfileUpdate(BaseModel):
    """Schema for updating 384-dimensional user taste embedding vector."""
    taste_vector: List[float] = Field(
        ..., description="Dense 384-dimensional taste vector for all-MiniLM-L6-v2 embeddings"
    )

    @field_validator("taste_vector")
    @classmethod
    def validate_vector_dimensions(cls, v: List[float]) -> List[float]:
        if len(v) != 384:
            raise ValueError(f"taste_vector must have exactly 384 dimensions, got {len(v)}")
        return v


class UserTasteProfileResponse(BaseModel):
    """Schema representing stored user taste profile metadata."""
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    taste_vector: Optional[List[float]] = None
    last_computed_at: datetime
    dimension: Optional[int] = 384


class TasteProfileComputeRequest(BaseModel):
    """Schema for requesting real vector computation for taste profile via Ollama."""
    taste_summary: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Natural language summary of user preferences (e.g. 'I love sci-fi and action')",
    )


