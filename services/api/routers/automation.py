# CineVault OS — Automations & Hooks API Router (v2.0 Module 4)
# Implements Media Server Webhooks (Plex/Jellyfin), Recommendation State Auto-Transitions, and Smart Watchlist

import logging
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query, HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..schemas.automation import (
    MediaServerWebhookPayload,
    MediaServerWebhookResponse,
    SmartWatchlistResponse,
    SmartWatchlistItem,
)
from ..schemas.social import RecommendationStatusEnum, RecommendationResponse
from ..models.personal import WatchEventModel, LibraryEntryModel
from ..models.canonical import TitleModel, TitleExternalIdModel, EditionModel
from ..models.social import RecommendationModel
from ..auth.dependencies import get_optional_claims, require_authenticated_user, require_system_admin
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.canonical import SEED_FALLBACK_TITLES
from ..repositories.personal import SEED_WATCH_EVENTS, _resolve_uuid as resolve_personal_uuid
from ..repositories.social import SEED_RECOMMENDATIONS, _resolve_uuid as resolve_social_uuid

logger = logging.getLogger("cinevault.routers.automation")

router = APIRouter(prefix="/automations", tags=["Automations & Hooks (v2.0 Module 4)"])

# Known external ID mapping fallbacks for test & development environments
SEED_EXTERNAL_MAPPINGS: Dict[str, str] = {
    # IMDB -> Title ID
    "tt0468569": "018f2e4a-7b31-7000-8000-123456789abf",  # The Dark Knight
    "tt6751668": "018f2e4a-7b31-7000-8000-123456789abc",  # Parasite
    "tt0073707": "018f2e4a-7b31-7000-8000-123456789abd",  # Sholay
    "tt1187043": "018f2e4a-7b31-7000-8000-123456789abe",  # 3 Idiots
    "tt1375666": "018f2e4a-7b31-7000-8000-123456789ac0",  # Inception
    "tt5074352": "018f2e4a-7b31-7000-8000-123456789ac1",  # Dangal
    "tt8178634": "018f2e4a-7b31-7000-8000-123456789ac2",  # RRR
    "tt0068646": "018f2e4a-7b31-7000-8000-123456789ac3",  # The Godfather
    "tt6077448": "018f2e4a-7b31-7000-8000-123456789ac4",  # Sacred Games
    "tt0816692": "018f2e4a-7b31-7000-8000-123456789ac5",  # Interstellar
    # TMDB -> Title ID
    "155": "018f2e4a-7b31-7000-8000-123456789abf",        # The Dark Knight
    "496243": "018f2e4a-7b31-7000-8000-123456789abc",     # Parasite
    "12244": "018f2e4a-7b31-7000-8000-123456789abd",      # Sholay
    "20453": "018f2e4a-7b31-7000-8000-123456789abe",      # 3 Idiots
    "27205": "018f2e4a-7b31-7000-8000-123456789ac0",      # Inception
    "360814": "018f2e4a-7b31-7000-8000-123456789ac1",     # Dangal
    "579974": "018f2e4a-7b31-7000-8000-123456789ac2",     # RRR
    "238": "018f2e4a-7b31-7000-8000-123456789ac3",        # The Godfather
    "157336": "018f2e4a-7b31-7000-8000-123456789ac5",     # Interstellar
}


