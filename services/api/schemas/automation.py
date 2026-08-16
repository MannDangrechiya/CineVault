# CineVault OS — Automation & Webhooks Schemas (v2.0 Module 4)
# Implements Media Server Webhook Payloads (Plex/Jellyfin) and Smart Watchlist categorization

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class MediaServerWebhookPayload(BaseModel):
    """
    Ingests external media server webhooks (Plex, Jellyfin, Emby) to automate watch tracking.
    Enforces required event, Account, and Metadata structures while accommodating provider variations.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    event: str = Field(..., description="Webhook event name (e.g. 'media.scrobble', 'ItemFinished', 'playback.stop')")
    Account: Dict[str, Any] = Field(default_factory=dict, description="Account metadata containing title, username, or id")
    Metadata: Dict[str, Any] = Field(default_factory=dict, description="Media metadata containing title, type, year, guid, or external IDs")

    # Optional provider-specific top-level blocks
    Server: Optional[Dict[str, Any]] = None
    Player: Optional[Dict[str, Any]] = None
    Item: Optional[Dict[str, Any]] = None
    User: Optional[Dict[str, Any]] = None


class SmartWatchlistItem(BaseModel):
    """Represents a canonical title entry categorized within the Smart Watchlist."""
    title_id: str
    canonical_title: str
    runtime_minutes: Optional[int] = None
    production_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    recommendation_note: Optional[str] = None
    recommended_by: Optional[str] = None


class SmartWatchlistResponse(BaseModel):
    """
    Partitioned smart watchlist categories based on canonical metadata (runtime)
    and social graph data (peer recommendations).
    """
    weekend_epics: List[SmartWatchlistItem] = Field(
        default_factory=list,
        description="Epic features with runtime strictly greater than 150 minutes (> 150m)"
    )
    quick_watches: List[SmartWatchlistItem] = Field(
        default_factory=list,
        description="Quick viewing titles with runtime strictly less than 100 minutes (< 100m)"
    )
    friend_recommended: List[SmartWatchlistItem] = Field(
        default_factory=list,
        description="Titles actively recommended by friends with ACCEPTED recommendation status"
    )


class MediaServerWebhookResponse(BaseModel):
    """Standardized response for media server webhook ingestion and social state transition hooks."""
    status: str = "success"
    event: str
    title_id: Optional[str] = None
    canonical_title: Optional[str] = None
    user_id: str
    watch_event_id: Optional[str] = None
    social_recommendation_updated: bool = False
    recommendation_id: Optional[str] = None
    message: str
