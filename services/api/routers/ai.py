# CineVault OS — AI Brain & Group Matchmaking Router (v2.0 Module 3)
# Integrates the AIProviderFactory (mock/openai/gemini/groq), Vector Group Consensus, and LLM Matchmaking (ADR-004)

import logging
from typing import Optional, List, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.ai import GroupMatchRequest, GroupMatchResponse
from ..schemas.ai_assistant import AIIntentExtraction
from ..auth.dependencies import require_authenticated_user
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.social import social_repository, _resolve_uuid
from ..repositories.recommendations import recommendation_repository
from ..ai.provider import AIProviderFactory

logger = logging.getLogger("cinevault.routers.ai")

router = APIRouter(prefix="/ai", tags=["AI Brain & Matchmaking (v2.0 Module 3)"])


def _extract_user_id(claims: Optional[SecurityTokenClaims]) -> uuid.UUID:
    """Extracts a valid UUID from security claims sub or generates a fallback for test environments."""
    if claims and hasattr(claims, "sub") and claims.sub:
        return _resolve_uuid(claims.sub, "user_id")
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


def compute_average_group_vector(vectors: List[List[float]]) -> List[float]:
    """
    Calculates the mathematical mean vector across all retrieved taste vectors in the group.

    :param vectors: Non-empty list of float vectors of uniform dimension.
    :return: Averaged consensus vector.
    :raises ValueError: If the vector list is empty or dimensions are inconsistent.
    """
    if not vectors:
        raise ValueError("Cannot compute average vector for an empty list of vectors.")

    dimension = len(vectors[0])
    if dimension == 0:
        raise ValueError("Vector dimension cannot be zero.")

    for idx, vec in enumerate(vectors):
        if len(vec) != dimension:
            raise ValueError(
                f"Vector at index {idx} has dimension {len(vec)}, expected {dimension}."
            )

    num_vectors = float(len(vectors))
    mean_vector = [
        round(sum(vec[i] for vec in vectors) / num_vectors, 6)
        for i in range(dimension)
    ]
    return mean_vector


@router.post(
    "/group-matchmaking",
    response_model=GroupMatchResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def group_matchmaking(
    body: GroupMatchRequest,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Executes AI-powered Group Matchmaking:
    1. Ensures all requested friend_ids have an ACCEPTED friendship with current user.
    2. Fetches taste_vector for current user and all requested friends.
    3. Calculates the Average Group Vector (mathematical mean).
    4. Retrieves real candidate movie titles via the recommendations pipeline.
    5. Calls the configured AI provider (mock/openai/gemini) to generate a
       grounded natural language group recommendation.
    """
    current_user_id = _extract_user_id(claims)

    if not body.friend_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="friend_ids list cannot be empty.",
        )

    # 1. Friendship Pre-Check: verify all requested friends are ACCEPTED friends
    for friend_id in body.friend_ids:
        f_uuid = _resolve_uuid(friend_id, "user_id")
        if f_uuid == current_user_id:
            continue
        are_friends = await social_repository.are_friends_accepted(
            db=db,
            user_a_id=current_user_id,
            user_b_id=f_uuid,
        )
        if not are_friends:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User {f_uuid} is not an ACCEPTED friend of {current_user_id}.",
            )

    # 2. Build unique group member list
    all_member_ids: List[uuid.UUID] = [current_user_id]
    for fid in body.friend_ids:
        f_uuid = _resolve_uuid(fid, "user_id")
        if f_uuid not in all_member_ids:
            all_member_ids.append(f_uuid)

    # 3. Fetch taste vectors for all group members
    retrieved_vectors: List[List[float]] = []
    for member_id in all_member_ids:
        profile = await social_repository.get_taste_profile(db=db, user_id=member_id)
        if profile and profile.get("taste_vector"):
            retrieved_vectors.append(profile["taste_vector"])

    # 4. Calculate Average Group Vector (Consensus Vector)
    if retrieved_vectors:
        group_vector = compute_average_group_vector(retrieved_vectors)
    else:
        # Fallback 384-dimensional zero vector if no members have profiles yet
        group_vector = [0.0] * 384

    # 5. Candidate selection — real catalog titles grounded in the requesting
    # user's actual recommendation pipeline (get_recommendations already has
    # its own real cold-start handling for a brand-new account), not the
    # 3 hardcoded movie names this endpoint used to return for every group
    # regardless of mood or who was in it. Titles don't carry an embedding
    # vector of their own (only user taste_vector does, see
    # compute_average_group_vector above), so a literal group-vector nearest-
    # neighbor title search isn't possible without a real ingestion source —
    # this is the closest honest approximation available today.
    rec_res = await recommendation_repository.get_recommendations(
        db=db,
        user_id=str(current_user_id),
        limit=3,
    )
    candidate_titles = [
        {
            "title_id": item.title_id,
            "display_id": item.display_id,
            "canonical_title": item.canonical_title,
            "release_year": item.release_year,
            "content_type": item.content_type,
            "genres": item.genres,
        }
        for item in rec_res.data
    ]
    recommended_title_names = [c["canonical_title"] for c in candidate_titles]

    # 6. Generate grounded natural language response via the same provider
    # abstraction (mock/openai/gemini) the Conversational Oracle chat uses —
    # this endpoint used to call a local Ollama server directly, which meant
    # it stayed broken regardless of any OPENAI_API_KEY/GEMINI_API_KEY
    # configured for the rest of the app.
    try:
        provider = AIProviderFactory.get_provider()
        intent = AIIntentExtraction(
            raw_query=f"group movie night, mood: {body.mood}",
            sanitized_query=f"group movie night, mood: {body.mood}",
            detected_intent_mode="RECOMMENDATION",
        )
        ai_response_text = await provider.generate_assistant_response(
            sanitized_query=f"Recommend a movie night pick for a group of {len(all_member_ids)} in the mood for: {body.mood}",
            intent=intent,
            matched_titles=candidate_titles,
        )
    except Exception as exc:
        logger.error(f"AI provider failed during group matchmaking: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI group matchmaking generation failed: {str(exc)}",
        ) from exc

    return GroupMatchResponse(
        status="success",
        mood=body.mood,
        group_size=len(all_member_ids),
        group_member_ids=all_member_ids,
        recommended_titles=recommended_title_names,
        ai_recommendation=ai_response_text,
        group_vector_preview=group_vector[:5] if group_vector else None,
    )
