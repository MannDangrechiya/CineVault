# CineVault OS — Recommendation Engine Schemas (CAT-1 & CAT-2 Boundary)
# Specification for Recommendation Foundation Engine (Build Unit 8.7)

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class RecommendationModeEnum(str, Enum):
    TONIGHT = "tonight"
    UNDER_90 = "under_90"
    FAVORITE_DIRECTORS = "favorite_directors"
    HIDDEN_GEMS = "hidden_gems"
    BECAUSE_YOU_LIKED = "because_you_liked"
    COLD_START = "cold_start"

class ColdStartPreferenceInput(BaseModel):
    preferred_genres: Optional[List[str]] = Field(default=None, description="Preferred genre names/IDs")
    preferred_countries: Optional[List[str]] = Field(default=None, description="Preferred 2-letter country codes")
    preferred_languages: Optional[List[str]] = Field(default=None, description="Preferred language codes")
    min_release_year: Optional[int] = Field(default=None, ge=1888, description="Minimum release year")
    max_release_year: Optional[int] = Field(default=None, le=2100, description="Maximum release year")

class GroundedExplanation(BaseModel):
    explanation_text: str = Field(..., description="Factually grounded justification without LLM hallucination")
    matched_genres: List[str] = Field(default_factory=list, description="Matched genre names")
    matched_directors: List[str] = Field(default_factory=list, description="Matched director names")
    matched_actors: List[str] = Field(default_factory=list, description="Matched actor names")
    seed_title_name: Optional[str] = Field(None, description="Seed title name if 'because_you_liked' mode")
    user_rating_applied: Optional[int] = Field(None, description="User's rating value on seed title")

class RecommendationItemResponse(BaseModel):
    title_id: str = Field(..., description="Canonical title UUID")
    display_id: str = Field(..., description="User-facing canonical display ID")
    canonical_title: str = Field(..., description="Primary canonical title name")
    original_title: Optional[str] = Field(None, description="Original language title name")
    release_year: Optional[int] = Field(None, description="Primary release year")
    content_type: str = Field(..., description="MOVIE or SHOW")
    runtime_minutes: Optional[int] = Field(None, description="Runtime duration in minutes")
    vote_average: float = Field(0.0, description="Catalog aggregate vote average")
    genres: List[str] = Field(default_factory=list, description="Associated canonical genres")
    directors: List[str] = Field(default_factory=list, description="Associated directors")
    recommendation_score: float = Field(..., ge=0.0, le=100.0, description="Calculated recommendation score (0-100)")
    is_available: bool = Field(True, description="True if available on known release/platform")
    explanation: GroundedExplanation = Field(..., description="Structured grounded rationale")

class RecommendationListResponse(BaseModel):
    mode: RecommendationModeEnum = Field(..., description="Applied recommendation mode")
    total: int = Field(..., ge=0, description="Total recommendation items returned")
    is_cold_start: bool = Field(False, description="True if recommendations were generated using cold-start rules")
    data: List[RecommendationItemResponse] = Field(..., description="List of ranked recommendation items")

class RecommendationExplainRequest(BaseModel):
    title_id: str = Field(..., description="Target canonical title UUID for explanation")
    seed_title_id: Optional[str] = Field(None, description="Optional seed title UUID if checking similarity")

class RecommendationExplainResponse(BaseModel):
    title_id: str = Field(..., description="Target canonical title UUID")
    canonical_title: str = Field(..., description="Target title name")
    explanation: GroundedExplanation = Field(..., description="Grounded rationale")
    score_breakdown: Dict[str, float] = Field(..., description="Transparent breakdown of scoring factors")

class GenreAffinity(BaseModel):
    genre: str
    weight: float
    watched_count: int
    avg_rating: Optional[float] = None

class ThemeAffinity(BaseModel):
    theme: str
    weight: float
    watched_count: int

class CreatorAffinity(BaseModel):
    person_name: str
    role: str
    weight: float
    titles_watched: int

class TasteProfileResponse(BaseModel):
    top_genres: List[GenreAffinity]
    top_themes: List[ThemeAffinity]
    top_directors: List[CreatorAffinity]
    top_actors: List[CreatorAffinity]
    favorite_decades: List[str]
    preferred_languages: List[str]
    preferred_countries: List[str]
    average_preferred_runtime: Optional[int]
    completion_rate: float
    abandon_rate: float
    total_rated_count: int
    taste_diversity_score: float
