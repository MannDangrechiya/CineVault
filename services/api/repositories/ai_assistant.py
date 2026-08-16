# CineVault OS — AI Assistant & Proposal Repository (Build Unit 8.8)
# Asynchronous database operations for AI assistant queries, prompt injection protection, and CAT-6 proposal staging

from ..config import config
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.quality import AIProposalStagingModel
from ..models.canonical import (
    TitleModel, EditionModel, GenreModel, CreditModel, PersonModel,
    FranchiseModel, FranchiseEntryModel, ViewingOrderModel, ViewingOrderItemModel, TitleGenreModel
)
from ..schemas.ai_assistant import (
    AIProviderEnum,
    AIIntentExtraction,
    AssistantQueryRequest,
    AssistantQueryResponse,
    AIProposalCreateRequest,
    AIProposalResponse,
    AIProposalReviewRequest,
    TitleComparisonResponse,
    ViewingPlanResponse,
    ViewingPlanItem,
    PersonalStatsExplanationResponse,
)
from ..ai.provider import PromptSanitizer, AIProviderFactory
from ..repositories.recommendations import recommendation_repository
from ..repositories.personal import personal_repository
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
                    "title_id": item.entity_id,
                    "canonical_title": item.primary_name,
                    "score": item.relevance_score
                }
                for item in search_res.data
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
            fallback_applied=False
        )

    async def stage_ai_proposal(
        self,
        db: Optional[AsyncSession],
        actor_id: str,
        body: AIProposalCreateRequest,
        provider_name: Optional[str] = None
    ) -> AIProposalResponse:
        """Stages an AI-generated metadata proposal into CAT-6 quality review table."""
        proposal_id = str(uuid.uuid4())
        submitted_at = datetime.now(timezone.utc)
        provider = AIProviderFactory.get_provider(provider_name)

        if db is not None:
            try:
                proposal_orm = AIProposalStagingModel(
                    proposal_id=uuid.UUID(proposal_id),
                    target_entity_type=body.target_entity_type.upper(),
                    target_entity_id=uuid.UUID(body.target_entity_id) if body.target_entity_id else None,
                    proposed_attribute_name=body.proposed_attribute_name.value,
                    proposed_value=body.proposed_value,
                    confidence_score=body.confidence_score,
                    evidence_payload={
                        "evidence_summary": body.evidence_summary,
                        "source_reference": body.source_reference
                    },
                    review_status="PENDING",
                    provider_name=provider.provider_enum.value,
                    prompt_version=body.prompt_version,
                    submitted_by=actor_id,
                    submitted_at=submitted_at
                )
                db.add(proposal_orm)
                await db.flush()
            except Exception as e:
                await db.rollback()
                logger.error(f"Database write stage_ai_proposal failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return AIProposalResponse(
            proposal_id=proposal_id,
            target_entity_type=body.target_entity_type.upper(),
            target_entity_id=body.target_entity_id,
            proposed_attribute_name=body.proposed_attribute_name.value,
            proposed_value=body.proposed_value,
            confidence_score=body.confidence_score,
            evidence_payload={
                "evidence_summary": body.evidence_summary,
                "source_reference": body.source_reference
            },
            review_status="PENDING",
            provider_name=provider.provider_enum.value,
            prompt_version=body.prompt_version,
            submitted_at=submitted_at
        )

    async def list_pending_proposals(
        self,
        db: Optional[AsyncSession],
        target_entity_type: Optional[str] = None,
        limit: int = 50
    ) -> List[AIProposalResponse]:
        """Lists pending AI proposals for human curator inspection and governance review."""
        if db is not None:
            try:
                stmt = select(AIProposalStagingModel).where(AIProposalStagingModel.review_status == "PENDING")
                if target_entity_type:
                    stmt = stmt.where(AIProposalStagingModel.target_entity_type == target_entity_type.upper())
                stmt = stmt.limit(limit)
                
                res = await db.execute(stmt)
                proposals = res.scalars().all()
                return [
                    AIProposalResponse(
                        proposal_id=str(p.proposal_id),
                        target_entity_type=p.target_entity_type,
                        target_entity_id=str(p.target_entity_id) if p.target_entity_id else None,
                        proposed_attribute_name=p.proposed_attribute_name,
                        proposed_value=p.proposed_value,
                        confidence_score=float(p.confidence_score),
                        evidence_payload=p.evidence_payload if isinstance(p.evidence_payload, dict) else {},
                        review_status=p.review_status,
                        provider_name=p.provider_name,
                        prompt_version=p.prompt_version,
                        submitted_at=p.submitted_at
                    )
                    for p in proposals
                ]
            except Exception as e:
                logger.error(f"Database read list_pending_proposals failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return []

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

    async def compare_titles(
        self,
        db: Optional[AsyncSession],
        title_id_1: str,
        title_id_2: str
    ) -> TitleComparisonResponse:
        """Performs structured comparative cinematic analysis between two canonical works."""
        t1_dict: Dict[str, Any] = {"title_id": title_id_1, "canonical_title": "Title 1"}
        t2_dict: Dict[str, Any] = {"title_id": title_id_2, "canonical_title": "Title 2"}
        shared_genres: List[str] = []
        shared_directors: List[str] = []
        shared_actors: List[str] = []

        if db is not None:
            try:
                u1 = uuid.UUID(title_id_1)
                u2 = uuid.UUID(title_id_2)

                stmt = (
                    select(TitleModel)
                    .options(
                        selectinload(TitleModel.genres),
                        selectinload(TitleModel.editions),
                        selectinload(TitleModel.credits).selectinload(CreditModel.person)
                    )
                    .where(TitleModel.title_id.in_([u1, u2]))
                )
                res = await db.execute(stmt)
                titles = {t.title_id: t for t in res.scalars().all()}

                t1 = titles.get(u1)
                t2 = titles.get(u2)

                if t1:
                    t1_genres = [g.name for g in t1.genres]
                    t1_directors = [c.person.canonical_name for c in t1.credits if c.credit_role_id == "DIRECTOR" and c.person]
                    t1_actors = [c.person.canonical_name for c in t1.credits if c.credit_role_id == "ACTOR" and c.person]
                    t1_dict = {
                        "title_id": str(t1.title_id),
                        "canonical_title": t1.canonical_title,
                        "production_year": t1.production_year,
                        "genres": t1_genres,
                        "directors": t1_directors,
                        "runtime_minutes": t1.editions[0].runtime_minutes if t1.editions else None
                    }

                if t2:
                    t2_genres = [g.name for g in t2.genres]
                    t2_directors = [c.person.canonical_name for c in t2.credits if c.credit_role_id == "DIRECTOR" and c.person]
                    t2_actors = [c.person.canonical_name for c in t2.credits if c.credit_role_id == "ACTOR" and c.person]
                    t2_dict = {
                        "title_id": str(t2.title_id),
                        "canonical_title": t2.canonical_title,
                        "production_year": t2.production_year,
                        "genres": t2_genres,
                        "directors": t2_directors,
                        "runtime_minutes": t2.editions[0].runtime_minutes if t2.editions else None
                    }

                if t1 and t2:
                    shared_genres = list(set(t1_genres).intersection(set(t2_genres)))
                    shared_directors = list(set(t1_directors).intersection(set(t2_directors)))
                    shared_actors = list(set(t1_actors).intersection(set(t2_actors)))
            except Exception as e:
                logger.error("compare_titles failed: %s", e, exc_info=True)

        summary = (
            f"Comparing '{t1_dict.get('canonical_title')}' and '{t2_dict.get('canonical_title')}'. "
            f"Shared genres: {', '.join(shared_genres) if shared_genres else 'None'}. "
            f"Shared directors: {', '.join(shared_directors) if shared_directors else 'None'}."
        )

        return TitleComparisonResponse(
            title_1=t1_dict,
            title_2=t2_dict,
            shared_genres=shared_genres,
            shared_directors=shared_directors,
            shared_actors=shared_actors,
            comparison_summary=summary
        )

    async def build_viewing_plan(
        self,
        db: Optional[AsyncSession],
        franchise_id_or_keyword: str,
        order_mode: str = "RELEASE_ORDER"
    ) -> ViewingPlanResponse:
        """Builds structured marathon viewing plans with calculated runtimes and sequencing."""
        items: List[ViewingPlanItem] = []
        total_runtime = 0
        plan_title = f"Marathon Plan for {franchise_id_or_keyword}"

        if db is not None:
            try:
                try:
                    f_uuid = uuid.UUID(franchise_id_or_keyword)
                    vo_stmt = (
                        select(ViewingOrderModel)
                        .where(
                            and_(
                                ViewingOrderModel.franchise_id == f_uuid,
                                ViewingOrderModel.order_type == order_mode
                            )
                        )
                    )
                    vo_res = await db.execute(vo_stmt)
                    vo = vo_res.scalar_one_or_none()

                    if vo:
                        item_stmt = (
                            select(ViewingOrderItemModel, TitleModel)
                            .join(TitleModel, ViewingOrderItemModel.title_id == TitleModel.title_id)
                            .options(selectinload(TitleModel.editions))
                            .where(ViewingOrderItemModel.viewing_order_id == vo.viewing_order_id)
                            .order_by(ViewingOrderItemModel.position.asc())
                        )
                        res = await db.execute(item_stmt)
                        rows = res.all()
                        for idx, (order_item, t) in enumerate(rows, start=1):
                            runtime = t.editions[0].runtime_minutes if t.editions else 120
                            total_runtime += runtime or 120
                            items.append(
                                ViewingPlanItem(
                                    step=order_item.position or idx,
                                    title_id=str(t.title_id),
                                    canonical_title=t.canonical_title,
                                    production_year=t.production_year,
                                    runtime_minutes=runtime,
                                    reason_for_order=f"Position #{order_item.position} in {order_mode.lower()} sequence."
                                )
                            )
                    else:
                        fe_stmt = (
                            select(FranchiseEntryModel, TitleModel)
                            .join(TitleModel, FranchiseEntryModel.title_id == TitleModel.title_id)
                            .options(selectinload(TitleModel.editions))
                            .where(FranchiseEntryModel.franchise_id == f_uuid)
                            .order_by(TitleModel.production_year.asc())
                        )
                        res = await db.execute(fe_stmt)
                        rows = res.all()
                        for idx, (entry, t) in enumerate(rows, start=1):
                            runtime = t.editions[0].runtime_minutes if t.editions else 120
                            total_runtime += runtime or 120
                            items.append(
                                ViewingPlanItem(
                                    step=idx,
                                    title_id=str(t.title_id),
                                    canonical_title=t.canonical_title,
                                    production_year=t.production_year,
                                    runtime_minutes=runtime,
                                    reason_for_order=f"Position #{idx} in {order_mode.lower()} sequence."
                                )
                            )
                except ValueError:
                    pass
            except Exception as e:
                logger.error("build_viewing_plan failed: %s", e, exc_info=True)

        return ViewingPlanResponse(
            plan_title=plan_title,
            viewing_order=order_mode,
            total_titles=len(items),
            total_runtime_minutes=total_runtime,
            items=items,
            grounded_notes=f"Generated {order_mode} viewing plan with {len(items)} works."
        )

    async def explain_personal_statistics(
        self,
        db: Optional[AsyncSession],
        user_id: str
    ) -> PersonalStatsExplanationResponse:
        """Synthesizes human-readable insights from user personal media statistics while enforcing strict privacy."""
        dash = await personal_repository.get_user_dashboard_metrics(db=db, user_id=user_id)
        
        insights = [
            f"You have watched a total of {dash.total_watch_hours} hours across {dash.watched_count} titles.",
            f"Current active watch streak: {dash.watch_streak_days} consecutive days.",
            f"Explored films and series across {len(dash.countries_explored)} countries and {len(dash.languages_explored)} languages."
        ]
        if dash.average_personal_rating:
            insights.append(f"Your average personal rating across rated titles is {dash.average_personal_rating}/10.")

        summary = (
            f"Personal Media Summary: {dash.total_titles} total titles in library, "
            f"{dash.completed_count} completed, {dash.watching_count} currently watching. "
            f"Total watch time is {dash.total_watch_hours} hours with an active {dash.watch_streak_days}-day streak."
        )

        return PersonalStatsExplanationResponse(
            user_id=user_id,
            summary_text=summary,
            total_titles=dash.total_titles,
            total_watch_hours=dash.total_watch_hours,
            top_genres=[],
            watch_streak_days=dash.watch_streak_days,
            grounded_insights=insights
        )


ai_assistant_repository = AIAssistantRepository()
