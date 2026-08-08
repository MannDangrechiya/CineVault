# CineVault OS — Offline Sync Protocol Schemas (ADR-004)
# Durable outbox push mutations and delta stream pull responses

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MutationItem(BaseModel):
    mutation_id: str = Field(..., description="Client-generated UUIDv7 mutation key for idempotency")
    mutation_type: str = Field(..., description="Action: CREATE_WATCH_EVENT, SET_RATING, UPSERT_NOTE, UPDATE_TITLE_STATE")
    client_timestamp: str = Field(..., description="ISO-8601 UTC timestamp when mutation was recorded offline")
    payload: Dict[str, Any]

class SyncPushRequest(BaseModel):
    mutations: List[MutationItem]

class SyncPushResponse(BaseModel):
    processed_count: int
    acknowledged_mutation_ids: List[str]
    failed_mutations: Optional[List[Dict[str, Any]]] = []

class SyncPullResponse(BaseModel):
    sync_cursor: str
    has_more: bool
    changes: List[Dict[str, Any]]
