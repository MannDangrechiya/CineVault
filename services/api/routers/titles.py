# CineVault OS — Public Catalog Read Endpoints Router
# Implements CAT-1 title lookups, pagination, display ID redirects, availability, and provenance lineage (ADR-001, ADR-002)

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.common import PaginatedResponse, CursorPagination
from ..schemas.titles import (
    TitleSummary, TitleDetail, TitleLookupResponse, ProvenanceRecord,
    ReleaseSummary, AvailabilityDiscoveryResponse, MetadataChangeHistoryRecord,
    GenreSummary, CatalogPageResponse
)
from ..rate_limiter import enforce_rate_limit
from ..auth.dependencies import get_optional_claims
from ..database import get_db
from ..repositories.canonical import canonical_repository

router = APIRouter(prefix="/v1/titles", tags=["Catalog Titles"])
catalog_router = APIRouter(prefix="/v1", tags=["Catalog Browsing"])
root_router = APIRouter(prefix="", tags=["Catalog Root"])

@root_router.api_route("/titles", methods=["GET", "HEAD"], response_model=CatalogPageResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
@catalog_router.api_route("/catalog", methods=["GET", "HEAD"], response_model=CatalogPageResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_catalog(
    q: Optional[str] = Query(None, description="Search query string"),
    query: Optional[str] = Query(None, description="Alias for search query string"),
    genre: Optional[str] = Query(None, description="Genre filter (name or ID)"),
    production_year: Optional[int] = Query(None, description="Filter by production release year"),
    year: Optional[int] = Query(None, description="Alias for production year"),
    content_type: Optional[str] = Query(None, description="Filter by classification: MOVIE, TV_SERIES, ANIME"),
    sort: Optional[str] = Query("-production_year,canonical_title", description="Sort order"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves offset-paginated canonical entertainment catalog (CAT-1)."""
    return await canonical_repository.list_catalog(
        db=db,
        q=q,
        query=query,
        genre=genre,
        production_year=production_year,
        year=year,
        content_type=content_type,
        sort=sort,
        limit=limit,
        offset=offset,
    )

@root_router.api_route("/genres", methods=["GET", "HEAD"], response_model=List[GenreSummary], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
@catalog_router.api_route("/genres", methods=["GET", "HEAD"], response_model=List[GenreSummary], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def list_genres(
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves distinct genre taxonomy list from canonical metadata."""
    return await canonical_repository.get_genres(db=db)

@router.api_route("", methods=["GET", "HEAD"], response_model=PaginatedResponse[TitleSummary], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def list_titles(
    content_type: Optional[str] = Query(None, description="Filter by classification: MOVIE, TV_SERIES, ANIME"),
    production_year: Optional[int] = Query(None, description="Filter by release year"),
    origin_country: Optional[str] = Query(None, description="Filter by country of origin"),
    sort: Optional[str] = Query("-production_year,canonical_title", description="Sort order"),
    limit: int = Query(25, ge=1, le=100),
    cursor: Optional[str] = Query(None, description="Cursor token"),
    claims=Depends(get_optional_claims),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves paginated list of canonical platform titles (CAT-1)."""
    items = await canonical_repository.list_titles(
        db=db,
        content_type=content_type,
        production_year=production_year,
        origin_country=origin_country,
        limit=limit,
        cursor=cursor
    )
    return PaginatedResponse(
        data=items,
        pagination=CursorPagination(next_cursor=None, has_more=False, limit=limit)
    )

@router.get("/lookup", response_model=TitleLookupResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def lookup_title(
    display_id: Optional[str] = Query(None, description="Human-readable ID (e.g. MOV-000001)"),
    provider: Optional[str] = Query(None, description="Provider code (TMDB, KOBIS, WIKIDATA)"),
    external_id: Optional[str] = Query(None, description="Provider external ID"),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Resolves secondary display ID or external provider mapping to canonical UUIDv7."""
    res = await canonical_repository.lookup_title(
        db=db,
        display_id=display_id,
        provider=provider,
        external_id=external_id
    )
    if res:
        return res
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No title found matching specified lookup criteria.")

@router.get("/{title_id}", response_model=TitleDetail, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_title_by_id(
    title_id: str,
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves single canonical Title by UUIDv7 primary key (ADR-001)."""
    title = await canonical_repository.get_title_by_id(db=db, title_id=title_id)
    if title:
        return title
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Title entity '{title_id}' not found.")

@router.get("/{title_id}/provenance", response_model=List[ProvenanceRecord], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_title_provenance(
    title_id: str,
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves field provenance lineage explaining the source and rule authority for canonical facts."""
    title = await canonical_repository.get_title_by_id(db=db, title_id=title_id)
    if not title:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Title entity '{title_id}' not found.")
        
    return await canonical_repository.get_provenance(db=db, title_id=title_id)

@router.get("/{title_id}/releases", response_model=List[ReleaseSummary], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_title_releases(
    title_id: str,
    country_code: Optional[str] = Query(None, description="Filter releases by 2-letter ISO country code"),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves distribution release history (theatrical, physical, digital) for title editions (ADR-002)."""
    title = await canonical_repository.get_title_by_id(db=db, title_id=title_id)
    if not title:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Title entity '{title_id}' not found.")

    return await canonical_repository.get_title_releases(db=db, title_id=title_id, country_code=country_code)

@router.get("/{title_id}/availability", response_model=AvailabilityDiscoveryResponse, dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_title_availability(
    title_id: str,
    country_code: str = Query("KR", description="2-letter ISO country code for regional offers"),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Discovers regional platform offers (FLATRATE, RENT, BUY) and active availability windows."""
    title = await canonical_repository.get_title_by_id(db=db, title_id=title_id)
    if not title:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Title entity '{title_id}' not found.")

    return await canonical_repository.get_title_availability(db=db, title_id=title_id, country_code=country_code)

@router.get("/{title_id}/history", response_model=List[MetadataChangeHistoryRecord], dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))])
async def get_title_metadata_history(
    title_id: str,
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves full append-only metadata change history tracking old/new values, actor, timestamp, reason, and confidence."""
    title = await canonical_repository.get_title_by_id(db=db, title_id=title_id)
    if not title:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Title entity '{title_id}' not found.")

    return await canonical_repository.get_metadata_history(db=db, title_id=title_id)
