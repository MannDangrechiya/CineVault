# CineVault OS — Quality Schema ORM Models
# Maps PostgreSQL quality schema tables enforcing ADR-001, ADR-004, and Physical Database Design V1

from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from sqlalchemy import Column, String, Text, SmallInteger, Integer, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .canonical import Base
from .ingestion import CandidateTitleModel


class ReconciliationCandidateModel(Base):
    __tablename__ = "reconciliation_candidate"
    __table_args__ = {"schema": "quality"}

    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    candidate_title_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("canonical.title.title_id", ondelete="CASCADE"), nullable=True)
    match_confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    match_rule_id: Mapped[str] = mapped_column(String(128), nullable=False)
    decision_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class AIProposalStagingModel(Base):
    __tablename__ = "ai_proposal_staging"
    __table_args__ = {"schema": "quality"}

    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    proposed_attribute_name: Mapped[str] = mapped_column(String(64), nullable=False)
    proposed_value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    evidence_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

class MetadataConflictModel(Base):
    __tablename__ = "metadata_conflict"
    __table_args__ = {"schema": "quality"}

    conflict_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(64), default="TITLE", nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    candidate_value: Mapped[str] = mapped_column(Text, nullable=False)
    existing_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[str] = mapped_column(String(32), default="CONFLICT", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

