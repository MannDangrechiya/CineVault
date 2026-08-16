# CineVault OS — Recommendation Engine Router (Build Unit 8.7)
# Public & Personal Recommendation endpoints for CineVault OS

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.recommendations import (
    RecommendationModeEnum,
    ColdStartPreferenceInput,
    RecommendationListResponse,
    RecommendationExplainRequest,
    RecommendationExplainResponse,
    TasteProfileResponse
)
from ..auth.dependencies import require_authenticated_user
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.recommendations import recommendation_repository

router = APIRouter(prefix="/v1/recommendations", tags=["Recommendation Foundation (8.7)"])

@router.get("/taste-profile", response_model=TasteProfileResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_user_taste_profile(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves user's learned cinematic taste profile (genre affinities, directors, actors, decades, runtime preferences)."""
    return await recommendation_repository.get_taste_profile(db=db, user_id=claims.sub)

@router.get("", response_model=RecommendationListResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
@router.get("/", response_model=RecommendationListResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_personalized_recommendations(
    mode: RecommendationModeEnum = Query(RecommendationModeEnum.TONIGHT, description="Recommendation mode"),
    max_runtime: Optional[int] = Query(None, description="Maximum runtime in minutes filter"),
    genre: Optional[str] = Query(None, description="Genre filter"),
    available_only: bool = Query(True, description="Only return titles available on active releases"),
    include_watched: bool = Query(False, description="Whether to include already watched titles"),
    seed_title_id: Optional[str] = Query(None, description="Seed title UUID for 'because_you_liked' mode"),
    limit: int = Query(10, ge=1, le=50, description="Maximum recommendation items to return"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves ranked personalized recommendations using governed hybrid pipeline (Candidate Generation -> Hard Filters -> Similarity -> Personal Taste -> Context -> Ranking -> Grounded Explanation)."""
    return await recommendation_repository.get_recommendations(
        db=db,
        user_id=claims.sub,
        mode=mode,
        max_runtime=max_runtime,
        genre=genre,
        available_only=available_only,
        include_watched=include_watched,
        seed_title_id=seed_title_id,
        limit=limit
    )

@router.post("/cold-start", response_model=RecommendationListResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_cold_start_recommendations(
    body: ColdStartPreferenceInput,
    limit: int = Query(10, ge=1, le=50, description="Maximum recommendation items to return"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Generates cold-start recommendations using explicit user preferences, curated canonical collections, and content similarity."""
    return await recommendation_repository.get_recommendations(
        db=db,
        user_id=claims.sub,
        mode=RecommendationModeEnum.COLD_START,
        cold_start_input=body,
        limit=limit
    )

@router.get("/similar/{title_id}", response_model=RecommendationListResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_similar_title_recommendations(
    title_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum similar items to return"),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves content-similar title recommendations based on target title attributes (genres, directors, cast)."""
    return await recommendation_repository.get_similar_titles(
        db=db,
        user_id=claims.sub,
        title_id=title_id,
        limit=limit
    )

@router.post("/explain", response_model=RecommendationExplainResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def explain_recommendation(
    body: RecommendationExplainRequest,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Generates transparent score breakdown and factually grounded explanation for a recommended title."""
    return await recommendation_repository.explain_recommendation(
        db=db,
        user_id=claims.sub,
        title_id=body.title_id,
        seed_title_id=body.seed_title_id
    )
