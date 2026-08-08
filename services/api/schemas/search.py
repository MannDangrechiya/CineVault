# CineVault OS — Unified Search Schemas

from typing import List, Optional
from pydantic import BaseModel

class SearchResultItem(BaseModel):
    id: str
    display_id: str
    canonical_title: str
    entity_type: str  # TITLE, PERSON, FRANCHISE, AWARD, FESTIVAL
    content_type: Optional[str] = None
    production_year: Optional[int] = None
    relevance_score: float

class SearchResponse(BaseModel):
    query: str
    total_hits: int
    results: List[SearchResultItem]
