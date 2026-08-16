# CineVault OS — AI Brain & Group Matchmaking Router (v2.0 Module 3)
# Integrates Ollama AI Brain, Vector Group Consensus, and LLM Matchmaking (ADR-004)

import logging
from typing import Optional, List, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.ai import GroupMatchRequest, GroupMatchResponse
from ..auth.dependencies import require_authenticated_user
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.social import social_repository, _resolve_uuid
from ..ai.ollama_client import OllamaClient

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
    4. Retrieves candidate movie titles (currently mocked).
    5. Calls Ollama AI Brain to generate grounded natural language group recommendations.
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

    # 5. Candidate selection (Mocked DB Step before pgvector canonical linkage)
    mock_titles = ["Inception", "Interstellar", "Blade Runner 2049"]

    # 6. Construct strict LLM Prompt
    titles_str = ", ".join(mock_titles)
    prompt = (
        f"You are CineVault Oracle. Recommend these 3 movies: {titles_str} "
        f"based on the group's mood: {body.mood}. Explain why they will like it."
    )

    # 7. Generate chat completion via Ollama AI Brain
    try:
        ollama = OllamaClient()
        ai_response_text = await ollama.generate_chat(prompt=prompt)
    except Exception as exc:
        logger.error(f"Ollama chat generation failed during group matchmaking: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama AI chat generation failed: {str(exc)}",
        ) from exc

    return GroupMatchResponse(
        status="success",
        mood=body.mood,
        group_size=len(all_member_ids),
        group_member_ids=all_member_ids,
        recommended_titles=mock_titles,
        ai_recommendation=ai_response_text,
        group_vector_preview=group_vector[:5] if group_vector else None,
    )
