# CineVault OS — Social Schema ORM Models (v2.0 Module 1)
# Implements Social Core, Friendships, and Peer Recommendations (ADR-003, ADR-004)

from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import (
    String, Text, Float, ForeignKey, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
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
