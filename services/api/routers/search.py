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
    year: Optional[int] = Query(None, description="Release year filter"),
    limit: int = Query(25, ge=1, le=100),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Executes unified search query across titles, people, and franchises."""
    return await search_repository.search_catalog(
        db=db,
        q=q,
        entity_type=type,
        content_type=content_type,
        year=year,
        limit=limit
    )
