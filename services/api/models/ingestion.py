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

class IngestionRunModel(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = {"schema": "ingestion"}

    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    records_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_valid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_conflicted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    summary_notes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

class IngestionItemModel(Base):
    __tablename__ = "ingestion_items"
    __table_args__ = {"schema": "ingestion"}

    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ingestion.ingestion_runs.run_id", ondelete="CASCADE"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("ingestion.raw_payload_capture.raw_payload_id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="RECEIVED", nullable=False)
    candidate_title_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class CandidateTitleModel(Base):
    __tablename__ = "candidate_title"
    __table_args__ = {"schema": "quality"}

    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingestion_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("ingestion.ingestion_runs.run_id", ondelete="SET NULL"), nullable=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    candidate_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    match_status: Mapped[str] = mapped_column(String(32), default="NO_MATCH", nullable=False)
    matched_canonical_title_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="SET NULL"), nullable=True)
    match_score: Mapped[float] = mapped_column(Numeric(4, 3), default=0.0, nullable=False)
    match_rule_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    review_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class FieldProvenanceModel(Base):
    __tablename__ = "field_provenance"
    __table_args__ = {"schema": "quality"}

    provenance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(64), default="TITLE", nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    field_value: Mapped[str] = mapped_column(Text, nullable=False)
    source_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    confidence: Mapped[str] = mapped_column(String(32), default="UNKNOWN", nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED", nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class DataSourceRegistryModel(Base):
    __tablename__ = "data_source_registry"
    __table_args__ = {"schema": "ingestion"}

    source_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    dataset_api: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    official_url: Mapped[str] = mapped_column(String(256), nullable=False)
    license_info: Mapped[str] = mapped_column(String(256), nullable=False)
    attribution_requirement: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    commercial_use_status: Mapped[str] = mapped_column(String(64), nullable=False)
    redistribution_restrictions: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    update_frequency: Mapped[str] = mapped_column(String(64), default="DAILY", nullable=False)
    authentication_requirements: Mapped[str] = mapped_column(String(64), nullable=False)
    regions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    available_fields: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Numeric(3, 2), default=0.50, nullable=False)
    activation_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    authority_role: Mapped[str] = mapped_column(String(64), nullable=False)
    access_status: Mapped[str] = mapped_column(String(32), default="PERMITTED", nullable=False)
    requires_api_key: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scraping_permitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