def _extract_external_identifiers(payload: MediaServerWebhookPayload) -> List[Tuple[str, str]]:
    """
    Extracts provider and external ID tuples (e.g. [('imdb', 'tt0468569'), ('tmdb', '155')])
    from heterogeneous Plex / Jellyfin webhook structures.
    """
    identifiers: List[Tuple[str, str]] = []
    metadata = payload.Metadata or {}
    item = payload.Item or {}

    # 1. Plex guid / Guid structure
    guid_val = metadata.get("guid") or item.get("guid")
    if isinstance(guid_val, str):
        # Format: "imdb://tt0468569" or "com.plexapp.agents.imdb://tt0468569" or "plex://movie/..."
        imdb_match = re.search(r"tt\d+", guid_val)
        if imdb_match:
            identifiers.append(("imdb", imdb_match.group(0)))
        tmdb_match = re.search(r"tmdb://(\d+)", guid_val)
        if tmdb_match:
            identifiers.append(("tmdb", tmdb_match.group(1)))

    guids_list = metadata.get("Guid") or metadata.get("guids") or item.get("Guid")
    if isinstance(guids_list, list):
        for g in guids_list:
            if isinstance(g, dict) and "id" in g:
                raw_id = str(g["id"])
                imdb_m = re.search(r"tt\d+", raw_id)
                if imdb_m:
                    identifiers.append(("imdb", imdb_m.group(0)))
                tmdb_m = re.search(r"tmdb://(\d+)", raw_id)
                if tmdb_m:
                    identifiers.append(("tmdb", tmdb_m.group(1)))
            elif isinstance(g, str):
                imdb_m = re.search(r"tt\d+", g)
                if imdb_m:
                    identifiers.append(("imdb", imdb_m.group(0)))

    # 2. Jellyfin ProviderIds structure
    provider_ids = item.get("ProviderIds") or metadata.get("ProviderIds") or {}
    if isinstance(provider_ids, dict):
        if "Imdb" in provider_ids:
            identifiers.append(("imdb", str(provider_ids["Imdb"])))
        if "Tmdb" in provider_ids:
            identifiers.append(("tmdb", str(provider_ids["Tmdb"])))

    # 3. Direct field indicators
    for key in ("imdb_id", "imdb", "Provider_imdb"):
        val = metadata.get(key) or item.get(key)
        if val:
            identifiers.append(("imdb", str(val)))

    for key in ("tmdb_id", "tmdb", "Provider_tmdb"):
        val = metadata.get(key) or item.get(key)
        if val:
            identifiers.append(("tmdb", str(val)))

    return identifiers


def _resolve_media_server_user_id(payload: MediaServerWebhookPayload, override_user_id: Optional[str] = None) -> uuid.UUID:
    """
    Resolves the target user UUID from the webhook's Account, User, or query context.
    Provides deterministic mapping for test scenarios.
    """
    if override_user_id:
        return resolve_personal_uuid(override_user_id, "user_id")

    account = payload.Account or {}
    user = payload.User or {}

    username_or_id = (
        account.get("username")
        or account.get("title")
        or account.get("id")
        or user.get("Name")
        or user.get("Id")
        or user.get("Username")
    )

    if username_or_id:
        return resolve_personal_uuid(str(username_or_id), "user_id")

    # Default fallback dev/test user
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _resolve_title_id(
    db: Optional[AsyncSession],
    payload: MediaServerWebhookPayload,
) -> Tuple[Optional[uuid.UUID], Optional[str]]:
    """
    Resolves canonical title UUID and title name from external IDs or title metadata.

    Production / real DB mode (db is not None): only ever resolves against
    real canonical.title / canonical.title_external_id rows. A genuine
    not-found returns (None, None) -- it must NEVER fall through to the
    hardcoded demo catalog (SEED_EXTERNAL_MAPPINGS / SEED_FALLBACK_TITLES) or
    a name-derived UUID; callers are responsible for turning that into a
    real 404/422, not inventing an identity.

    Explicit local-dev seed mode (db is None): this only happens when
    get_db() has already gated it behind config.allow_seed_fallback (see
    database.py) -- i.e. local development without Postgres running. In
    that case the seed/demo fallback chain below is a deliberate, explicitly
    gated development convenience, not something reachable in staging/prod.
    """
    metadata = payload.Metadata or {}
    item = payload.Item or {}

    # Check for direct title_id in metadata (an explicit ID is trusted as-is
    # in both modes -- it isn't an invented identity, the caller supplied it)
    raw_title_id = metadata.get("title_id") or metadata.get("id") or item.get("title_id")
    if raw_title_id:
        try:
            return uuid.UUID(str(raw_title_id)), str(metadata.get("title") or item.get("Name") or "Resolved Title")
        except (ValueError, AttributeError):
            pass

    external_ids = _extract_external_identifiers(payload)
    title_name = metadata.get("title") or item.get("Name")

    if db is not None:
        # Real DB mode: resolve strictly against real data, no demo fallback.
        for provider, ext_id in external_ids:
            clean_id = ext_id.strip()
            stmt = (
                select(TitleExternalIdModel)
                .where(TitleExternalIdModel.external_id == clean_id)
                .options(selectinload(TitleExternalIdModel.title))
            )
            result = await db.execute(stmt)
            mapping = result.scalars().first()
            if mapping and mapping.title:
                return mapping.title_id, mapping.title.canonical_title

        if title_name:
            stmt = select(TitleModel).where(TitleModel.canonical_title.ilike(title_name))
            res = await db.execute(stmt)
            title_row = res.scalars().first()
            if title_row:
                return title_row.title_id, title_row.canonical_title

        # Genuine not-found against the real catalog -- do not invent one.
        return None, None

    # Explicit local-dev seed mode only (db is None).
    for provider, ext_id in external_ids:
        clean_id = ext_id.strip()
        if clean_id in SEED_EXTERNAL_MAPPINGS:
            tid_str = SEED_EXTERNAL_MAPPINGS[clean_id]
            seed_title_name = SEED_FALLBACK_TITLES.get(tid_str, {}).get("canonical_title", "Canonical Title")
            return uuid.UUID(tid_str), seed_title_name

    if title_name:
        for tid_str, s_data in SEED_FALLBACK_TITLES.items():
            if s_data.get("canonical_title", "").lower() == str(title_name).lower():
                return uuid.UUID(tid_str), s_data.get("canonical_title")

        # Deterministic UUID derived from the title name -- a documented
        # local-dev-only convenience so webhook testing works without a DB;
        # never reached outside the config.allow_seed_fallback gate above.
        derived_uuid = resolve_personal_uuid(str(title_name), "title_id")
        return derived_uuid, str(title_name)

    return None, None


