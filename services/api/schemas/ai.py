# CineVault OS — AI Module Schemas (v2.0 Module 3)
# Defines schemas for AI Provider integration, Group Matchmaking, and Vector operations

from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class GroupMatchRequest(BaseModel):
    """Request payload for group movie matchmaking."""
    friend_ids: List[uuid.UUID] = Field(
        ...,
        min_length=1,
        description="List of friend UUIDs to include in group matchmaking session",
    )
    mood: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language mood or theme for the group watch session (e.g. 'sci-fi adventure')",
    )


class GroupMatchResponse(BaseModel):
    """Response payload returned by the AI Group Matchmaking engine."""
    model_config = ConfigDict(from_attributes=True)

    status: str = "success"
    mood: str
    group_size: int
    group_member_ids: List[uuid.UUID]
    recommended_titles: List[str]
    ai_recommendation: str
    group_vector_preview: Optional[List[float]] = None
