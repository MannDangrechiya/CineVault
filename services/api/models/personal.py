# CineVault OS — Personal Schema ORM Models (CAT-2)
# Maps PostgreSQL personal schema tables enforcing ADR-003, ADR-004, and Physical Database Design V1

from datetime import datetime, date
from typing import Optional, Dict, Any, List
import uuid
from sqlalchemy import (
    Column, String, Text, SmallInteger, Integer, Boolean, Date, DateTime, ForeignKey, PrimaryKeyConstraint
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .canonical import Base

class LibraryEntryModel(Base):
    __tablename__ = "library_entry"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "title_id"),
        {"schema": "personal"}
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"))
    added_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    status_override: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

class WatchEventModel(Base):
    __tablename__ = "watch_event"
    __table_args__ = {"schema": "personal"}

    watch_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    edition_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.edition.edition_id", ondelete="RESTRICT"), nullable=True)
    season_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.season.season_id", ondelete="RESTRICT"), nullable=True)
    episode_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.episode.episode_id", ondelete="RESTRICT"), nullable=True)
    watched_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    device_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_tombstoned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class UserTitleStateModel(Base):
    __tablename__ = "user_title_state"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "title_id"),
        {"schema": "personal"}
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"))
    manual_status_override: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_edition_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.edition.edition_id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class RatingModel(Base):
    __tablename__ = "rating"
    __table_args__ = {"schema": "personal"}

    rating_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    rating_value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class NoteModel(Base):
    __tablename__ = "note"
    __table_args__ = {"schema": "personal"}

    note_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class ReviewModel(Base):
    __tablename__ = "review"
    __table_args__ = {"schema": "personal"}

    review_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    review_title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    contains_spoilers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class PersonalDataConflictModel(Base):
    __tablename__ = "personal_data_conflict"
    __table_args__ = {"schema": "personal"}

    conflict_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    conflict_type: Mapped[str] = mapped_column(String(64), nullable=False)
    surviving_title_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=True)
    retired_title_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=True)
    conflicting_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(32), default="UNRESOLVED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class SyncOutboxMutationModel(Base):
    __tablename__ = "sync_outbox_mutation"
    __table_args__ = {"schema": "personal"}

    mutation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    mutation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    client_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    processing_state: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

class SyncCursorStateModel(Base):
    __tablename__ = "sync_cursor_state"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "device_id"),
        {"schema": "personal"}
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    last_synced_mutation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class UserListModel(Base):
    __tablename__ = "user_list"
    __table_args__ = {"schema": "personal"}

    list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    items: Mapped[List["UserListItemModel"]] = relationship("UserListItemModel", back_populates="user_list", cascade="all, delete-orphan")

class UserListItemModel(Base):
    __tablename__ = "user_list_item"
    __table_args__ = {"schema": "personal"}

    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("personal.user_list.list_id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="RESTRICT"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    user_list: Mapped[UserListModel] = relationship("UserListModel", back_populates="items")

