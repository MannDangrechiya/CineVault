# CineVault OS — AI Assistant & Proposal Engine Schemas (CAT-6 Boundary)
# Specification for AI Proposal / Assistant Foundation Engine (Build Unit 8.8)

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class AIProviderEnum(str, Enum):
    MOCK = "mock"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROQ = "groq"
    GROK = "grok"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"

class ProposalTypeEnum(str, Enum):
    SYNOPSIS_ENHANCEMENT = "SYNOPSIS_ENHANCEMENT"
    TAGLINE_SUGGESTION = "TAGLINE_SUGGESTION"
    GENRE_MAPPING = "GENRE_MAPPING"
    PERSON_ALIAS = "PERSON_ALIAS"
    RELEASE_WINDOW = "RELEASE_WINDOW"

class AIIntentExtraction(BaseModel):
    raw_query: str = Field(..., description="Original query text")
    sanitized_query: str = Field(..., description="Query stripped of prompt injection tokens")
    target_genres: List[str] = Field(default_factory=list, description="Extracted genre filters")
    target_directors: List[str] = Field(default_factory=list, description="Extracted director names")
    target_actors: List[str] = Field(default_factory=list, description="Extracted actor names")
    min_year: Optional[int] = Field(None, ge=1888, le=2100, description="Extracted minimum release year")
    max_year: Optional[int] = Field(None, ge=1888, le=2100, description="Extracted maximum release year")
    max_runtime: Optional[int] = Field(None, ge=1, le=1000, description="Extracted max runtime in minutes")
    preferred_content_type: Optional[str] = Field(None, description="MOVIE, SHOW, or ALL")
    detected_intent_mode: str = Field("GENERAL_SEARCH", description="SEARCH, RECOMMENDATION, SIMILARITY, or GENERAL_SEARCH")

class AssistantQueryRequest(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=1000, description="User natural language request text")
    include_recommendation_context: bool = Field(True, description="Whether to include user taste context")
    max_results: int = Field(5, ge=1, le=20, description="Max titles to present in response")

class AssistantQueryResponse(BaseModel):
    response_text: str = Field(..., description="Grounded natural language conversational response")
    intent: AIIntentExtraction = Field(..., description="Validated structured intent breakdown")
    matched_titles: List[Dict[str, Any]] = Field(default_factory=list, description="Matched catalog title summaries")
    provider_used: AIProviderEnum = Field(..., description="AI provider backend executed")
    is_grounded: bool = Field(True, description="True if response is factually grounded in CineVault catalog")
    fallback_applied: bool = Field(False, description="True if provider fallback occurred")

class AIProposalCreateRequest(BaseModel):
    target_entity_type: str = Field(..., description="Target domain entity (TITLE, PERSON, RELEASE)")
    target_entity_id: Optional[str] = Field(None, description="Target entity UUID if updating existing record")
    proposed_attribute_name: ProposalTypeEnum = Field(..., description="Proposed metadata attribute")
    proposed_value: str = Field(..., min_length=1, description="Proposed textual attribute value")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence score (0.000 - 1.000)")
    evidence_summary: str = Field(..., description="Factual evidence grounding proposal")
    source_reference: Optional[str] = Field(None, description="Source payload ID or external reference")
    prompt_version: str = Field("v1.0.0", description="Prompt template version identifier")

class AIProposalResponse(BaseModel):
    proposal_id: str = Field(..., description="CAT-6 proposal staging UUID")
    target_entity_type: str = Field(..., description="Target domain entity")
    target_entity_id: Optional[str] = Field(None, description="Target entity UUID")
    proposed_attribute_name: str = Field(..., description="Proposed metadata attribute")
    proposed_value: str = Field(..., description="Proposed attribute value")
    confidence_score: float = Field(..., description="Model confidence score")
    evidence_payload: Dict[str, Any] = Field(..., description="Structured evidence payload")
    review_status: str = Field(..., description="PENDING, APPROVED, or REJECTED")
    provider_name: str = Field(..., description="Originating AI provider")
    prompt_version: str = Field(..., description="Prompt version used")
    submitted_at: datetime = Field(..., description="Proposal submission timestamp")

class AIProposalReviewRequest(BaseModel):
    decision: str = Field(..., description="APPROVE or REJECT")
    rationale: str = Field(..., min_length=3, description="Curator decision rationale for audit trail")
    override_value: Optional[str] = Field(None, description="Optional curator value override during approval")

class TitleComparisonResponse(BaseModel):
    title_1: Dict[str, Any]
    title_2: Dict[str, Any]
    shared_genres: List[str]
    shared_directors: List[str]
    shared_actors: List[str]
    comparison_summary: str

class ViewingPlanItem(BaseModel):
    step: int
    title_id: str
    canonical_title: str
    production_year: Optional[int] = None
    runtime_minutes: Optional[int] = None
    reason_for_order: str

class ViewingPlanResponse(BaseModel):
    plan_title: str
    viewing_order: str
    total_titles: int
    total_runtime_minutes: int
    items: List[ViewingPlanItem]
    grounded_notes: str

class PersonalStatsExplanationResponse(BaseModel):
    user_id: str
    summary_text: str
    total_titles: int
    total_watch_hours: float
    top_genres: List[str]
    watch_streak_days: int
    grounded_insights: List[str]
