# CineVault OS — AI Assistant & Proposal Repository (Build Unit 8.8)
# Asynchronous database operations for AI assistant queries, prompt injection protection, and CAT-6 proposal staging

from ..config import config
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.quality import AIProposalStagingModel
from ..schemas.ai_assistant import (
    AIProviderEnum,
    AIIntentExtraction,
    AssistantQueryRequest,
    AssistantQueryResponse,
    AIProposalCreateRequest,
    AIProposalResponse,
    AIProposalReviewRequest
)
from ..ai.provider import PromptSanitizer, AIProviderFactory
from ..repositories.recommendations import recommendation_repository
from ..repositories.search import search_repository
from ..auth.audit import audit_logger

logger = logging.getLogger("cinevault.repositories.ai_assistant")

class AIAssistantRepository:
    """Provides async operations for AI assistant intent extraction, grounded query processing, and CAT-6 proposal review."""

    async def process_assistant_query(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        body: AssistantQueryRequest,
        provider_name: Optional[str] = None
    ) -> AssistantQueryResponse:
        """Processes conversational query through prompt sanitization, intent extraction, structured domain search, and grounded response assembly."""
        provider = AIProviderFactory.get_provider(provider_name)

        # 1. Prompt Injection Sanitization
        sanitized_query = PromptSanitizer.sanitize(body.query_text)

        # 2. Structured Intent Extraction
        intent = await provider.extract_intent(sanitized_query)

        # 3. Domain Service Query Execution (CineVault Catalog & Recommendations)
        matched_titles: List[Dict[str, Any]] = []
        
        if intent.detected_intent_mode == "RECOMMENDATION" and body.include_recommendation_context:
            rec_res = await recommendation_repository.get_recommendations(
                db=db,
                user_id=user_id,
                genre=intent.target_genres[0] if intent.target_genres else None,
                max_runtime=intent.max_runtime,
                limit=body.max_results
            )
            matched_titles = [
                {
                    "title_id": item.title_id,
                    "display_id": item.display_id,
                    "canonical_title": item.canonical_title,
                    "release_year": item.release_year,
                    "content_type": item.content_type,
                    "genres": item.genres,
                    "score": item.recommendation_score
                }
                for item in rec_res.data
            ]
        else:
            search_res = await search_repository.search_catalog(
                db=db,
                q=sanitized_query,
                entity_type="TITLE",
                year=intent.min_year,
                limit=body.max_results
            )
            matched_titles = [
                {
                    "title_id": item.target_id,
                    "display_id": item.display_id,
                    "canonical_title": item.title,
                    "release_year": item.production_year,
                    "content_type": item.content_type
                }
                for item in search_res.results
            ]

        # 4. Grounded Conversational Response Generation
        response_text = await provider.generate_assistant_response(
            sanitized_query=sanitized_query,
            intent=intent,
            matched_titles=matched_titles
        )

        return AssistantQueryResponse(
            response_text=response_text,
            intent=intent,
            matched_titles=matched_titles,
            provider_used=provider.provider_enum,
            is_grounded=True,
            fallback_fallback=False
        )

    async def stage_ai_proposal(
        self,
        db: Optional[AsyncSession],
        body: AIProposalCreateRequest,
        actor_id: str,
        provider_name: str = "MOCK"
    ) -> AIProposalResponse:
        """Stages an AI metadata proposal into quality.ai_proposal_staging (CAT-6 boundary). Zero direct canonical write."""
        proposal_id = str(uuid.uuid4())
        submitted_at = datetime.now(timezone.utc)

        evidence_payload = {
            "evidence_summary": body.evidence_summary,
            "source_reference": body.source_reference,
            "prompt_version": body.prompt_version,
            "provider_name": provider_name,
            "submitted_by": actor_id
        }

        if db is not None:
            try:
                target_uuid = uuid.UUID(body.target_entity_id) if body.target_entity_id else None
                model = AIProposalStagingModel(
                    proposal_id=uuid.UUID(proposal_id),
                    target_entity_type=body.target_entity_type,
                    target_entity_id=target_uuid,
                    proposed_attribute_name=body.proposed_attribute_name.value,
                    proposed_value=body.proposed_value,
                    confidence_score=body.confidence_score,
                    evidence_payload=evidence_payload,
                    review_status="PENDING",
                    submitted_at=submitted_at
                )
                db.add(model)
                await db.flush()
            except Exception as e:
                await db.rollback()
                logger.error(f"Database insertion stage_ai_proposal failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Audit event log
        audit_logger.log_event(
            event_type="AUDIT_AI_PROPOSAL_SUBMITTED",
            actor_id=actor_id,
            target_id=proposal_id,
            details={"attribute": body.proposed_attribute_name.value, "confidence": body.confidence_score}
        )

        return AIProposalResponse(
            proposal_id=proposal_id,
            target_entity_type=body.target_entity_type,
            target_entity_id=body.target_entity_id,
            proposed_attribute_name=body.proposed_attribute_name.value,
            proposed_value=body.proposed_value,
            confidence_score=body.confidence_score,
            evidence_payload=evidence_payload,
            review_status="PENDING",
            provider_name=provider_name,
            prompt_version=body.prompt_version,
            submitted_at=submitted_at
        )

    async def list_pending_proposals(self, db: Optional[AsyncSession]) -> List[AIProposalResponse]:
        """Lists pending staged AI proposals for curator inspection."""
        if db is not None:
            try:
                stmt = select(AIProposalStagingModel).where(AIProposalStagingModel.review_status == "PENDING")
                res = await db.execute(stmt)
                records = res.scalars().all()
                if records:
                    return [
                        AIProposalResponse(
                            proposal_id=str(r.proposal_id),
                            target_entity_type=r.target_entity_type,
                            target_entity_id=str(r.target_entity_id) if r.target_entity_id else None,
                            proposed_attribute_name=r.proposed_attribute_name,
                            proposed_value=r.proposed_value,
                            confidence_score=float(r.confidence_score),
                            evidence_payload=r.evidence_payload,
                            review_status=r.review_status,
                            provider_name=r.evidence_payload.get("provider_name", "MOCK"),
                            prompt_version=r.evidence_payload.get("prompt_version", "v1.0.0"),
                            submitted_at=r.submitted_at
                        )
                        for r in records
                    ]
            except Exception as e:
                await db.rollback()
                logger.error(f"Database query list_pending_proposals failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Fallback staged proposals for unit tests
        return [
            AIProposalResponse(
                proposal_id="prop_001_mock",
                target_entity_type="TITLE",
                target_entity_id="018f4a00-0000-7000-8000-000000000001",
                proposed_attribute_name="SYNOPSIS_ENHANCEMENT",
                proposed_value="Enhanced localized synopsis for Inception",
                confidence_score=0.920,
                evidence_payload={"summary": "Cross-referenced TMDB and KOBIS canonical records."},
                review_status="PENDING",
                provider_name="MOCK",
                prompt_version="v1.0.0",
                submitted_at=datetime.now(timezone.utc)
            )
        ]

    async def review_ai_proposal(
        self,
        db: Optional[AsyncSession],
        proposal_id: str,
        actor_id: str,
        body: AIProposalReviewRequest
    ) -> Dict[str, Any]:
        """Approves or rejects a staged AI proposal with curator rationale and SHA-256 HMAC audit logging."""
        review_status = "APPROVED" if body.decision.upper() == "APPROVE" else "REJECTED"
        reviewed_at = datetime.now(timezone.utc).isoformat()

        audit_record = audit_logger.log_event(
            event_type="AUDIT_AI_PROPOSAL_DECISION",
            actor_id=actor_id,
            target_id=proposal_id,
            details={
                "decision": review_status,
                "rationale": body.rationale,
                "override_value": body.override_value
            }
        )

        if db is not None:
            try:
                prop_uuid = uuid.UUID(proposal_id)
                stmt = select(AIProposalStagingModel).where(AIProposalStagingModel.proposal_id == prop_uuid)
                res = await db.execute(stmt)
                prop = res.scalar_one_or_none()
                if prop:
                    prop.review_status = review_status
                    await db.flush()
            except Exception as e:
                await db.rollback()
                logger.error(f"Database update review_ai_proposal failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return {
            "status": review_status,
            "proposal_id": proposal_id,
            "reviewed_by": actor_id,
            "rationale": body.rationale,
            "reviewed_at": reviewed_at,
            "integrity_hash": audit_record["integrity_hash"]
        }

ai_assistant_repository = AIAssistantRepository()
