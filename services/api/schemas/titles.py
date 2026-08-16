# CineVault OS — Canonical Catalog Title & Availability Schemas
# CAT-1 Canonical domain schemas adhering to ADR-001 UUIDv7 identity routing and ADR-002 Release structure

from typing import List, Optional
from pydantic import BaseModel, Field

class TitleAliasSummary(BaseModel):
    alias_name: str
    alias_type: str = Field(default="ALTERNATIVE", description="ALTERNATIVE, TRANSLITERATED, LOCALIZED, WORKING")
    language_code: Optional[str] = None
    country_code: Optional[str] = None

class ThemeSummary(BaseModel):
    theme_id: str
    name: str

class KeywordSummary(BaseModel):
    keyword_id: str
    name: str

class CertificationSummary(BaseModel):
    country_code: str
    certification_code: str
    rating_body: Optional[str] = None
    meaning: Optional[str] = None
    min_age: Optional[int] = None
    note: Optional[str] = None

class CreditSummary(BaseModel):
    credit_id: str
    person_id: str
    person_name: str
    role_name: str
    role_category: str
    character_name: Optional[str] = None
    billing_order: Optional[int] = None

class CompanySummary(BaseModel):
    company_id: str
    company_name: str
    role: str = Field(..., description="STUDIO, NETWORK, DISTRIBUTOR, PRODUCTION")
    country_code: Optional[str] = None

class AwardResultSummary(BaseModel):
    award_name: str
    organization: str
    category_name: str
    year: int
    is_winner: bool

class FestivalParticipationSummary(BaseModel):
    festival_name: str
    year: int
    section_name: Optional[str] = None

class EpisodeSummary(BaseModel):
    id: str
    season_id: str
    episode_number: int
    episode_name: Optional[str] = None
    air_date: Optional[str] = None
    runtime_minutes: Optional[int] = None
    overview: Optional[str] = None

class SeasonSummary(BaseModel):
    id: str
    title_id: str
    season_number: int
    season_name: Optional[str] = None
    overview: Optional[str] = None
    episodes: List[EpisodeSummary] = []

class ReleaseSummary(BaseModel):
    release_id: str
    edition_id: str
    release_name: str
    release_type: str = Field(..., description="THEATRICAL, DIGITAL, PHYSICAL_BLURAY, TV_BROADCAST")
    release_date: Optional[str] = None
    country_code: Optional[str] = None

class EditionSummary(BaseModel):
    id: str
    title_id: str
    edition_name: str
    is_primary: bool = False
    runtime_minutes: Optional[int] = None
    aspect_ratio: Optional[str] = None
    color_format: Optional[str] = None
    sound_mix: Optional[str] = None
    releases: List[ReleaseSummary] = []

class ExternalIdSummary(BaseModel):
    provider_name: str
    external_id: str
    external_url: Optional[str] = None

class TitleSummary(BaseModel):
    id: str = Field(..., description="Canonical UUIDv7 identifier (ADR-001)")
    display_id: str = Field(..., description="Human-readable display identifier (e.g. MOV-000001)")
    canonical_title: str
    original_title: Optional[str] = None
    content_type: str = Field(..., description="Classification: MOVIE, TV_SERIES, ANIME, DOCUMENTARY")
    production_year: Optional[int] = None
    origin_country: Optional[str] = None
    has_licensed_artwork: bool = True
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None

class TitleDetail(TitleSummary):
    tagline: Optional[str] = None
    synopsis: Optional[str] = None
    genres: List[str] = []
    themes: List[ThemeSummary] = []
    keywords: List[KeywordSummary] = []
    aliases: List[TitleAliasSummary] = []
    languages: List[str] = []
    countries: List[str] = []
    certifications: List[CertificationSummary] = []
    credits: List[CreditSummary] = []
    companies: List[CompanySummary] = []
    awards: List[AwardResultSummary] = []
    festival_participations: List[FestivalParticipationSummary] = []
    primary_edition: Optional[EditionSummary] = None
    editions: List[EditionSummary] = []
    seasons: List[SeasonSummary] = []
    external_ids: List[ExternalIdSummary] = []

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
