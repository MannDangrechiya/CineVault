# CineVault OS — Unified Search Router
# Script-normalized multi-entity search endpoint utilizing PostgreSQL pg_trgm & FTS (ADR-001)

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.search import SearchResponse, SearchResultItem
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.search import search_repository

router = APIRouter(prefix="/v1/search", tags=["Search"])

@router.get("", response_model=SearchResponse, dependencies=[Depends(enforce_rate_limit("SEARCH"))])
async def search_catalog(
    q: str = Query(..., min_length=1, description="Raw query string (script-normalized, unicode-folded)"),
    type: Optional[str] = Query("ALL", description="Entity filter: TITLE, PERSON, FRANCHISE, AWARD, FESTIVAL, ALL"),
    content_type: Optional[str] = Query(None, description="Title classification filter"),
    genre: Optional[str] = Query(None, description="Genre taxonomy filter"),
    theme: Optional[str] = Query(None, description="Theme taxonomy filter"),
    country: Optional[str] = Query(None, description="Country code filter (e.g. KR, US, JP)"),
    year: Optional[int] = Query(None, description="Release year filter"),
    limit: int = Query(25, ge=1, le=100),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Executes unified search query across titles, aliases, people, and franchises."""
    return await search_repository.search_catalog(
        db=db,
        q=q,
        entity_type=type,
        content_type=content_type,
        genre=genre,
        theme=theme,
        country=country,
        year=year,
        limit=limit,
        page=page
    )
