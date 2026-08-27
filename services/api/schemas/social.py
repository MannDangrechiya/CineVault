# CineVault OS — Social Core Schemas (v2.0 Module 1 & 2)
# Request and response models for Friendships, Recommendations, and Taste Profiles (ADR-003, ADR-004)

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
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
    """Schema for requesting real vector computation for taste profile via the self-hosted embedding service."""
    taste_summary: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Natural language summary of user preferences (e.g. 'I love sci-fi and action')",
    )


class CompatibilityResponse(BaseModel):
    """Detailed head-to-head compatibility breakdown between two users."""
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    friend_id: uuid.UUID
    friend_name: Optional[str] = None
    friend_username: Optional[str] = None
    compatibility_score: float = Field(
        ..., ge=0.0, le=100.0, description="Taste compatibility percentage score (0.0 to 100.0)"
    )
    taste_tier: str = Field(..., description="Compatibility tier label (Oracle, Critic, Regular, Curious)")
    shared_genres: List[str] = Field(default_factory=list, description="Top genres overlapping between both users")
    shared_directors: List[str] = Field(default_factory=list, description="Directors watched by both users")
    shared_favorite_titles: List[str] = Field(default_factory=list, description="Titles favored or highly rated by both users")
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LeaderboardEntry(BaseModel):
    """Represents a member's rank and viewing volume on the social circle leaderboard."""
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: Optional[str] = None
    username: Optional[str] = None
    watch_count: int = Field(0, description="Total titles or episodes watched within the period")
    watch_hours: float = Field(0.0, description="Total viewing duration in hours")
    rank: int = Field(..., description="Position on the leaderboard starting at 1")
    is_current_user: bool = Field(False, description="True if this entry corresponds to the requesting user")


class LeaderboardResponse(BaseModel):
    """Social circle viewing activity leaderboard."""
    model_config = ConfigDict(from_attributes=True)

    period: str = Field("weekly", description="Leaderboard time window: weekly, monthly, or all_time")
    entries: List[LeaderboardEntry] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BadgeResponse(BaseModel):
    """Badge achievement details."""
    model_config = ConfigDict(from_attributes=True)

    badge_id: uuid.UUID
    slug: str
    name: str
    description: str
    icon_url: Optional[str] = None
    is_earned: bool = False
    earned_at: Optional[datetime] = None
    context_json: Optional[Dict[str, Any]] = None


class UserBadgesResponse(BaseModel):
    """List of all system badges and earned status for a user."""
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    badges: List[BadgeResponse] = Field(default_factory=list)
    total_earned: int = 0


class InviteTokenCreateResponse(BaseModel):
    """Shareable taste-preview invite link details."""
    model_config = ConfigDict(from_attributes=True)

    token: str
    invite_url: str
    inviter_id: uuid.UUID
    inviter_name: Optional[str] = None
    inviter_username: Optional[str] = None
    preview_data: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime


class InvitePreviewResponse(BaseModel):
    """Publicly accessible taste preview for link visitors."""
    model_config = ConfigDict(from_attributes=True)

    token: str
    inviter_id: uuid.UUID
    inviter_name: Optional[str] = None
    inviter_username: Optional[str] = None
    top_genres: List[str] = Field(default_factory=list)
    recent_watched_titles: List[str] = Field(default_factory=list)
    total_watched_count: int = 0
    is_expired: bool = False
    is_converted: bool = False
    created_at: datetime


class ReferralResponse(BaseModel):
    """Details of a single referral conversion."""
    model_config = ConfigDict(from_attributes=True)

    referral_id: uuid.UUID
    inviter_id: uuid.UUID
    invitee_id: uuid.UUID
    invitee_name: Optional[str] = None
    invitee_username: Optional[str] = None
    status: str
    milestone_reached_at: Optional[datetime] = None
    reward_issued: bool
    created_at: datetime


class ReferralStatsResponse(BaseModel):
    """Aggregated referral reward analytics for a user."""
    model_config = ConfigDict(from_attributes=True)

    inviter_id: uuid.UUID
    total_invites_sent: int = 0
    total_conversions: int = 0
    qualified_referrals: int = 0
    referrals: List[ReferralResponse] = Field(default_factory=list)


class PickRoomCreate(BaseModel):
    """Payload to create a new group-pick room."""
    title: str = Field("Movie Night Ballot", max_length=255)
    candidate_title_ids: List[uuid.UUID] = Field(..., min_length=2, max_length=12)
    expires_in_hours: Optional[int] = Field(48, ge=1, le=168)
    constraints_json: Optional[Dict[str, Any]] = None


class CandidateSummary(BaseModel):
    """Candidate title details with vote count and voters."""
    model_config = ConfigDict(from_attributes=True)

    title_id: uuid.UUID
    canonical_title: str
    original_title: Optional[str] = None
    production_year: Optional[int] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    upvotes: int = 0
    voter_names: List[str] = Field(default_factory=list)


class PickRoomDetailResponse(BaseModel):
    """Complete group pick ballot room state and candidate tallies."""
    model_config = ConfigDict(from_attributes=True)

    room_id: uuid.UUID
    host_id: uuid.UUID
    host_name: Optional[str] = None
    host_username: Optional[str] = None
    slug: str
    title: str
    status: str
    winning_title_id: Optional[uuid.UUID] = None
    winning_title_name: Optional[str] = None
    total_votes: int = 0
    candidates: List[CandidateSummary] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    is_expired: bool = False
    created_at: datetime


class PickVoteCreate(BaseModel):
    """Payload to cast a vote for a candidate title."""
    title_id: uuid.UUID
    guest_name: Optional[str] = Field(None, max_length=128)
    voter_fingerprint: Optional[str] = Field(None, max_length=64)
    vote_type: str = Field("UPVOTE", pattern="^(UPVOTE|DOWNVOTE)$")


class PickVoteResponse(BaseModel):
    """Acknowledgement of a recorded vote."""
    vote_id: uuid.UUID
    room_id: uuid.UUID
    title_id: uuid.UUID
    voter_name: str
    vote_type: str
    created_at: datetime


class PickRoomCloseResponse(BaseModel):
    """Result of closing and resolving a group pick ballot."""
    room_id: uuid.UUID
    slug: str
    status: str
    winning_title_id: Optional[uuid.UUID] = None
    winning_title_name: Optional[str] = None
    total_votes_cast: int = 0


class RecapGenreStat(BaseModel):
    """Genre distribution for cinema recap."""
    genre: str
    count: int
    percentage: float


class RecapDirectorStat(BaseModel):
    """Most watched director for cinema recap."""
    director: str
    count: int


class RecapResponse(BaseModel):
    """Aggregated cinema year-in-review / recap snapshot."""
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    user_name: Optional[str] = None
    user_username: Optional[str] = None
    period: str = "yearly"
    year: int
    total_titles_watched: int = 0
    total_runtime_minutes: int = 0
    longest_streak_days: int = 0
    top_genres: List[RecapGenreStat] = Field(default_factory=list)
    top_directors: List[RecapDirectorStat] = Field(default_factory=list)
    favorite_release_era: str = "Contemporary (2020s)"
    circle_percentile: float = 50.0
    cinema_archetype: str = "The Cinephile Explorer"
    archetype_description: str = "A versatile viewer with an insatiable appetite for cinematic journeys across genres."
    generated_at: datetime


# =========================================================================
# Part 2 Phase 3: Watch Clubs & Monthly Challenges Schemas (2.10 - 2.13)
# =========================================================================

class WatchClubCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    avatar_url: Optional[str] = None


class WatchClubResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    club_id: uuid.UUID
    name: str
    slug: str
    created_by: uuid.UUID
    creator_name: Optional[str] = None
    creator_username: Optional[str] = None
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    member_count: int = 1
    created_at: datetime


class ClubMembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    club_id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    user_username: Optional[str] = None
    role: str
    joined_at: datetime


class ClubDetailResponse(BaseModel):
    club: WatchClubResponse
    members: List[ClubMembershipResponse] = Field(default_factory=list)
    taste_profile: Optional[dict] = None


class ClubActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_id: uuid.UUID
    club_id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    activity_type: str
    reference_id: Optional[uuid.UUID] = None
    metadata_json: Optional[dict] = None
    created_at: datetime


class ChallengeCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    challenge_type: str = Field('GLOBAL', pattern='^(GLOBAL|CLUB)$')
    club_id: Optional[uuid.UUID] = None
    criteria_json: Optional[dict] = None
    goal_count: int = Field(1, ge=1)
    starts_at: datetime
    ends_at: datetime


class ChallengeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    challenge_id: uuid.UUID
    title: str
    description: Optional[str] = None
    challenge_type: str
    club_id: Optional[uuid.UUID] = None
    criteria_json: Optional[dict] = None
    goal_count: int
    starts_at: datetime
    ends_at: datetime
    created_at: datetime
    participant_count: int = 0
    # Caller-relative: the requesting user's own progress toward goal_count,
    # if they've joined. None (not 0) means "haven't joined yet" -- the
    # frontend needs to tell that apart from "joined, zero progress logged".
    my_progress: Optional[int] = None
    my_completed: bool = False


class ChallengeParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    challenge_id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    progress: int = 0
    completed: bool = False
    completed_at: Optional[datetime] = None
    joined_at: datetime


class ChallengeDetailResponse(BaseModel):
    challenge: ChallengeResponse
    participants: List[ChallengeParticipantResponse] = Field(default_factory=list)








