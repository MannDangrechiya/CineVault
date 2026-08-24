# CineVault OS — Social Schema ORM Models (v2.0 Module 1 & 2)
# Implements Social Core, Friendships, Peer Recommendations, and Taste Vector Profiles (ADR-003, ADR-004)

from datetime import datetime, timezone
from typing import Optional, Any
import uuid
from sqlalchemy import (
    String, Text, Float, ForeignKey, DateTime, PrimaryKeyConstraint
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


