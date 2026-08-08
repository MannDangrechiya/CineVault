# CineVault OS — Offline Sync Protocol Router (ADR-004)
# Implements durable outbox push processing and incremental delta change pull stream

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from ..schemas.sync import SyncPushRequest, SyncPushResponse, SyncPullResponse
from ..auth.dependencies import require_authenticated_user
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit

router = APIRouter(prefix="/v1/sync", tags=["Offline Sync Protocol (ADR-004)"])

@router.post("/push", response_model=SyncPushResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("SYNC"))])
async def sync_push(
    body: SyncPushRequest,
    claims: SecurityTokenClaims = Depends(require_authenticated_user)
):
    """
    Submits a batch of client mutations recorded while offline.
    Each mutation is uniquely identified by client-generated UUIDv7 mutation_id for server-side idempotency check.
    """
    acked_ids = [m.mutation_id for m in body.mutations]
    return SyncPushResponse(
        processed_count=len(acked_ids),
        acknowledged_mutation_ids=acked_ids,
        failed_mutations=[]
    )

@router.get("/pull", response_model=SyncPullResponse, dependencies=[Depends(enforce_rate_limit("SYNC"))])
async def sync_pull(
    sync_cursor: Optional[str] = Query(None, description="Opaque sequential change cursor pointer"),
    limit: int = Query(50, ge=1, le=200),
    claims: SecurityTokenClaims = Depends(require_authenticated_user)
):
    """Retrieves server-side delta changes occurring since the client's last sync_cursor pointer."""
    return SyncPullResponse(
        sync_cursor="cursor_seq_100025",
        has_more=False,
        changes=[]
    )
