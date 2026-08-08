# CineVault OS — Canonical Catalog Title & Availability Schemas
# CAT-1 Canonical domain schemas adhering to ADR-001 UUIDv7 identity routing and ADR-002 Release structure

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

class ReleaseSummary(BaseModel):
    release_id: str
    edition_id: str
    release_name: str
    release_type: str = Field(..., description="THEATRICAL, DIGITAL, PHYSICAL_BLURAY, TV_BROADCAST")
    release_date: Optional[str] = None
    country_code: Optional[str] = None

class PlatformSummary(BaseModel):
    platform_id: str
    name: str
    code: str

class PlatformOfferSummary(BaseModel):
    offer_id: str
    platform_id: str
    platform_name: str
    platform_code: str
    title_id: str
    country_code: str
    offer_type: str = Field(..., description="FLATRATE, RENT, BUY, FREE, ADS")
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None

class AvailabilityDiscoveryResponse(BaseModel):
    title_id: str
    display_id: str
    country_code: str
    total_offers: int
    offers: List[PlatformOfferSummary]
    releases: List[ReleaseSummary]
