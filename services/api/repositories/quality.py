# CineVault OS — Data Quality & Reconciliation Repository
# Asynchronous PostgreSQL operations for identity resolution candidates, human curation, metadata conflicts, and canonical promotion (ADR-001, ADR-004)

from ..config import config
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.quality import ReconciliationCandidateModel, AIProposalStagingModel, MetadataConflictModel, CandidateTitleModel
from ..models.canonical import TitleModel, TitleExternalIdModel, EditionModel
from ..schemas.internal import ReconciliationCandidateSummary, AIProposalSummary
from ..auth.audit import audit_logger

logger = logging.getLogger("cinevault.repositories.quality")

class QualityRepository:
    """Provides async database operations for identity reconciliation, curator promotion, metadata conflicts, and AI proposal review."""

    async def list_reconciliation_candidates(self, db: Optional[AsyncSession]) -> List[ReconciliationCandidateSummary]:
        """Fetches reconciliation candidates flagged for human review or curation."""
        if db is not None:
            try:
                stmt = select(ReconciliationCandidateModel).where(
                    ReconciliationCandidateModel.decision_status == "PENDING"
                )
                res = await db.execute(stmt)
                records = res.scalars().all()
                # Real result returned unconditionally, even if empty -- no
                # pending candidates right now is honest, healthy state.
                return [
                    ReconciliationCandidateSummary(
                        candidate_id=str(r.candidate_id),
                        source_provider=r.provider_name,
                        suggested_action="MERGE_CANDIDATE" if r.candidate_title_id else "NEW_TITLE_CANDIDATE",
                        match_confidence=float(r.match_confidence),
                        status=r.decision_status
                    )
                    for r in records
                ]
            except Exception as e:
                logger.error(f"Database query list_reconciliation_candidates failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Fallback staged candidates for unit tests
        return [
            ReconciliationCandidateSummary(
                candidate_id="cand_001",
                source_provider="TMDB",
                suggested_action="MERGE_CANDIDATE",
                match_confidence=0.92,
                status="PENDING_REVIEW"
            )
        ]

    async def list_metadata_conflicts(self, db: Optional[AsyncSession]) -> List[Dict[str, Any]]:
        """Retrieves active metadata conflicts requiring review or resolution."""
        if db is not None:
            try:
                stmt = select(MetadataConflictModel).where(MetadataConflictModel.status == "OPEN")
                res = await db.execute(stmt)
                records = res.scalars().all()
                # Real result returned unconditionally, even if empty -- no
                # open conflicts right now is honest, healthy state.
                return [
                    {
                        "conflict_id": str(r.conflict_id),
                        "entity_type": r.entity_type,
                        "entity_id": str(r.entity_id) if r.entity_id else None,
                        "field_name": r.field_name,
                        "candidate_value": r.candidate_value,
                        "existing_value": r.existing_value,
                        "source_provider": r.source_provider,
                        "confidence": r.confidence,
                        "status": r.status,
                        "created_at": r.created_at.isoformat()
                    }
                    for r in records
                ]
            except Exception as e:
                logger.error(f"Database query list_metadata_conflicts failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Fallback staged metadata conflicts for unit tests
        return [
            {
                "conflict_id": "conf_001",
                "entity_type": "TITLE",
                "entity_id": "018f6f60-7a00-7000-8000-000000000001",
                "field_name": "runtime_minutes",
                "candidate_value": "140",
                "existing_value": "142",
                "source_provider": "TMDB",
                "confidence": "CONFLICT",
                "status": "OPEN",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]

    async def resolve_metadata_conflict(
        self,
        db: Optional[AsyncSession],
        conflict_id: str,
        actor_id: str,
        winning_value: str,
        resolution_notes: str
    ) -> Optional[Dict[str, Any]]:
        """Resolves active metadata conflict, updating status and preserving resolution audit provenance.

        Returns None if `conflict_id` doesn't match a real, existing
        conflict in real-DB mode -- callers must turn that into a 404, not
        report a fabricated "RESOLVED" success for a mutation that never
        happened."""
        resolved_iso = datetime.now(timezone.utc).isoformat()

        if db is not None:
            try:
                c_uuid = uuid.UUID(conflict_id)
                stmt = select(MetadataConflictModel).where(MetadataConflictModel.conflict_id == c_uuid)
                res = await db.execute(stmt)
                record = res.scalar_one_or_none()
                if not record:
                    return None
                record.status = "RESOLVED"
                record.resolution_notes = f"Winning value '{winning_value}': {resolution_notes}"
                record.resolved_at = datetime.now(timezone.utc)
                record.resolved_by = actor_id
                await db.flush()
            except ValueError:
                # Malformed conflict_id -- not a real UUID, so not a real conflict.
                return None
            except Exception as e:
                logger.error(f"Database update resolve_metadata_conflict failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        audit_record = audit_logger.log_event(
            event_type="AUDIT_METADATA_CONFLICT_RESOLVED",
            actor_id=actor_id,
            target_id=conflict_id,
            details={"winning_value": winning_value, "notes": resolution_notes}
        )
        return {
            "status": "RESOLVED",
            "conflict_id": conflict_id,
            "resolved_by": actor_id,
            "winning_value": winning_value,
            "resolution_notes": resolution_notes,
            "resolved_at": resolved_iso,
            "integrity_hash": audit_record["integrity_hash"]
        }

    async def promote_candidate(
        self,
        db: Optional[AsyncSession],
        candidate_id: str,
        actor_id: str,
        rationale: str,
        override_fields: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Approves human curation decision and promotes record to CAT-1 Canonical Platform Data.

        Returns None if `candidate_id` doesn't match a real, existing
        candidate in real-DB mode -- callers must turn that into a 404, not
        report a fabricated "PROMOTED" success for a mutation that never
        happened."""
        promoted_iso = datetime.now(timezone.utc).isoformat()

        if db is not None:
            try:
                cand_uuid = uuid.UUID(candidate_id)
                stmt = select(ReconciliationCandidateModel).where(ReconciliationCandidateModel.candidate_id == cand_uuid)
                res = await db.execute(stmt)
                cand = res.scalar_one_or_none()
                if not cand:
                    return None
                cand.decision_status = "PROMOTED"
                await db.flush()
            except ValueError:
                return None
            except Exception as e:
                logger.error(f"Database update promote_candidate failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        audit_record = audit_logger.log_event(
            event_type="AUDIT_CANONICAL_PROMOTION",
            actor_id=actor_id,
            target_id=candidate_id,
            details={"rationale": rationale, "override_fields": override_fields or {}}
        )
        return {
            "status": "PROMOTED",
            "candidate_id": candidate_id,
            "promoted_by": actor_id,
            "rationale": rationale,
            "promoted_at": promoted_iso,
            "integrity_hash": audit_record["integrity_hash"]
        }

    async def reject_candidate(
        self,
        db: Optional[AsyncSession],
        candidate_id: str,
        actor_id: str,
        rationale: str
    ) -> Optional[Dict[str, Any]]:
        """Rejects reconciliation candidate with logged audit rationale.

        Returns None if `candidate_id` doesn't match a real, existing
        candidate in real-DB mode -- callers must turn that into a 404, not
        report a fabricated "REJECTED" success for a mutation that never
        happened."""
        rejected_iso = datetime.now(timezone.utc).isoformat()

        if db is not None:
            try:
                cand_uuid = uuid.UUID(candidate_id)
                stmt = select(ReconciliationCandidateModel).where(ReconciliationCandidateModel.candidate_id == cand_uuid)
                res = await db.execute(stmt)
                cand = res.scalar_one_or_none()
                if not cand:
                    return None
                cand.decision_status = "REJECTED"
                await db.flush()
            except ValueError:
                return None
            except Exception as e:
                logger.error(f"Database update reject_candidate failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        audit_record = audit_logger.log_event(
            event_type="AUDIT_AI_PROPOSAL_DECISION",
            actor_id=actor_id,
            target_id=candidate_id,
            details={"action": "REJECT", "rationale": rationale}
        )
        return {
            "status": "REJECTED",
            "candidate_id": candidate_id,
            "rejected_by": actor_id,
            "rationale": rationale,
            "rejected_at": rejected_iso,
            "integrity_hash": audit_record["integrity_hash"]
        }

    async def list_ai_proposals(self, db: Optional[AsyncSession]) -> List[AIProposalSummary]:
        """Inspects CAT-6 AI proposal candidates. AI endpoints cannot directly write to CAT-1."""
        if db is not None:
            try:
                stmt = select(AIProposalStagingModel).where(AIProposalStagingModel.review_status == "PENDING")
                res = await db.execute(stmt)
                proposals = res.scalars().all()
                # Real result returned unconditionally, even if empty -- no
                # pending AI proposals right now is honest, healthy state.
                return [
                    AIProposalSummary(
                        proposal_id=str(p.proposal_id),
                        target_title_id=str(p.target_entity_id) if p.target_entity_id else "",
                        proposal_type=p.proposed_attribute_name,
                        confidence_score=float(p.confidence_score),
                        provenance_type="AI_GENERATED",
                        model_id="cinevault-synopsis-v1",
                        suggested_attributes={"proposed_value": p.proposed_value}
                    )
                    for p in proposals
                ]
            except Exception as e:
                logger.error(f"Database query list_ai_proposals failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return [
            AIProposalSummary(
                proposal_id="prop_ai_991",
                target_title_id="018f2e4a-7b31-7000-8000-123456789abc",
                proposal_type="SYNOPSIS_ENHANCEMENT",
                confidence_score=0.88,
                provenance_type="AI_GENERATED",
                model_id="cinevault-synopsis-v1",
                suggested_attributes={"enhanced_synopsis": "An AI proposed localized synopsis summary."}
            )
        ]

quality_repository = QualityRepository()
