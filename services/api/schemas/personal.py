from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ExportFormatEnum(str, Enum):
    JSON = "json"
    CSV = "csv"

class PersonalDataExportResponse(BaseModel):
    schema_version: str = "v1.0.0"
    exported_at: str
    user_id: str
    watch_history: List[Dict[str, Any]]
    ratings: List[Dict[str, Any]]
    user_title_states: List[Dict[str, Any]]
    private_notes: List[Dict[str, Any]]
    custom_lists: List[Dict[str, Any]]

class ImportConflictStrategyEnum(str, Enum):
    KEEP_EXISTING = "KEEP_EXISTING"
    OVERWRITE = "OVERWRITE"
    MERGE = "MERGE"

class ImportItemPayload(BaseModel):
    canonical_title: Optional[str] = None
    production_year: Optional[int] = None
    title_id: Optional[str] = None
    watched_at: Optional[str] = None
    progress_percentage: Optional[float] = 100.0
    rating_value: Optional[int] = None
    is_favorite: Optional[bool] = False
    manual_status_override: Optional[str] = None
    notes: Optional[str] = None

class ImportPreviewRequest(BaseModel):
    items: List[ImportItemPayload]

class ImportConflictItem(BaseModel):
    title_id: str
    canonical_title: str
    field_name: str
    existing_value: Any
    imported_value: Any

class ImportPreviewResponse(BaseModel):
    total_items: int
    matched_titles: int
    unmatched_titles: int
    conflicts_count: int
    conflicts: List[ImportConflictItem]

class ImportApplyRequest(BaseModel):
    items: List[ImportItemPayload]
    conflict_strategy: ImportConflictStrategyEnum = ImportConflictStrategyEnum.KEEP_EXISTING

class ImportApplyResponse(BaseModel):
    applied_count: int
    conflicts_resolved: int
    strategy_applied: str
    applied_at: str

class WatchEventCreate(BaseModel):
    title_id: str = Field(..., description="Target canonical Title UUIDv7")
    edition_id: Optional[str] = None
    season_id: Optional[str] = None
    episode_id: Optional[str] = None
    device_type: Optional[str] = None
    notes: Optional[str] = None
    watched_at: str = Field(..., description="ISO-8601 UTC timestamp")
    progress_percentage: float = Field(100.0, ge=0.0, le=100.0)
    tombstone_reference_id: Optional[str] = Field(None, description="Tombstone reference if correcting a prior event")

class WatchEventResponse(BaseModel):
    id: str
    user_id: str
    title_id: str
    edition_id: Optional[str] = None
    season_id: Optional[str] = None
    episode_id: Optional[str] = None
    device_type: Optional[str] = None
    notes: Optional[str] = None
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

class UserDashboardMetricsResponse(BaseModel):
    total_titles: int
    watched_count: int
    unwatched_count: int
    watching_count: int
    completed_count: int
    dropped_count: int
    favorites_count: int
    total_watch_hours: float
    movies_watched: int
    series_completed: int
    anime_completed: int
    countries_explored: List[str]
    languages_explored: List[str]
    watch_streak_days: int
    monthly_watch_count: int
    annual_watch_count: int
    average_personal_rating: Optional[float]

class HistoryItemResponse(BaseModel):
    id: str
    title_id: str
    canonical_title: str
    production_year: Optional[int] = None
    content_type: str = "MOVIE"
    poster_url: Optional[str] = None
    watched_at: str
    rating_value: Optional[float] = None
    device_type: Optional[str] = None
    progress_percentage: float = 100.0

class HistoryPageResponse(BaseModel):
    items: List[HistoryItemResponse]
    total: int
    limit: int
    offset: int

class WatchlistItemResponse(BaseModel):
    id: str
    title_id: str
    canonical_title: str
    production_year: Optional[int] = None
    content_type: str = "MOVIE"
    poster_url: Optional[str] = None
    added_at: str

class WatchlistPageResponse(BaseModel):
    items: List[WatchlistItemResponse]
    total: int
    limit: int
    offset: int

class CollectionItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    item_count: int = 0
    banner_url: Optional[str] = None
    curator: str = "Personal Curator"
    tags: List[str] = []
    is_private: bool = True
    is_custom: bool = True
    created_at: Optional[str] = None

class CollectionCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    banner_url: Optional[str] = None
    is_private: bool = True

class GenreAffinityItem(BaseModel):
    genre: str
    count: int
    percentage: float

class CreatorAffinityItem(BaseModel):
    name: str
    role: str
    count: int

class MonthlyTrendItem(BaseModel):
    month: str
    count: int
    hours: float

class PersonalAnalyticsResponse(BaseModel):
    total_watch_hours: float
    watched_count: int
    total_titles: int
    monthly_watch_count: int
    annual_watch_count: int
    watch_streak_days: int
    taste_match_score: float
    movies_watched: int
    series_completed: int
    anime_completed: int
    pending_recommendations_count: int
    top_genres: List[GenreAffinityItem]
    top_directors: List[CreatorAffinityItem]
    top_actors: List[CreatorAffinityItem]
    monthly_trend: List[MonthlyTrendItem]