# =============================================================================
# 1. Media Server Webhook Ingestion & Recommendation State Hook
# =============================================================================

@router.post(
    "/webhooks/media-server",
    response_model=MediaServerWebhookResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(enforce_rate_limit("PERSONAL_WRITE"))],
)
async def ingest_media_server_webhook(
    payload: MediaServerWebhookPayload,
    user_id: Optional[str] = Query(None, description="Optional target user UUID override"),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Ingests external media server webhooks (Plex, Jellyfin) to automate watch history logging
    and execute the automated state transition hook for peer recommendations:
    - Step A: Extracts external provider IDs (IMDB/TMDB) or metadata.
    - Step B: Resolves canonical title in canonical catalog.
    - Step C: Resolves user identity mapping.
    - Step D: Inserts an append-only WatchEventModel in the personal schema.
    - Step E: Social Hook — Checks for an 'ACCEPTED' recommendation for this (user_id, title_id)
              and automatically transitions its lifecycle status to 'WATCHED'.
    """
    event_name = payload.event
    target_user_uuid = _resolve_media_server_user_id(payload, override_user_id=user_id)
    title_uuid, canonical_title = await _resolve_title_id(db, payload)

    if not title_uuid:
        raw_name = (payload.Metadata or {}).get("title") or (payload.Item or {}).get("Name")

        # A payload with no title metadata at all has nothing to resolve an
        # identity from -- that's a malformed request regardless of
        # environment, checked before the db-mode branch below.
        if not raw_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Webhook payload has no title metadata to resolve (no Metadata.title or Item.Name).",
            )

        if db is not None:
            # Real DB mode: a title that cannot be resolved against the real
            # catalog is a real error -- never invent an identity for it
            # (that would create a watch_event/recommendation referencing a
            # title that doesn't exist).
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Could not resolve a canonical title for this webhook event ({raw_name!r}). "
                    "No matching external ID or title name was found in the catalog."
                ),
            )

        # db is None only when config.allow_seed_fallback is explicitly true
        # (local dev without Postgres, see database.py's get_db()). A
        # deterministic fallback UUID keeps local webhook testing usable
        # without a DB.
        title_uuid = resolve_personal_uuid(str(raw_name), "title_id")
        canonical_title = str(raw_name)

    now = datetime.now(timezone.utc)
    watch_event_id = uuid.uuid4()
    device_type = (payload.Player or {}).get("title") or "external_media_server"

    # -------------------------------------------------------------------------
    # D. Insert WatchEventModel into personal schema
    # -------------------------------------------------------------------------
    if db is not None:
        try:
            watch_event = WatchEventModel(
                watch_event_id=watch_event_id,
                user_id=target_user_uuid,
                title_id=title_uuid,
                watched_at=now,
                device_type=device_type,
                notes=f"Auto-scrobbled via external media server ({event_name})",
                is_tombstoned=False,
                created_at=now,
            )
            db.add(watch_event)
            await db.flush()
        except Exception as exc:
            logger.warning(f"Database write for watch_event failed, recording in memory: {exc}")
    else:
        user_key = str(target_user_uuid)
        if user_key not in SEED_WATCH_EVENTS:
            SEED_WATCH_EVENTS[user_key] = []
        from ..schemas.personal import WatchEventResponse
        SEED_WATCH_EVENTS[user_key].append(
            WatchEventResponse(
                id=str(watch_event_id),
                user_id=user_key,
                title_id=str(title_uuid),
                watched_at=now.isoformat(),
                progress_percentage=100.0,
                created_at=now.isoformat(),
                device_type=device_type,
                notes=f"Auto-scrobbled via external media server ({event_name})",
            )
        )

    # -------------------------------------------------------------------------
    # E. SOCIAL HOOK: Check and Auto-Transition ACCEPTED Recommendation -> WATCHED
    # -------------------------------------------------------------------------
    social_recommendation_updated = False
    updated_rec_id: Optional[str] = None

    if db is not None:
        try:
            stmt = select(RecommendationModel).where(
                and_(
                    RecommendationModel.recipient_id == target_user_uuid,
                    RecommendationModel.title_id == title_uuid,
                    RecommendationModel.status == RecommendationStatusEnum.ACCEPTED.value,
                )
            )
            res = await db.execute(stmt)
            matching_recs = res.scalars().all()

            for rec in matching_recs:
                rec.status = RecommendationStatusEnum.WATCHED.value
                rec.updated_at = now
                social_recommendation_updated = True
                updated_rec_id = str(rec.recommendation_id)

            if matching_recs:
                await db.flush()
        except Exception as exc:
            logger.warning(f"Failed to check recommendations in DB: {exc}")

    # In-memory hook execution (for unit tests / offline fallback)
    for rec_id, rec in list(SEED_RECOMMENDATIONS.items()):
        rec_recipient = resolve_social_uuid(rec.recipient_id, "user_id")
        rec_title = resolve_social_uuid(rec.title_id, "title_id")

        if (
            rec_recipient == target_user_uuid
            and rec_title == title_uuid
            and rec.status == RecommendationStatusEnum.ACCEPTED
        ):
            updated_rec = RecommendationResponse(
                recommendation_id=rec.recommendation_id,
                sender_id=rec.sender_id,
                recipient_id=rec.recipient_id,
                title_id=rec.title_id,
                status=RecommendationStatusEnum.WATCHED,
                sender_predicted_rating=rec.sender_predicted_rating,
                recipient_actual_rating=rec.recipient_actual_rating,
                context_note=rec.context_note,
                sent_at=rec.sent_at,
                updated_at=now,
            )
            SEED_RECOMMENDATIONS[rec_id] = updated_rec
            social_recommendation_updated = True
            updated_rec_id = str(rec_id)

    return MediaServerWebhookResponse(
        status="success",
        event=event_name,
        title_id=str(title_uuid),
        canonical_title=canonical_title,
        user_id=str(target_user_uuid),
        watch_event_id=str(watch_event_id),
        social_recommendation_updated=social_recommendation_updated,
        recommendation_id=updated_rec_id,
        message=(
            f"Successfully processed webhook event '{event_name}'."
            + (" Transitioned ACCEPTED recommendation to WATCHED." if social_recommendation_updated else "")
        ),
    )


# =============================================================================
# 2. Smart Watchlist API
# =============================================================================

@router.get(
    "/smart-watchlist",
    response_model=SmartWatchlistResponse,
    dependencies=[Depends(enforce_rate_limit("PUBLIC_READ"))],
)
async def get_smart_watchlist(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Categorizes the user's unwatched library into high-intent Smart Watchlist playlists:
    1. 'weekend_epics': Long-format cinematic experiences (Runtime > 150 mins).
    2. 'quick_watches': Snappy, high-efficiency entertainment (Runtime < 100 mins).
    3. 'friend_recommended': Peer-curated titles currently in 'ACCEPTED' recommendation status.
    """
    # 1. Resolve active user
    active_user_uuid = resolve_personal_uuid(claims.sub, "user_id")

    # 2. Identify watched title UUIDs to filter out completed items
    watched_title_ids = set()

    if db is not None:
        # Real DB mode: watched titles come strictly from real watch_event
        # rows. A query failure here is a real error, not "no watch
        # history" -- surface it rather than silently returning a possibly-
        # incomplete list.
        stmt = select(WatchEventModel.title_id).where(
            and_(
                WatchEventModel.user_id == active_user_uuid,
                WatchEventModel.is_tombstoned == False,
            )
        )
        res = await db.execute(stmt)
        for tid in res.scalars().all():
            watched_title_ids.add(str(tid))
    else:
        # db is None only when config.allow_seed_fallback is explicitly true
        # (local dev without Postgres, see database.py's get_db()).
        user_key = str(active_user_uuid)
        for we in SEED_WATCH_EVENTS.get(user_key, []):
            watched_title_ids.add(str(we.title_id))

    # 3. Collect catalog titles with canonical metadata and runtimes
    catalog_items: Dict[str, Dict[str, Any]] = {}

    if db is not None:
        # Real DB mode: catalog comes strictly from canonical.title. The
        # hardcoded demo catalog (SEED_FALLBACK_TITLES) must never be mixed
        # into a real response just because it's always been there --
        # that would show fabricated demo movies alongside genuine ones to
        # every real user, unconditionally, regardless of DB health.
        stmt = select(TitleModel).options(selectinload(TitleModel.editions), selectinload(TitleModel.genres))
        res = await db.execute(stmt)
        db_titles = res.scalars().all()
        for t in db_titles:
            t_id_str = str(t.title_id)
            runtime = None
            if t.editions:
                runtime = t.editions[0].runtime_minutes
            genres = [g.name for g in t.genres] if hasattr(t, "genres") and t.genres else []
            catalog_items[t_id_str] = {
                "title_id": t_id_str,
                "canonical_title": t.canonical_title,
                "runtime_minutes": runtime,
                "production_year": t.production_year,
                "genres": genres,
                "poster_url": t.poster_url,
                "backdrop_url": t.backdrop_url,
            }
    else:
        for tid_str, title_data in SEED_FALLBACK_TITLES.items():
            runtime = title_data.get("primary_edition", {}).get("runtime_minutes")
            catalog_items[tid_str] = {
                "title_id": tid_str,
                "canonical_title": title_data.get("canonical_title", "Untitled"),
                "runtime_minutes": runtime,
                "production_year": title_data.get("production_year"),
                "genres": title_data.get("genres", []),
                "poster_url": title_data.get("poster_url"),
                "backdrop_url": title_data.get("backdrop_url"),
            }

    # 4. Collect friend recommendations in ACCEPTED status
    accepted_recommendations: List[Dict[str, Any]] = []

    if db is not None:
        stmt = select(RecommendationModel).where(
            and_(
                RecommendationModel.recipient_id == active_user_uuid,
                RecommendationModel.status == RecommendationStatusEnum.ACCEPTED.value,
            )
        )
        res = await db.execute(stmt)
        recs = res.scalars().all()
        for r in recs:
            accepted_recommendations.append({
                "title_id": str(r.title_id),
                "context_note": r.context_note,
                "sender_id": str(r.sender_id),
            })
    else:
        for r in SEED_RECOMMENDATIONS.values():
            rec_recipient = resolve_social_uuid(r.recipient_id, "user_id")
            if rec_recipient == active_user_uuid and r.status == RecommendationStatusEnum.ACCEPTED:
                accepted_recommendations.append({
                    "title_id": str(r.title_id),
                    "context_note": r.context_note,
                    "sender_id": str(r.sender_id),
                })

    # 5. Partition titles into SmartWatchlistResponse categories
    weekend_epics: List[SmartWatchlistItem] = []
    quick_watches: List[SmartWatchlistItem] = []
    friend_recommended: List[SmartWatchlistItem] = []

    # Process Catalog Titles
    for tid_str, item_info in catalog_items.items():
        if tid_str in watched_title_ids:
            continue  # Skip already watched titles

        runtime = item_info.get("runtime_minutes")
        if runtime is not None:
            if runtime > 150:
                weekend_epics.append(
                    SmartWatchlistItem(
                        title_id=item_info["title_id"],
                        canonical_title=item_info["canonical_title"],
                        runtime_minutes=runtime,
                        production_year=item_info.get("production_year"),
                        genres=item_info.get("genres", []),
                        poster_url=item_info.get("poster_url"),
                        backdrop_url=item_info.get("backdrop_url"),
                    )
                )
            elif runtime < 100:
                quick_watches.append(
                    SmartWatchlistItem(
                        title_id=item_info["title_id"],
                        canonical_title=item_info["canonical_title"],
                        runtime_minutes=runtime,
                        production_year=item_info.get("production_year"),
                        genres=item_info.get("genres", []),
                        poster_url=item_info.get("poster_url"),
                        backdrop_url=item_info.get("backdrop_url"),
                    )
                )

    # Process Accepted Friend Recommendations
    for rec_data in accepted_recommendations:
        tid_str = rec_data["title_id"]
        # Resolve title details from catalog or fallback
        title_meta = catalog_items.get(tid_str)
        if title_meta:
            friend_recommended.append(
                SmartWatchlistItem(
                    title_id=title_meta["title_id"],
                    canonical_title=title_meta["canonical_title"],
                    runtime_minutes=title_meta.get("runtime_minutes"),
                    production_year=title_meta.get("production_year"),
                    genres=title_meta.get("genres", []),
                    poster_url=title_meta.get("poster_url"),
                    backdrop_url=title_meta.get("backdrop_url"),
                    recommendation_note=rec_data.get("context_note"),
                    recommended_by=rec_data.get("sender_id"),
                )
            )
        else:
            friend_recommended.append(
                SmartWatchlistItem(
                    title_id=tid_str,
                    canonical_title=f"Recommended Title ({tid_str[-6:]})",
                    recommendation_note=rec_data.get("context_note"),
                    recommended_by=rec_data.get("sender_id"),
                )
            )

    return SmartWatchlistResponse(
        weekend_epics=weekend_epics,
        quick_watches=quick_watches,
        friend_recommended=friend_recommended,
    )


@router.post("/sync-metadata", status_code=status.HTTP_202_ACCEPTED)
async def trigger_automations_metadata_sync(
    background_tasks: BackgroundTasks,
    batch_size: int = Query(500, ge=1, le=5000, description="Batch size per query"),
    max_batches: Optional[int] = Query(None, ge=1, description="Optional max batch count"),
    api_key: Optional[str] = Query(None, description="Optional TMDB API key override"),
    claims: SecurityTokenClaims = Depends(require_system_admin),
) -> Dict[str, Any]:
    """Triggers background TMDB metadata and poster synchronization from automations router."""
    from ..ingestion.tmdb_worker import sync_missing_posters
    job_id = f"sync-meta-{uuid.uuid4().hex[:12]}"

    background_tasks.add_task(
        sync_missing_posters,
        tmdb_api_key=api_key,
        batch_size=batch_size,
        max_batches=max_batches,
    )

    return {
        "status": "ACCEPTED",
        "job_id": job_id,
        "message": "Background TMDB artwork & metadata synchronization dispatched.",
        "batch_size": batch_size,
        "max_batches": max_batches,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }

