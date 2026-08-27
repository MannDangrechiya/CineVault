# CineVault OS — AI Assistant & Proposal Engine Router (Build Unit 8.8)
# Exposes Public Conversational Assistant Endpoints & Internal CAT-6 Curator AI Proposal Workflow

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.ai_assistant import (
    AIIntentExtraction,
    AssistantQueryRequest,
    AssistantQueryResponse,
    AIProposalCreateRequest,
    AIProposalResponse,
    AIProposalReviewRequest,
    TitleComparisonResponse,
    ViewingPlanResponse,
    PersonalStatsExplanationResponse,
)
from ..auth.dependencies import require_authenticated_user, require_curator
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.ai_assistant import ai_assistant_repository
from ..ai.provider import PromptSanitizer, AIProviderFactory

public_router = APIRouter(prefix="/v1/ai/assistant", tags=["AI Assistant (8.8)"])
internal_router = APIRouter(prefix="/internal/v1/ai/proposals", tags=["AI Proposals (CAT-6 / 8.8)"])

# ------------------------------------------------------------------------
# 1. Public Assistant Endpoints
# ------------------------------------------------------------------------

@public_router.post("/query", response_model=AssistantQueryResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def process_assistant_query(
    body: AssistantQueryRequest,
    provider: Optional[str] = Query(None, description="Optional target AI provider (mock, openai, gemini, groq)"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Processes natural language conversational user request with prompt sanitization, intent extraction, and grounded response assembly."""
    return await ai_assistant_repository.process_assistant_query(
        db=db,
        user_id=claims.sub,
        body=body,
        provider_name=provider
    )

@public_router.post("/intent", response_model=AIIntentExtraction, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def extract_query_intent(
    query_text: str = Query(..., min_length=1, max_length=1000, description="Raw query text"),
    provider: Optional[str] = Query(None, description="Optional target AI provider"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user)
):
    """Extracts structured search/recommendation intent from natural language input."""
    sanitized = PromptSanitizer.sanitize(query_text)
    provider_adapter = AIProviderFactory.get_provider(provider)
    return await provider_adapter.extract_intent(sanitized)

@public_router.get("/compare", response_model=TitleComparisonResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def compare_titles_endpoint(
    title_id_1: str = Query(..., description="First title UUID"),
    title_id_2: str = Query(..., description="Second title UUID"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Compares two canonical titles with shared genres, crew/cast, and comparative summary."""
    return await ai_assistant_repository.compare_titles(
        db=db,
        title_id_1=title_id_1,
        title_id_2=title_id_2
    )

@public_router.get("/viewing-plan", response_model=ViewingPlanResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def generate_viewing_plan_endpoint(
    franchise_id: str = Query(..., description="Franchise UUID or keyword"),
    order_mode: str = Query("RELEASE_ORDER", description="RELEASE_ORDER or CHRONOLOGICAL"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Builds a structured marathon viewing plan for a franchise or cinematic series."""
    return await ai_assistant_repository.build_viewing_plan(
        db=db,
        franchise_id_or_keyword=franchise_id,
        order_mode=order_mode
    )

@public_router.get("/personal-stats", response_model=PersonalStatsExplanationResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def explain_personal_stats_endpoint(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Summarizes and explains the authenticated user's private viewing statistics."""
    return await ai_assistant_repository.explain_personal_statistics(
        db=db,
        user_id=claims.sub
    )

# ------------------------------------------------------------------------
# 2. Internal Curator AI Proposal Endpoints (CAT-6 Boundary)
# ------------------------------------------------------------------------

@internal_router.post("", response_model=AIProposalResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
@internal_router.post("/", response_model=AIProposalResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def stage_ai_proposal(
    body: AIProposalCreateRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Stages an AI metadata proposal into quality.ai_proposal_staging (CAT-6). Direct canonical writes are strictly prohibited."""
    return await ai_assistant_repository.stage_ai_proposal(
        db=db,
        body=body,
        actor_id=claims.sub
    )

@internal_router.get("", response_model=List[AIProposalResponse], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
@internal_router.get("/", response_model=List[AIProposalResponse], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_pending_ai_proposals(
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists pending staged AI proposals for curator inspection."""
    return await ai_assistant_repository.list_pending_proposals(db=db)

@internal_router.post("/{proposal_id}/review", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def review_ai_proposal(
    proposal_id: str,
    body: AIProposalReviewRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Submits curator approve/reject decision for a staged AI proposal with immutable SHA-256 HMAC audit log entry."""
    return await ai_assistant_repository.review_ai_proposal(
        db=db,
        proposal_id=proposal_id,
        actor_id=claims.sub,
        body=body
    )
