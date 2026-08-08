# CineVault OS — Personal Data Schemas (CAT-2)
# User personal logs, watch events (append-only), ratings, notes, reviews & conflicts (ADR-003)

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class WatchEventCreate(BaseModel):
    title_id: str = Field(..., description="Target canonical Title UUIDv7")
    edition_id: Optional[str] = None
    watched_at: str = Field(..., description="ISO-8601 UTC timestamp")
    progress_percentage: float = Field(100.0, ge=0.0, le=100.0)
    tombstone_reference_id: Optional[str] = Field(None, description="Tombstone reference if correcting a prior event")

class WatchEventResponse(BaseModel):
    id: str
    user_id: str
    title_id: str
    edition_id: Optional[str] = None
    watched_at: str
    progress_percentage: float
    created_at: str

class UserTitleStateResponse(BaseModel):
    title_id: str
    derived_status: str  # Read-only calculated
    manual_status_override: Optional[str] = None  # COMPLETED, WATCHING, PLAN_TO_WATCH, DROPPED
    is_favorite: bool = False
    preferred_edition_id: Optional[str] = None
    updated_at: str

class UserTitleStateUpdate(BaseModel):
    manual_status_override: Optional[str] = None
    is_favorite: Optional[bool] = None
    preferred_edition_id: Optional[str] = None

class RatingCreate(BaseModel):
    title_id: str
    rating_value: int = Field(..., ge=1, le=10)

class RatingResponse(BaseModel):
    id: str
    title_id: str
    rating_value: int
    updated_at: str

class NoteCreate(BaseModel):
    title_id: str
    note_text: str

class NoteResponse(BaseModel):
    id: str
    title_id: str
    note_text: str
    updated_at: str

class ReviewCreate(BaseModel):
    title_id: str
    review_title: str
    review_text: str
    is_public: bool = False

class ReviewResponse(BaseModel):
    id: str
    title_id: str
    review_title: str
    review_text: str
    is_public: bool
    created_at: str

class PersonalDataConflictResponse(BaseModel):
    conflict_id: str
    conflict_type: str
    affected_title_id: str
    conflict_details: Dict[str, Any]
    created_at: str

class PersonalDataConflictResolveRequest(BaseModel):
    chosen_option_id: str
    resolution_note: Optional[str] = None
