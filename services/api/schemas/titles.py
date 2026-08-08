# CineVault OS — Canonical Catalog Title Schemas
# CAT-1 Canonical domain schemas adhering to ADR-001 UUIDv7 identity routing

from typing import List, Optional
from pydantic import BaseModel, Field

class TitleSummary(BaseModel):
    id: str = Field(..., description="Canonical UUIDv7 identifier (ADR-001)")
    display_id: str = Field(..., description="Human-readable display identifier (e.g. MOV-000001)")
    canonical_title: str
    original_title: Optional[str] = None
    content_type: str = Field(..., description="Classification: MOVIE, TV_SERIES, ANIME")
    production_year: Optional[int] = None
    origin_country: Optional[str] = None
    has_licensed_artwork: bool = True
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None

class EditionSummary(BaseModel):
    id: str
    title_id: str
    edition_name: str
    runtime_minutes: Optional[int] = None
    format: Optional[str] = None

class TitleDetail(TitleSummary):
    synopsis: Optional[str] = None
    genres: List[str] = []
    primary_edition: Optional[EditionSummary] = None

class TitleLookupResponse(BaseModel):
    id: str
    display_id: str
    canonical_title: str
    lookup_method: str
    matched_external_id: Optional[str] = None

class ProvenanceRecord(BaseModel):
    field_name: str
    source_provider: str
    observation_timestamp: str
    applied_rule_id: str
    is_manually_overridden: bool = False
