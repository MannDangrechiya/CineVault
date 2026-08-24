# CineVault OS — Social Schema ORM Models (v2.0 Module 1 & 2)
# Implements Social Core, Friendships, Peer Recommendations, and Taste Vector Profiles (ADR-003, ADR-004)

from datetime import datetime, timezone
from typing import Optional, Any
import uuid
from sqlalchemy import (
    String, Text, Float, ForeignKey, DateTime, PrimaryKeyConstraint, Boolean
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from .canonical import Base


class FriendshipModel(Base):
    """
    Represents directional or bidirectional peer relationships between users.
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "friendship"
    __table_args__ = {"schema": "social"}

    friendship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    addressee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING, ACCEPTED, BLOCKED
    trust_score: Mapped[float] = mapped_column(
        Float, default=50.0, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class RecommendationModel(Base):
    """
    Represents peer-to-peer media recommendations subject to state machine lifecycle.
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "recommendation"
    __table_args__ = {"schema": "social"}

    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    title_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical.title.title_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default="SENT", nullable=False
    )  # SENT, ACCEPTED, REJECTED, WATCHED, RATED
    sender_predicted_rating: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    recipient_actual_rating: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    context_note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    sent_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UserTasteProfileModel(Base):
    """
    Represents 384-dimensional dense taste vector profiles for semantic
    taste similarity and peer compatibility matching (all-MiniLM-L6-v2 compatible).
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "user_taste_profile"
    __table_args__ = {"schema": "social"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    taste_vector: Mapped[Optional[Any]] = mapped_column(
        Vector(384), nullable=True
    )
    last_computed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class BadgeDefinitionModel(Base):
    """
    Defines system badge achievements and unlock criteria.
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "badge_definition"
    __table_args__ = {"schema": "social"}

    badge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    icon_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    criteria_json: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UserBadgeModel(Base):
    """
    Represents badges earned by users with timestamp and award context.
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "user_badge"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "badge_id"),
        {"schema": "social"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    badge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social.badge_definition.badge_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    earned_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    context_json: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )


class InviteTokenModel(Base):
    """
    Represents shareable taste-preview invite tokens with baked stats snapshots.
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "invite_token"
    __table_args__ = {"schema": "social"}

    token: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    inviter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    preview_data_json: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    converted_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ReferralModel(Base):
    """
    Tracks viral member referrals and milestone reward qualifications.
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "referral"
    __table_args__ = {"schema": "social"}

    referral_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inviter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    invitee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING, QUALIFIED, REWARDED
    milestone_reached_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    reward_issued: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class PickRoomModel(Base):
    """
    Represents a shareable movie-night voting ballot room with candidates and async voting.
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "pick_room"
    __table_args__ = {"schema": "social"}

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(
        String(255), default="Movie Night Ballot", nullable=False
    )
    constraints_json: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default="OPEN", nullable=False
    )  # OPEN, CLOSED, RESOLVED
    winning_title_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical.title.title_id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class PickRoomCandidateModel(Base):
    """
    Represents candidate titles nominated for a pick room ballot.
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "pick_room_candidate"
    __table_args__ = (
        PrimaryKeyConstraint("room_id", "title_id"),
        {"schema": "social"},
    )

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social.pick_room.room_id", ondelete="CASCADE"),
        nullable=False,
    )
    title_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical.title.title_id", ondelete="CASCADE"),
        nullable=False,
    )


class PickVoteModel(Base):
    """
    Represents an async ballot vote cast by a circle member or guest in a pick room.
    Isolated within the `social` PostgreSQL schema.
    """
    __tablename__ = "pick_vote"
    __table_args__ = {"schema": "social"}

    vote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social.pick_room.room_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    guest_name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True
    )
    voter_fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    title_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical.title.title_id", ondelete="CASCADE"),
        nullable=False,
    )
    vote_type: Mapped[str] = mapped_column(
        String(16), default="UPVOTE", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ── Part 2 Phase 3: Watch Clubs (2.10) ──────────────────────────────────────────

class WatchClubModel(Base):
    """A persistent named group of users who watch and discuss together."""
    __tablename__ = "watch_club"
    __table_args__ = {"schema": "social"}

    club_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    member_count: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class ClubMembershipModel(Base):
    """Membership link between users and watch clubs."""
    __tablename__ = "club_membership"
    __table_args__ = (
        PrimaryKeyConstraint("club_id", "user_id"),
        {"schema": "social"},
    )

    club_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social.watch_club.club_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), default="MEMBER", nullable=False)  # OWNER, ADMIN, MEMBER
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── Part 2 Phase 3: Club Taste DNA (2.11) ───────────────────────────────────────

class ClubTasteProfileModel(Base):
    """Aggregated taste vector for a watch club, computed from member profiles."""
    __tablename__ = "club_taste_profile"
    __table_args__ = {"schema": "social"}

    club_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social.watch_club.club_id", ondelete="CASCADE"),
        primary_key=True,
    )
    taste_vector = mapped_column(Vector(384), nullable=True)
    total_watches: Mapped[int] = mapped_column(default=0, nullable=False)
    top_genres_json: Mapped[Optional[Any]] = mapped_column(JSONB, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── Part 2 Phase 3: Club Activity Feed (2.12) ───────────────────────────────────

class ClubActivityModel(Base):
    """Activity feed entry for a watch club."""
    __tablename__ = "club_activity"
    __table_args__ = {"schema": "social"}

    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    club_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social.watch_club.club_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── Part 2 Phase 3: Monthly Challenges (2.13) ───────────────────────────────────

class ChallengeModel(Base):
    """A time-bound viewing challenge (global or club-scoped)."""
    __tablename__ = "challenge"
    __table_args__ = {"schema": "social"}

    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    challenge_type: Mapped[str] = mapped_column(String(64), default="GLOBAL", nullable=False)
    club_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social.watch_club.club_id", ondelete="CASCADE"),
        nullable=True,
    )
    criteria_json: Mapped[Optional[Any]] = mapped_column(JSONB, default=dict)
    goal_count: Mapped[int] = mapped_column(default=1, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class ChallengeParticipantModel(Base):
    """User participation and progress in a challenge."""
    __tablename__ = "challenge_participant"
    __table_args__ = (
        PrimaryKeyConstraint("challenge_id", "user_id"),
        {"schema": "social"},
    )

    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social.challenge.challenge_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    progress: Mapped[int] = mapped_column(default=0, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )





