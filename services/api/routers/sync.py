# CineVault OS — Offline Sync Protocol Router (ADR-004)
# Implements durable outbox push processing, server-side idempotency, and incremental delta change pull streams

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.sync import SyncPushRequest, SyncPushResponse, SyncPullResponse
from ..auth.dependencies import require_authenticated_user
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.sync import sync_repository

router = APIRouter(prefix="/v1/sync", tags=["Offline Sync Protocol (ADR-004)"])

@router.post("/push", response_model=SyncPushResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("SYNC"))])
async def sync_push(
    body: SyncPushRequest,
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """
    Submits a batch of client mutations recorded while offline.
    Each mutation is uniquely identified by client-generated UUIDv7 mutation_id for server-side idempotency check.
    """
    return await sync_repository.process_push_mutations(
        db=db,
        user_id=claims.sub,
        mutations=body.mutations
    )

@router.get("/pull", response_model=SyncPullResponse, dependencies=[Depends(enforce_rate_limit("SYNC"))])
async def sync_pull(
    sync_cursor: Optional[str] = Query(None, description="Opaque sequential change cursor pointer"),
    limit: int = Query(50, ge=1, le=200),
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves server-side delta changes occurring since the client's last sync_cursor pointer."""
    return await sync_repository.get_delta_pull_changes(
        db=db,
        user_id=claims.sub,
        sync_cursor=sync_cursor,
        limit=limit
    )
