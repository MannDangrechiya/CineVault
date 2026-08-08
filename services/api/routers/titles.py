# CineVault OS — Public Catalog Read Endpoints Router
# Implements CAT-1 title lookups, pagination, display ID redirects, and provenance lineage

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from ..schemas.common import PaginatedResponse, CursorPagination
from ..schemas.titles import TitleSummary, TitleDetail, TitleLookupResponse, ProvenanceRecord, EditionSummary
from ..rate_limiter import enforce_rate_limit
from ..auth.dependencies import get_optional_claims

router = APIRouter(prefix="/v1/titles", tags=["Catalog Titles"])

# Mock database records for API Foundation demonstration
MOCK_TITLES = {
    "018f2e4a-7b31-7000-8000-123456789abc": {
        "id": "018f2e4a-7b31-7000-8000-123456789abc",
        "display_id": "MOV-000001",
        "canonical_title": "Parasite",
        "original_title": "기생충",
        "content_type": "MOVIE",
        "production_year": 2019,
        "origin_country": "KR",
        "synopsis": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
        "genres": ["Drama", "Thriller", "Comedy"],
        "has_licensed_artwork": True,
        "poster_url": "https://cdn.cinevault.org/artwork/posters/mov-000001.jpg",
        "backdrop_url": "https://cdn.cinevault.org/artwork/backdrops/mov-000001.jpg",
        "primary_edition": {
            "id": "018f2e4a-7b31-7000-8000-edition-001",
            "title_id": "018f2e4a-7b31-7000-8000-123456789abc",
            "edition_name": "Theatrical Cut",
            "runtime_minutes": 132,
            "format": "FEATURE"
        }
    }
}

@router.get("", response_model=PaginatedResponse[TitleSummary], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def list_titles(
    content_type: Optional[str] = Query(None, description="Filter by classification: MOVIE, TV_SERIES, ANIME"),
    production_year: Optional[int] = Query(None, description="Filter by release year"),
    origin_country: Optional[str] = Query(None, description="Filter by country of origin"),
    sort: Optional[str] = Query("-production_year,canonical_title", description="Sort order"),
    limit: int = Query(25, ge=1, le=100),
    cursor: Optional[str] = Query(None, description="Cursor token"),
    claims=Depends(get_optional_claims)
):
    """Retrieves paginated list of canonical platform titles (CAT-1)."""
    items = [TitleSummary(**data) for data in MOCK_TITLES.values()]
    return PaginatedResponse(
        data=items,
        pagination=CursorPagination(next_cursor=None, has_more=False, limit=limit)
    )

@router.get("/lookup", response_model=TitleLookupResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def lookup_title(
    display_id: Optional[str] = Query(None, description="Human-readable ID (e.g. MOV-000001)"),
    provider: Optional[str] = Query(None, description="Provider code (TMDB, KOBIS, WIKIDATA)"),
    external_id: Optional[str] = Query(None, description="Provider external ID")
):
    """Resolves secondary display ID or external provider mapping to canonical UUIDv7."""
    if display_id == "MOV-000001" or (provider == "TMDB" and external_id == "496243"):
        return TitleLookupResponse(
            id="018f2e4a-7b31-7000-8000-123456789abc",
            display_id="MOV-000001",
            canonical_title="Parasite",
            lookup_method="DISPLAY_ID" if display_id else "PROVIDER_EXTERNAL_MAPPING",
            matched_external_id=external_id
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No title found matching specified lookup criteria.")

@router.get("/{title_id}", response_model=TitleDetail, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_title_by_id(title_id: str):
    """Retrieves single canonical Title by UUIDv7 primary key (ADR-001)."""
    if title_id in MOCK_TITLES:
        return TitleDetail(**MOCK_TITLES[title_id])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Title entity '{title_id}' not found.")

@router.get("/{title_id}/provenance", response_model=List[ProvenanceRecord], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_title_provenance(title_id: str):
    """Retrieves field provenance lineage explaining the source and rule authority for canonical facts."""
    if title_id not in MOCK_TITLES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Title entity '{title_id}' not found.")
        
    return [
        ProvenanceRecord(
            field_name="canonical_title",
            source_provider="KOBIS",
            observation_timestamp="2026-08-08T12:00:00Z",
            applied_rule_id="RULE-KOREAN-FILM-PRIMARY-KOBIS",
            is_manually_overridden=False
        ),
        ProvenanceRecord(
            field_name="production_year",
            source_provider="TMDB",
            observation_timestamp="2026-08-08T12:00:00Z",
            applied_rule_id="RULE-PRODUCTION-YEAR-EXACT",
            is_manually_overridden=False
        )
    ]
