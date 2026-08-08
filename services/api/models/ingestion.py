# CineVault OS — Ingestion & Quality Staging ORM Models
# Maps PostgreSQL ingestion and quality schema tables enforcing ADR-001, ADR-004, and Physical Database Design V1

from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from sqlalchemy import Column, String, Text, SmallInteger, Integer, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .canonical import Base

class RawPayloadCaptureModel(Base):
    __tablename__ = "raw_payload_capture"
    __table_args__ = {"schema": "ingestion"}

    raw_payload_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    external_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    external_entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    http_status_code: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    acquired_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

class ProviderCheckpointModel(Base):
    __tablename__ = "provider_checkpoint"
    __table_args__ = {"schema": "ingestion"}

    provider_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_successful_sync_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    last_processed_cursor: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    status_flag: Mapped[str] = mapped_column(String(32), default="HEALTHY", nullable=False)

class QuarantineRecordModel(Base):
    __tablename__ = "quarantine_record"
    __table_args__ = {"schema": "quality"}

    quarantine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_payload_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("ingestion.raw_payload_capture.raw_payload_id", ondelete="SET NULL"), nullable=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    failure_category: Mapped[str] = mapped_column(String(64), nullable=False)
    diagnostic_details: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    detected_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class NormalizedTitleStagingModel(Base):
    __tablename__ = "normalized_title_staging"
    __table_args__ = {"schema": "quality"}

    staging_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_payload_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("ingestion.raw_payload_capture.raw_payload_id", ondelete="CASCADE"), nullable=True)
    normalized_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    normalization_status: Mapped[str] = mapped_column(String(32), default="NORMALIZED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
