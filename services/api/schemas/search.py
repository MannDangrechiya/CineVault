# CineVault OS — Unified Search Schemas

from typing import List, Optional
from pydantic import BaseModel

class SearchResultItem(BaseModel):
    id: str
    display_id: str
    canonical_title: str
    original_title: Optional[str] = None
    poster_url: Optional[str] = None
    entity_type: str  # TITLE, PERSON, FRANCHISE, AWARD, FESTIVAL
    content_type: Optional[str] = None
    production_year: Optional[int] = None
    relevance_score: float

class SearchResponse(BaseModel):
    query: str
    total_hits: int
    page: int = 1
    total_pages: int = 1
    results: List[SearchResultItem]
