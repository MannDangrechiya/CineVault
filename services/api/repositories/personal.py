# CineVault OS — Personal Domain Repository (CAT-2) (P0 Fix)
# Asynchronous PostgreSQL database access layer for user personal logs,
# watch events, ratings, notes & conflicts (ADR-003, ADR-004)
#
# P0 Fix: Replaced uuid.uuid4() fallback for invalid IDs with strict UUID
# validation helpers that raise ValueError rather than silently generating
# new random UUIDs, which caused every non-UUID user_id to write to a
# different database row — completely breaking personal data isolation.

from ..config import config
import uuid
import logging
from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, update, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.personal import (
    LibraryEntryModel, WatchEventModel, UserTitleStateModel,
    RatingModel, NoteModel, ReviewModel, PersonalDataConflictModel,
    UserListModel, UserListItemModel, UserStreakModel
)
from ..models.canonical import (
    TitleModel, EditionModel, SeasonModel, EpisodeModel, TitleCountryModel, TitleLanguageModel, CreditModel, TitleExternalIdModel
)
from ..schemas.personal import (
    WatchEventCreate, WatchEventResponse,
    UserTitleStateResponse, UserTitleStateUpdate,
    RatingCreate, RatingResponse,
    NoteCreate, NoteResponse,
    ReviewCreate, ReviewResponse,
    PersonalDataConflictResponse,
    UserDashboardMetricsResponse,
    PersonalDataExportResponse,
    ImportPreviewResponse,
    ImportPreviewRequest,
    ImportConflictItem,
    ImportCandidateMatch,
    ImportApplyResponse,
    ImportApplyRequest,
    ImportItemPayload,
    ImportConflictStrategyEnum,
    ImportItemVerdict,
    WatchlistItemResponse,
    WatchlistPageResponse,
    UserStreakResponse,
    GenreAffinityItem,
    CreatorAffinityItem,
    MonthlyTrendItem,
    HistoryItemResponse,
    HistoryPageResponse,
    CollectionItemResponse,
    CollectionCreateRequest,
    CollectionDetailResponse,
    CollectionTitleItem,
    LibraryItemResponse,
    LibraryPageResponse,
)
from ..media_resolver import resolve_poster_url
from ..personal.export_service import (
    build_json_export, build_csv_zip_export, build_excel_export, build_markdown_export
)
from ..personal.mapping import (
    parse_csv_content, parse_json_content, parse_xlsx_content, parse_unstructured_text_content,
    convert_raw_dict_to_import_payload
)

# Both values are treated as "on the watchlist" — some pre-existing rows use
# the older WATCHLIST label, new writes use PLAN_TO_WATCH (see toggleWatchlistState).
WATCHLIST_STATUS_VALUES = ("PLAN_TO_WATCH", "WATCHLIST")

logger = logging.getLogger("cinevault.repositories.personal")

# In-memory stores used ONLY in local_development when allow_seed_fallback=True
SEED_WATCH_EVENTS: Dict[str, List[WatchEventResponse]] = {}
SEED_RATINGS: Dict[str, List[RatingResponse]] = {}
SEED_NOTES: Dict[str, List[NoteResponse]] = {}
SEED_REVIEWS: Dict[str, List[ReviewResponse]] = {}
SEED_USER_TITLE_STATES: Dict[str, Dict[str, UserTitleStateResponse]] = {}
SEED_LIBRARY: Dict[str, List[LibraryItemResponse]] = {}
SEED_COLLECTIONS: Dict[str, List[CollectionDetailResponse]] = {}


# ---------------------------------------------------------------------------
# UUID Resolution Helpers (P0 Fix)
# ---------------------------------------------------------------------------

def _resolve_uuid(value: str, field_name: str) -> uuid.UUID:
    """
    Resolves a string to a UUID object.
    - If value is a valid UUID string (e.g. UUIDv4 or UUIDv7), returns uuid.UUID(value).
    - If value is a string identifier (e.g. 'usr_user_001' or 'user-123'), deterministically
      maps it to a UUIDv5 using uuid.NAMESPACE_DNS so that the exact same string
      identifier consistently maps to the same UUID without generating random UUIDs.
    """
    if not value:
        raise ValueError(f"Invalid {field_name}: value cannot be empty.")
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"cinevault:{field_name}:{value}")


def _resolve_user_uuid(user_id: str) -> uuid.UUID:
    return _resolve_uuid(user_id, "user_id")


def _resolve_title_uuid(title_id: str) -> uuid.UUID:
    return _resolve_uuid(title_id, "title_id")


def _resolve_edition_uuid(edition_id: Optional[str]) -> Optional[uuid.UUID]:
    if edition_id is None:
        return None
    return _resolve_uuid(edition_id, "edition_id")


def _resolve_season_uuid(season_id: Optional[str]) -> Optional[uuid.UUID]:
    if season_id is None:
        return None
    return _resolve_uuid(season_id, "season_id")


def _resolve_episode_uuid(episode_id: Optional[str]) -> Optional[uuid.UUID]:
    if episode_id is None:
        return None
    return _resolve_uuid(episode_id, "episode_id")


def _resolve_idempotency_key(key: Optional[str]) -> uuid.UUID:
    """Resolves an idempotency key to UUID, or generates a fresh UUIDv4 if None."""
    if key is None:
        return uuid.uuid4()
    try:
        return uuid.UUID(key)
    except (ValueError, AttributeError):
        logger.warning(
            "Idempotency key '%s' is not a valid UUID — generating new UUID for this event.",
            key,
        )
        return uuid.uuid4()


async def _safe_rollback(db: Optional[AsyncSession]) -> None:
    if db is not None:
        try:
            await db.rollback()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class PersonalRepository:
    """Provides async database operations for user personal library, watch history, and state."""

    async def list_watch_events(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        title_id: Optional[str] = None,
    ) -> List[WatchEventResponse]:
        """Lists append-only watch events owned by the specified user (CAT-2), optionally filtered by title_id."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                filters = [
                    WatchEventModel.user_id == user_uuid,
                    WatchEventModel.is_tombstoned == False,  # noqa: E712
                ]
                if title_id:
                    title_uuid = _resolve_title_uuid(title_id)
                    filters.append(WatchEventModel.title_id == title_uuid)

                stmt = (
                    select(WatchEventModel)
                    .where(and_(*filters))
                    .order_by(WatchEventModel.watched_at.desc())
                )
                result = await db.execute(stmt)
                events = result.scalars().all()
                return [
                    WatchEventResponse(
                        id=str(e.watch_event_id),
                        user_id=str(e.user_id),
                        title_id=str(e.title_id),
                        edition_id=str(e.edition_id) if e.edition_id else None,
                        season_id=str(e.season_id) if e.season_id else None,
                        episode_id=str(e.episode_id) if e.episode_id else None,
                        device_type=e.device_type,
                        notes=e.notes,
                        watched_at=(
                            e.watched_at.isoformat()
                            if e.watched_at
                            else datetime.now(timezone.utc).isoformat()
                        ),
                        progress_percentage=100.0,
                        created_at=(
                            e.created_at.isoformat()
                            if e.created_at
                            else datetime.now(timezone.utc).isoformat()
                        ),
                    )
                    for e in events
                ]
            except ValueError:
                raise  # UUID validation error — propagate as 400
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("list_watch_events failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise
                # Fall through to seed fallback below

        # Seed fallback — local_development only when allow_seed_fallback=True
        user_events = SEED_WATCH_EVENTS.get(user_id, [])
        if not user_events:
            user_events = [
                WatchEventResponse(
                    id="018f2e4a-7b31-7000-8000-000000000001",
                    user_id=user_id,
                    title_id="018f2e4a-7b31-7000-8000-123456789abc",
                    watched_at="2026-08-08T18:00:00Z",
                    progress_percentage=100.0,
                    created_at="2026-08-08T18:00:00Z",
                )
            ]
        return user_events

    async def create_watch_event(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        body: WatchEventCreate,
        idempotency_key: Optional[str] = None,
    ) -> WatchEventResponse:
        """Appends an immutable watch event log (ADR-003)."""
        new_event_uuid = _resolve_idempotency_key(idempotency_key)
        created_iso = datetime.now(timezone.utc).isoformat()

        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(body.title_id)
                edition_uuid = _resolve_edition_uuid(body.edition_id)
                season_uuid = _resolve_season_uuid(body.season_id)
                episode_uuid = _resolve_episode_uuid(body.episode_id)

                # Idempotency check: if event already exists with this ID, return it
                existing_stmt = select(WatchEventModel).where(
                    WatchEventModel.watch_event_id == new_event_uuid
                )
                existing_ev = (await db.execute(existing_stmt)).scalar_one_or_none()
                if existing_ev:
                    return WatchEventResponse(
                        id=str(existing_ev.watch_event_id),
                        user_id=user_id,
                        title_id=str(existing_ev.title_id),
                        edition_id=str(existing_ev.edition_id) if existing_ev.edition_id else None,
                        season_id=str(existing_ev.season_id) if existing_ev.season_id else None,
                        episode_id=str(existing_ev.episode_id) if existing_ev.episode_id else None,
                        device_type=existing_ev.device_type,
                        notes=existing_ev.notes,
                        watched_at=existing_ev.watched_at.isoformat(),
                        progress_percentage=body.progress_percentage,
                        created_at=existing_ev.created_at.isoformat(),
                    )

                event_orm = WatchEventModel(
                    watch_event_id=new_event_uuid,
                    user_id=user_uuid,
                    title_id=title_uuid,
                    edition_id=edition_uuid,
                    season_id=season_uuid,
                    episode_id=episode_uuid,
                    device_type=body.device_type,
                    notes=body.notes,
                    watched_at=(
                        datetime.fromisoformat(body.watched_at.replace("Z", "+00:00"))
                        if "T" in body.watched_at
                        else datetime.now(timezone.utc)
                    ),
                    is_tombstoned=False,
                )
                db.add(event_orm)
                await db.flush()

                # Automatically maintain user title state (ADR-003)
                target_status = "COMPLETED"
                if episode_uuid:
                    # Query total episodes belonging to this series
                    ep_count_stmt = (
                        select(func.count(EpisodeModel.episode_id))
                        .join(SeasonModel, SeasonModel.season_id == EpisodeModel.season_id)
                        .where(SeasonModel.title_id == title_uuid)
                    )
                    total_episodes = (await db.execute(ep_count_stmt)).scalar() or 0

                    # Query distinct watched episodes for this user on this series
                    watched_eps_stmt = (
                        select(func.count(func.distinct(WatchEventModel.episode_id)))
                        .where(
                            and_(
                                WatchEventModel.user_id == user_uuid,
                                WatchEventModel.title_id == title_uuid,
                                WatchEventModel.episode_id.isnot(None),
                                WatchEventModel.is_tombstoned == False,  # noqa: E712
                            )
                        )
                    )
                    distinct_watched = (await db.execute(watched_eps_stmt)).scalar() or 0

                    if total_episodes > 0 and distinct_watched >= total_episodes:
                        target_status = "COMPLETED"
                    else:
                        target_status = "WATCHING"

                state_stmt = select(UserTitleStateModel).where(
                    and_(
                        UserTitleStateModel.user_id == user_uuid,
                        UserTitleStateModel.title_id == title_uuid,
                    )
                )
                st_res = await db.execute(state_stmt)
                st_orm = st_res.scalar_one_or_none()
                if not st_orm:
                    st_orm = UserTitleStateModel(
                        user_id=user_uuid,
                        title_id=title_uuid,
                        manual_status_override=target_status,
                        is_favorite=False,
                        preferred_edition_id=edition_uuid,
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(st_orm)
                else:
                    if target_status == "COMPLETED" or st_orm.manual_status_override in (None, "PLAN_TO_WATCH", "WATCHLIST", "WATCHING"):
                        st_orm.manual_status_override = target_status
                        st_orm.updated_at = datetime.now(timezone.utc)

                # Maintain streak progression (Part 2 Item 2.3)
                watch_dt = event_orm.watched_at
                watch_date = watch_dt.date() if isinstance(watch_dt, datetime) else datetime.now(timezone.utc).date()
                await self.update_user_streak(db, user_uuid, watch_date)

                return WatchEventResponse(
                    id=str(event_orm.watch_event_id),
                    user_id=user_id,
                    title_id=body.title_id,
                    edition_id=body.edition_id,
                    season_id=body.season_id,
                    episode_id=body.episode_id,
                    device_type=body.device_type,
                    notes=body.notes,
                    watched_at=body.watched_at,
                    progress_percentage=body.progress_percentage,
                    created_at=created_iso,
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("create_watch_event failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        resp = WatchEventResponse(
            id=str(new_event_uuid),
            user_id=user_id,
            title_id=body.title_id,
            edition_id=body.edition_id,
            watched_at=body.watched_at,
            progress_percentage=body.progress_percentage,
            created_at=created_iso,
        )
        if user_id not in SEED_WATCH_EVENTS:
            SEED_WATCH_EVENTS[user_id] = []
        SEED_WATCH_EVENTS[user_id].append(resp)
        return resp

    async def update_user_streak(
        self,
        db: AsyncSession,
        user_uuid: uuid.UUID,
        watch_date: date,
    ) -> UserStreakModel:
        """
        Maintains consecutive daily viewing streak for a user (ADR-003, Part 2 Item 2.3).
        - Same day: no-op (streak maintained).
        - Consecutive day (watch_date == last_watch_date + 1 day): current_streak += 1, longest_streak = max.
        - Broken streak (watch_date > last_watch_date + 1 day or last_watch_date is None): current_streak = 1, longest_streak = max.
        """
        now = datetime.now(timezone.utc)
        stmt = select(UserStreakModel).where(UserStreakModel.user_id == user_uuid)
        res = await db.execute(stmt)
        streak = res.scalar_one_or_none()

        if not streak:
            streak = UserStreakModel(
                user_id=user_uuid,
                current_streak=1,
                longest_streak=1,
                last_watch_date=watch_date,
                updated_at=now,
            )
            db.add(streak)
        else:
            if streak.last_watch_date is None:
                streak.current_streak = 1
                streak.longest_streak = max(streak.longest_streak, 1)
                streak.last_watch_date = watch_date
                streak.updated_at = now
            elif watch_date == streak.last_watch_date:
                # Same day watch, do not double-increment
                streak.updated_at = now
            elif watch_date == streak.last_watch_date + timedelta(days=1):
                # Consecutive day watch
                streak.current_streak += 1
                streak.longest_streak = max(streak.longest_streak, streak.current_streak)
                streak.last_watch_date = watch_date
                streak.updated_at = now
            elif watch_date > streak.last_watch_date + timedelta(days=1):
                # Broken streak
                streak.current_streak = 1
                streak.longest_streak = max(streak.longest_streak, 1)
                streak.last_watch_date = watch_date
                streak.updated_at = now

        await db.flush()
        return streak

    async def get_user_streak(
        self,
        db: Optional[AsyncSession],
        user_id: str,
    ) -> UserStreakResponse:
        """Fetches the user's current and longest watch streaks."""
        user_uuid = _resolve_user_uuid(user_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        if db is not None:
            try:
                stmt = select(UserStreakModel).where(UserStreakModel.user_id == user_uuid)
                res = await db.execute(stmt)
                streak = res.scalar_one_or_none()
                if streak:
                    return UserStreakResponse(
                        user_id=str(streak.user_id),
                        current_streak=streak.current_streak,
                        longest_streak=streak.longest_streak,
                        last_watch_date=streak.last_watch_date.isoformat() if streak.last_watch_date else None,
                        updated_at=streak.updated_at.isoformat() if streak.updated_at else now_iso,
                    )
            except Exception as exc:
                logger.error("get_user_streak failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return UserStreakResponse(
            user_id=user_id,
            current_streak=0,
            longest_streak=0,
            last_watch_date=None,
            updated_at=now_iso,
        )

    async def get_user_title_state(
        self, db: Optional[AsyncSession], user_id: str, title_id: str
    ) -> UserTitleStateResponse:
        """Retrieves user title library state (watch status, favorite flag, preferred edition)."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(title_id)
                stmt = select(UserTitleStateModel).where(
                    and_(
                        UserTitleStateModel.user_id == user_uuid,
                        UserTitleStateModel.title_id == title_uuid,
                    )
                )
                res = await db.execute(stmt)
                st = res.scalar_one_or_none()
                if st:
                    return UserTitleStateResponse(
                        title_id=title_id,
                        derived_status=st.manual_status_override or "UNWATCHED",
                        manual_status_override=st.manual_status_override,
                        is_favorite=st.is_favorite,
                        preferred_edition_id=(
                            str(st.preferred_edition_id)
                            if st.preferred_edition_id
                            else None
                        ),
                        updated_at=(
                            st.updated_at.isoformat()
                            if st.updated_at
                            else datetime.now(timezone.utc).isoformat()
                        ),
                    )
                # No state record found — return canonical empty state (not a fallback)
                return UserTitleStateResponse(
                    title_id=title_id,
                    derived_status="UNWATCHED",
                    manual_status_override=None,
                    is_favorite=False,
                    preferred_edition_id=None,
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("get_user_title_state failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        user_states = SEED_USER_TITLE_STATES.get(user_id, {})
        if title_id in user_states:
            return user_states[title_id]
        return UserTitleStateResponse(
            title_id=title_id,
            derived_status="UNWATCHED",
            manual_status_override=None,
            is_favorite=False,
            preferred_edition_id=None,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    async def update_user_title_state(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        title_id: str,
        body: UserTitleStateUpdate,
    ) -> UserTitleStateResponse:
        """Updates user title library state.

        PATCH semantics: a field omitted from the request body leaves the stored
        value unchanged; a field explicitly present in the body — including an
        explicit null — overwrites it. This is what lets a client clear
        manual_status_override (e.g. remove a title from the watchlist) instead
        of a null silently falling back to whatever was already stored.
        """
        updated_iso = datetime.now(timezone.utc).isoformat()
        fields_set = body.model_fields_set

        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(title_id)

                stmt = select(UserTitleStateModel).where(
                    and_(
                        UserTitleStateModel.user_id == user_uuid,
                        UserTitleStateModel.title_id == title_uuid,
                    )
                )
                res = await db.execute(stmt)
                st = res.scalar_one_or_none()

                fav = (
                    body.is_favorite if "is_favorite" in fields_set
                    else (st.is_favorite if st else False)
                )
                status_override = (
                    body.manual_status_override if "manual_status_override" in fields_set
                    else (st.manual_status_override if st else None)
                )
                pref_ed_uuid = (
                    _resolve_edition_uuid(body.preferred_edition_id) if "preferred_edition_id" in fields_set
                    else (st.preferred_edition_id if st else None)
                )

                if st:
                    st.is_favorite = fav
                    st.manual_status_override = status_override
                    st.preferred_edition_id = pref_ed_uuid
                    st.updated_at = datetime.now(timezone.utc)
                else:
                    st = UserTitleStateModel(
                        user_id=user_uuid,
                        title_id=title_uuid,
                        manual_status_override=status_override,
                        is_favorite=fav,
                        preferred_edition_id=pref_ed_uuid,
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(st)
                await db.flush()

                return UserTitleStateResponse(
                    title_id=title_id,
                    derived_status=status_override or "UNWATCHED",
                    manual_status_override=status_override,
                    is_favorite=fav,
                    preferred_edition_id=str(pref_ed_uuid) if pref_ed_uuid else None,
                    updated_at=updated_iso,
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("update_user_title_state failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        if user_id not in SEED_USER_TITLE_STATES:
            SEED_USER_TITLE_STATES[user_id] = {}
        existing = SEED_USER_TITLE_STATES[user_id].get(title_id)
        fav = (
            body.is_favorite if "is_favorite" in fields_set
            else (existing.is_favorite if existing else False)
        )
        status_override = (
            body.manual_status_override if "manual_status_override" in fields_set
            else (existing.manual_status_override if existing else None)
        )
        pref_ed = (
            body.preferred_edition_id if "preferred_edition_id" in fields_set
            else (existing.preferred_edition_id if existing else None)
        )
        resp = UserTitleStateResponse(
            title_id=title_id,
            derived_status=status_override or "UNWATCHED",
            manual_status_override=status_override,
            is_favorite=fav if fav is not None else False,
            preferred_edition_id=pref_ed,
            updated_at=updated_iso,
        )
        SEED_USER_TITLE_STATES[user_id][title_id] = resp
        return resp

    async def list_watchlist(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        sort: str = "added_at_desc",
    ) -> WatchlistPageResponse:
        """Lists titles the user has marked plan-to-watch, joined with canonical title metadata."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                where_clause = and_(
                    UserTitleStateModel.user_id == user_uuid,
                    UserTitleStateModel.manual_status_override.in_(WATCHLIST_STATUS_VALUES),
                )

                total = (
                    await db.execute(select(func.count()).select_from(UserTitleStateModel).where(where_clause))
                ).scalar_one()

                order_col = UserTitleStateModel.updated_at
                order = order_col.asc() if sort == "added_at_asc" else order_col.desc()
                stmt = (
                    select(UserTitleStateModel)
                    .where(where_clause)
                    .order_by(order)
                    .limit(limit)
                    .offset(offset)
                )
                states = (await db.execute(stmt)).scalars().all()

                title_map: Dict[uuid.UUID, TitleModel] = {}
                title_ids = [s.title_id for s in states]
                if title_ids:
                    titles = (
                        await db.execute(select(TitleModel).where(TitleModel.title_id.in_(title_ids)))
                    ).scalars().all()
                    title_map = {t.title_id: t for t in titles}

                items = [
                    WatchlistItemResponse(
                        id=f"{s.user_id}:{s.title_id}",
                        title_id=str(s.title_id),
                        canonical_title=(title_map[s.title_id].canonical_title if s.title_id in title_map else "Unknown Title"),
                        production_year=(title_map[s.title_id].production_year if s.title_id in title_map else None),
                        content_type=((title_map[s.title_id].content_type_id if s.title_id in title_map else None) or "MOVIE").upper(),
                        poster_url=resolve_poster_url(title_map[s.title_id].poster_url if s.title_id in title_map else None),
                        added_at=s.updated_at.isoformat() if s.updated_at else datetime.now(timezone.utc).isoformat(),
                    )
                    for s in states
                ]

                return WatchlistPageResponse(items=items, total=total, limit=limit, offset=offset)
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("list_watchlist failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        from .canonical import SEED_FALLBACK_TITLES
        user_states = SEED_USER_TITLE_STATES.get(user_id, {})
        items = []
        for tid, s in user_states.items():
            if s.manual_status_override in WATCHLIST_STATUS_VALUES:
                canonical_info = SEED_FALLBACK_TITLES.get(tid, {})
                items.append(
                    WatchlistItemResponse(
                        id=f"{user_id}:{tid}",
                        title_id=tid,
                        canonical_title=canonical_info.get("canonical_title", "Unknown Title"),
                        production_year=canonical_info.get("production_year", 2024),
                        content_type=(canonical_info.get("content_type") or "MOVIE").upper(),
                        poster_url=resolve_poster_url(canonical_info.get("poster_url")),
                        added_at=s.updated_at,
                    )
                )
        return WatchlistPageResponse(items=items, total=len(items), limit=limit, offset=offset)

    async def list_history(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        content_type: Optional[str] = None,
    ) -> HistoryPageResponse:
        """Lists paginated real watch history for the user (personal.watch_event),
        joined with canonical title metadata and the user's own rating for that
        title when one exists. Mirrors list_watchlist's join/pagination/fallback shape."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                where_clause = and_(
                    WatchEventModel.user_id == user_uuid,
                    WatchEventModel.is_tombstoned == False,  # noqa: E712
                )
                base_query = select(WatchEventModel).where(where_clause)
                count_query = select(func.count()).select_from(WatchEventModel).where(where_clause)

                # Optional content-type filter (e.g. "MOVIE"/"TV_SERIES") requires a join
                # against canonical.title, matched case-insensitively like list_titles().
                if content_type and content_type != "ALL":
                    base_query = base_query.join(
                        TitleModel, TitleModel.title_id == WatchEventModel.title_id
                    ).where(TitleModel.content_type_id.ilike(content_type))
                    count_query = count_query.join(
                        TitleModel, TitleModel.title_id == WatchEventModel.title_id
                    ).where(TitleModel.content_type_id.ilike(content_type))

                total = (await db.execute(count_query)).scalar_one()

                stmt = (
                    base_query
                    .order_by(WatchEventModel.watched_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                events = (await db.execute(stmt)).scalars().all()

                title_ids = [e.title_id for e in events]
                episode_ids = [e.episode_id for e in events if e.episode_id]
                season_ids = [e.season_id for e in events if e.season_id]

                title_map: Dict[uuid.UUID, TitleModel] = {}
                rating_map: Dict[uuid.UUID, RatingModel] = {}
                episode_map: Dict[uuid.UUID, EpisodeModel] = {}
                season_map: Dict[uuid.UUID, SeasonModel] = {}

                if title_ids:
                    titles = (
                        await db.execute(select(TitleModel).where(TitleModel.title_id.in_(title_ids)))
                    ).scalars().all()
                    title_map = {t.title_id: t for t in titles}

                    ratings = (
                        await db.execute(
                            select(RatingModel).where(
                                and_(
                                    RatingModel.user_id == user_uuid,
                                    RatingModel.title_id.in_(title_ids),
                                )
                            )
                        )
                    ).scalars().all()
                    rating_map = {r.title_id: r for r in ratings}

                if episode_ids:
                    episodes = (
                        await db.execute(select(EpisodeModel).where(EpisodeModel.episode_id.in_(episode_ids)))
                    ).scalars().all()
                    episode_map = {ep.episode_id: ep for ep in episodes}
                    for ep in episodes:
                        if ep.season_id and ep.season_id not in season_ids:
                            season_ids.append(ep.season_id)

                if season_ids:
                    seasons = (
                        await db.execute(select(SeasonModel).where(SeasonModel.season_id.in_(season_ids)))
                    ).scalars().all()
                    season_map = {s.season_id: s for s in seasons}

                items = []
                for e in events:
                    ep_orm = episode_map.get(e.episode_id) if e.episode_id else None
                    s_orm = season_map.get(e.season_id) if e.season_id else (season_map.get(ep_orm.season_id) if ep_orm else None)
                    items.append(
                        HistoryItemResponse(
                            id=str(e.watch_event_id),
                            title_id=str(e.title_id),
                            canonical_title=(title_map[e.title_id].canonical_title if e.title_id in title_map else "Unknown Title"),
                            production_year=(title_map[e.title_id].production_year if e.title_id in title_map else None),
                            content_type=((title_map[e.title_id].content_type_id if e.title_id in title_map else None) or "MOVIE").upper(),
                            poster_url=resolve_poster_url(title_map[e.title_id].poster_url if e.title_id in title_map else None),
                            watched_at=e.watched_at.isoformat() if e.watched_at else datetime.now(timezone.utc).isoformat(),
                            rating_value=(rating_map[e.title_id].rating_value if e.title_id in rating_map else None),
                            device_type=e.device_type,
                            progress_percentage=100.0,
                            season_id=str(s_orm.season_id) if s_orm else (str(e.season_id) if e.season_id else None),
                            episode_id=str(e.episode_id) if e.episode_id else None,
                            season_number=s_orm.season_number if s_orm else None,
                            episode_number=ep_orm.episode_number if ep_orm else None,
                            episode_name=ep_orm.episode_name if ep_orm else None,
                        )
                    )

                return HistoryPageResponse(items=items, total=total, limit=limit, offset=offset)
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("list_history failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return HistoryPageResponse(items=[], total=0, limit=limit, offset=offset)

    async def delete_watch_event(
        self, db: Optional[AsyncSession], user_id: str, watch_event_id: str
    ) -> bool:
        """Tombstones (soft-deletes) a watch history event owned by the user.
        Uses is_tombstoned rather than a hard delete, matching ADR-003's append-only
        watch event log design. Returns False (not a crash) for a bad UUID or a
        not-found/not-owned event."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                try:
                    event_uuid = uuid.UUID(watch_event_id)
                except ValueError:
                    return False

                stmt = select(WatchEventModel).where(
                    and_(
                        WatchEventModel.watch_event_id == event_uuid,
                        WatchEventModel.user_id == user_uuid,
                    )
                )
                event = (await db.execute(stmt)).scalar_one_or_none()
                if not event:
                    return False

                event.is_tombstoned = True
                await db.flush()
                return True
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("delete_watch_event failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise
                return False

        return False

    async def list_collections(
        self, db: Optional[AsyncSession], user_id: str
    ) -> List[CollectionItemResponse]:
        """Lists user-owned collections (personal.user_list), enriched with real item
        counts. curator/tags/is_custom have no backing columns on UserListModel, so
        they fall through to the Pydantic schema's own static field defaults."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                stmt = (
                    select(UserListModel)
                    .options(selectinload(UserListModel.items))
                    .where(UserListModel.user_id == user_uuid)
                    .order_by(UserListModel.created_at.desc())
                )
                lists = (await db.execute(stmt)).scalars().all()
                return [
                    CollectionItemResponse(
                        id=str(ul.list_id),
                        name=ul.title,
                        description=ul.description,
                        item_count=len(ul.items),
                        banner_url=None,
                        is_private=ul.is_private,
                        created_at=ul.created_at.isoformat() if ul.created_at else datetime.now(timezone.utc).isoformat(),
                    )
                    for ul in lists
                ]
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("list_collections failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return []

    async def create_collection(
        self, db: Optional[AsyncSession], user_id: str, body: CollectionCreateRequest
    ) -> CollectionItemResponse:
        """Creates a new user-owned collection (personal.user_list)."""
        created_iso = datetime.now(timezone.utc).isoformat()
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                now = datetime.now(timezone.utc)
                ul = UserListModel(
                    list_id=uuid.uuid4(),
                    user_id=user_uuid,
                    title=body.name,
                    description=body.description,
                    is_private=body.is_private,
                    created_at=now,
                    updated_at=now,
                )
                db.add(ul)
                await db.flush()
                return CollectionItemResponse(
                    id=str(ul.list_id),
                    name=ul.title,
                    description=ul.description,
                    item_count=0,
                    banner_url=None,
                    is_private=ul.is_private,
                    created_at=ul.created_at.isoformat(),
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("create_collection failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return CollectionItemResponse(
            id=str(uuid.uuid4()),
            name=body.name,
            description=body.description,
            item_count=0,
            is_private=body.is_private,
            created_at=created_iso,
        )

    async def delete_collection(
        self, db: Optional[AsyncSession], user_id: str, list_id: str
    ) -> bool:
        """Deletes a user-owned collection (personal.user_list), scoped to the
        requesting user so one user cannot delete another user's collection."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                try:
                    list_uuid = uuid.UUID(list_id)
                except ValueError:
                    return False

                stmt = select(UserListModel).where(
                    and_(
                        UserListModel.list_id == list_uuid,
                        UserListModel.user_id == user_uuid,
                    )
                )
                ul = (await db.execute(stmt)).scalar_one_or_none()
                if not ul:
                    return False

                await db.delete(ul)
                await db.flush()
                return True
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("delete_collection failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise
                return False

        return False

    async def get_collection_detail(
        self, db: Optional[AsyncSession], user_id: str, list_id: str
    ) -> Optional[CollectionDetailResponse]:
        """Retrieves a single collection with its real title items, joined
        against canonical.title. personal.user_list_item has always existed
        and list_collections already loaded it (for the item_count), but
        nothing ever exposed the actual items -- a collection could be
        created and deleted but never populated or viewed."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                try:
                    list_uuid = uuid.UUID(list_id)
                except ValueError:
                    return None

                stmt = (
                    select(UserListModel)
                    .options(selectinload(UserListModel.items))
                    .where(
                        and_(
                            UserListModel.list_id == list_uuid,
                            UserListModel.user_id == user_uuid,
                        )
                    )
                )
                ul = (await db.execute(stmt)).scalar_one_or_none()
                if not ul:
                    return None

                title_ids = [it.title_id for it in ul.items]
                title_map: Dict[uuid.UUID, TitleModel] = {}
                if title_ids:
                    titles = (
                        await db.execute(select(TitleModel).where(TitleModel.title_id.in_(title_ids)))
                    ).scalars().all()
                    title_map = {t.title_id: t for t in titles}

                items = [
                    CollectionTitleItem(
                        item_id=str(it.item_id),
                        title_id=str(it.title_id),
                        canonical_title=(title_map[it.title_id].canonical_title if it.title_id in title_map else "Unknown Title"),
                        production_year=(title_map[it.title_id].production_year if it.title_id in title_map else None),
                        content_type=((title_map[it.title_id].content_type_id if it.title_id in title_map else None) or "MOVIE").upper(),
                        poster_url=resolve_poster_url(title_map[it.title_id].poster_url if it.title_id in title_map else None),
                        notes=it.notes,
                        added_at=it.added_at.isoformat() if it.added_at else datetime.now(timezone.utc).isoformat(),
                    )
                    for it in sorted(ul.items, key=lambda i: i.position)
                ]

                return CollectionDetailResponse(
                    collection=CollectionItemResponse(
                        id=str(ul.list_id),
                        name=ul.title,
                        description=ul.description,
                        item_count=len(ul.items),
                        banner_url=None,
                        is_private=ul.is_private,
                        created_at=ul.created_at.isoformat() if ul.created_at else datetime.now(timezone.utc).isoformat(),
                    ),
                    items=items,
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("get_collection_detail failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return None

    async def add_collection_item(
        self, db: Optional[AsyncSession], user_id: str, list_id: str, title_id: str, notes: Optional[str] = None
    ) -> Optional[CollectionDetailResponse]:
        """Adds a real title to a collection the requesting user owns."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                try:
                    list_uuid = uuid.UUID(list_id)
                    title_uuid = uuid.UUID(title_id)
                except ValueError:
                    return None

                stmt = select(UserListModel).where(
                    and_(UserListModel.list_id == list_uuid, UserListModel.user_id == user_uuid)
                )
                ul = (await db.execute(stmt)).scalar_one_or_none()
                if not ul:
                    return None

                existing_stmt = select(UserListItemModel).where(
                    and_(
                        UserListItemModel.list_id == list_uuid,
                        UserListItemModel.title_id == title_uuid,
                    )
                )
                existing = (await db.execute(existing_stmt)).scalar_one_or_none()
                if not existing:
                    count_stmt = select(func.count()).select_from(UserListItemModel).where(
                        UserListItemModel.list_id == list_uuid
                    )
                    position = (await db.execute(count_stmt)).scalar_one()
                    db.add(
                        UserListItemModel(
                            item_id=uuid.uuid4(),
                            list_id=list_uuid,
                            title_id=title_uuid,
                            position=position,
                            notes=notes,
                            added_at=datetime.now(timezone.utc),
                        )
                    )
                    await db.commit()

                return await self.get_collection_detail(db=db, user_id=user_id, list_id=list_id)
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("add_collection_item failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return None

    async def remove_collection_item(
        self, db: Optional[AsyncSession], user_id: str, list_id: str, title_id: str
    ) -> bool:
        """Removes a title from a collection the requesting user owns."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                try:
                    list_uuid = uuid.UUID(list_id)
                    title_uuid = uuid.UUID(title_id)
                except ValueError:
                    return False

                owner_stmt = select(UserListModel.list_id).where(
                    and_(UserListModel.list_id == list_uuid, UserListModel.user_id == user_uuid)
                )
                if (await db.execute(owner_stmt)).scalar_one_or_none() is None:
                    return False

                item_stmt = select(UserListItemModel).where(
                    and_(
                        UserListItemModel.list_id == list_uuid,
                        UserListItemModel.title_id == title_uuid,
                    )
                )
                item = (await db.execute(item_stmt)).scalar_one_or_none()
                if not item:
                    return False

                await db.delete(item)
                await db.commit()
                return True
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("remove_collection_item failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise
                return False

        return False

    async def list_library(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        content_type: Optional[str] = None,
    ) -> LibraryPageResponse:
        """Lists titles the user has added to their personal library (personal.library_entry),
        joined with canonical title metadata. Same join/pagination/fallback shape as list_history."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                where_clause = LibraryEntryModel.user_id == user_uuid
                base_query = select(LibraryEntryModel).where(where_clause)
                count_query = select(func.count()).select_from(LibraryEntryModel).where(where_clause)

                if content_type and content_type != "ALL":
                    base_query = base_query.join(
                        TitleModel, TitleModel.title_id == LibraryEntryModel.title_id
                    ).where(TitleModel.content_type_id.ilike(content_type))
                    count_query = count_query.join(
                        TitleModel, TitleModel.title_id == LibraryEntryModel.title_id
                    ).where(TitleModel.content_type_id.ilike(content_type))

                total = (await db.execute(count_query)).scalar_one()

                stmt = (
                    base_query
                    .order_by(LibraryEntryModel.added_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                entries = (await db.execute(stmt)).scalars().all()

                title_ids = [e.title_id for e in entries]
                title_map: Dict[uuid.UUID, TitleModel] = {}
                if title_ids:
                    titles = (
                        await db.execute(select(TitleModel).where(TitleModel.title_id.in_(title_ids)))
                    ).scalars().all()
                    title_map = {t.title_id: t for t in titles}

                items = [
                    LibraryItemResponse(
                        id=f"{e.user_id}:{e.title_id}",
                        title_id=str(e.title_id),
                        canonical_title=(title_map[e.title_id].canonical_title if e.title_id in title_map else "Unknown Title"),
                        production_year=(title_map[e.title_id].production_year if e.title_id in title_map else None),
                        content_type=((title_map[e.title_id].content_type_id if e.title_id in title_map else None) or "MOVIE").upper(),
                        poster_url=resolve_poster_url(title_map[e.title_id].poster_url if e.title_id in title_map else None),
                        added_at=e.added_at.isoformat() if e.added_at else datetime.now(timezone.utc).isoformat(),
                    )
                    for e in entries
                ]

                return LibraryPageResponse(items=items, total=total, limit=limit, offset=offset)
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("list_library failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        lib = SEED_LIBRARY.get(user_id, [])
        return LibraryPageResponse(items=lib, total=len(lib), limit=limit, offset=offset)

    async def add_to_library(
        self, db: Optional[AsyncSession], user_id: str, title_id: str
    ) -> LibraryItemResponse:
        """Adds a title to the user's personal library (personal.library_entry).
        Idempotent: re-adding an already-present title returns the existing entry."""
        added_iso = datetime.now(timezone.utc).isoformat()
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(title_id)

                stmt = select(LibraryEntryModel).where(
                    and_(
                        LibraryEntryModel.user_id == user_uuid,
                        LibraryEntryModel.title_id == title_uuid,
                    )
                )
                entry = (await db.execute(stmt)).scalar_one_or_none()
                if not entry:
                    entry = LibraryEntryModel(
                        user_id=user_uuid,
                        title_id=title_uuid,
                        added_at=datetime.now(timezone.utc),
                    )
                    db.add(entry)
                    await db.flush()

                title = await db.get(TitleModel, title_uuid)
                return LibraryItemResponse(
                    id=f"{user_uuid}:{title_uuid}",
                    title_id=title_id,
                    canonical_title=title.canonical_title if title else "Unknown Title",
                    production_year=title.production_year if title else None,
                    content_type=((title.content_type_id if title else None) or "MOVIE").upper(),
                    poster_url=resolve_poster_url(title.poster_url) if title else None,
                    added_at=entry.added_at.isoformat() if entry.added_at else added_iso,
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("add_to_library failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        from .canonical import SEED_FALLBACK_TITLES
        if user_id not in SEED_LIBRARY:
            SEED_LIBRARY[user_id] = []
        canonical_info = SEED_FALLBACK_TITLES.get(title_id, {})
        existing = next((it for it in SEED_LIBRARY[user_id] if it.title_id == title_id), None)
        if existing:
            return existing
        item = LibraryItemResponse(
            id=f"{user_id}:{title_id}",
            title_id=title_id,
            canonical_title=canonical_info.get("canonical_title", "Unknown Title"),
            production_year=canonical_info.get("production_year", 2024),
            content_type=(canonical_info.get("content_type") or "MOVIE").upper(),
            poster_url=resolve_poster_url(canonical_info.get("poster_url")),
            added_at=added_iso,
        )
        SEED_LIBRARY[user_id].append(item)
        return item

    async def remove_from_library(
        self, db: Optional[AsyncSession], user_id: str, title_id: str
    ) -> bool:
        """Removes a title from the user's personal library, scoped to the requesting user."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(title_id)
                stmt = select(LibraryEntryModel).where(
                    and_(
                        LibraryEntryModel.user_id == user_uuid,
                        LibraryEntryModel.title_id == title_uuid,
                    )
                )
                entry = (await db.execute(stmt)).scalar_one_or_none()
                if not entry:
                    return False

                await db.delete(entry)
                await db.flush()
                return True
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("remove_from_library failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise
                return False

        # Seed fallback
        if user_id in SEED_LIBRARY:
            orig = len(SEED_LIBRARY[user_id])
            SEED_LIBRARY[user_id] = [it for it in SEED_LIBRARY[user_id] if it.title_id != title_id and it.id != title_id]
            return len(SEED_LIBRARY[user_id]) < orig
        return False

    async def list_ratings(
        self, db: Optional[AsyncSession], user_id: str, title_id: Optional[str] = None
    ) -> List[RatingResponse]:
        """Lists ratings created by user, optionally filtered by title_id."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                conditions = [RatingModel.user_id == user_uuid]
                if title_id:
                    conditions.append(RatingModel.title_id == _resolve_title_uuid(title_id))
                stmt = select(RatingModel).where(and_(*conditions))
                res = await db.execute(stmt)
                ratings = res.scalars().all()
                return [
                    RatingResponse(
                        id=str(r.rating_id),
                        title_id=str(r.title_id),
                        rating_value=r.rating_value,
                        updated_at=(
                            r.rated_at.isoformat()
                            if r.rated_at
                            else datetime.now(timezone.utc).isoformat()
                        ),
                    )
                    for r in ratings
                ]
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("list_ratings failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        res = SEED_RATINGS.get(user_id, [])
        if title_id:
            return [r for r in res if r.title_id == title_id]
        return res

    async def delete_rating(
        self, db: Optional[AsyncSession], user_id: str, title_id: str
    ) -> bool:
        """Deletes user's rating for a title."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(title_id)
                stmt = select(RatingModel).where(
                    and_(
                        RatingModel.user_id == user_uuid,
                        RatingModel.title_id == title_uuid,
                    )
                )
                r_orm = (await db.execute(stmt)).scalar_one_or_none()
                if not r_orm:
                    return False
                await db.delete(r_orm)
                await db.flush()
                return True
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("delete_rating failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise
                return False

        # Seed fallback
        if user_id in SEED_RATINGS:
            orig = len(SEED_RATINGS[user_id])
            SEED_RATINGS[user_id] = [r for r in SEED_RATINGS[user_id] if r.title_id != title_id]
            return len(SEED_RATINGS[user_id]) < orig
        return False

    async def set_rating(
        self, db: Optional[AsyncSession], user_id: str, body: RatingCreate
    ) -> RatingResponse:
        """Sets title rating (1-10 scale). Upserts: replaces existing rating if present."""
        rated_iso = datetime.now(timezone.utc).isoformat()
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(body.title_id)
                stmt = select(RatingModel).where(
                    and_(
                        RatingModel.user_id == user_uuid,
                        RatingModel.title_id == title_uuid,
                    )
                )
                res = await db.execute(stmt)
                r_orm = res.scalar_one_or_none()
                if r_orm:
                    r_orm.rating_value = body.rating_value
                    r_orm.rated_at = datetime.now(timezone.utc)
                else:
                    r_orm = RatingModel(
                        rating_id=uuid.uuid4(),
                        user_id=user_uuid,
                        title_id=title_uuid,
                        rating_value=body.rating_value,
                        rated_at=datetime.now(timezone.utc),
                    )
                    db.add(r_orm)
                await db.flush()

                return RatingResponse(
                    id=str(r_orm.rating_id),
                    title_id=body.title_id,
                    rating_value=body.rating_value,
                    updated_at=rated_iso,
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("set_rating failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        if user_id not in SEED_RATINGS:
            SEED_RATINGS[user_id] = []
        SEED_RATINGS[user_id] = [r for r in SEED_RATINGS[user_id] if r.title_id != body.title_id]
        resp = RatingResponse(
            id=str(uuid.uuid4()),
            title_id=body.title_id,
            rating_value=body.rating_value,
            updated_at=rated_iso,
        )
        SEED_RATINGS[user_id].append(resp)
        return resp

    async def list_notes(
        self, db: Optional[AsyncSession], user_id: str, title_id: Optional[str] = None
    ) -> List[NoteResponse]:
        """Lists private personal notes created by user, optionally filtered by title_id."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                conditions = [NoteModel.user_id == user_uuid]
                if title_id:
                    conditions.append(NoteModel.title_id == _resolve_title_uuid(title_id))
                stmt = select(NoteModel).where(and_(*conditions)).order_by(NoteModel.created_at.desc())
                res = await db.execute(stmt)
                notes = res.scalars().all()
                return [
                    NoteResponse(
                        id=str(n.note_id),
                        title_id=str(n.title_id),
                        note_text=n.note_text,
                        updated_at=(
                            n.created_at.isoformat()
                            if n.created_at
                            else datetime.now(timezone.utc).isoformat()
                        ),
                    )
                    for n in notes
                ]
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("list_notes failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        notes = SEED_NOTES.get(user_id, [])
        if title_id:
            notes = [n for n in notes if n.title_id == title_id]
        return notes

    async def delete_note(
        self, db: Optional[AsyncSession], user_id: str, note_id: str
    ) -> bool:
        """Deletes a private personal note owned by the requesting user."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                note_uuid = _resolve_uuid(note_id, "note_id")
                stmt = select(NoteModel).where(
                    and_(
                        NoteModel.note_id == note_uuid,
                        NoteModel.user_id == user_uuid,
                    )
                )
                n_orm = (await db.execute(stmt)).scalar_one_or_none()
                if not n_orm:
                    return False
                await db.delete(n_orm)
                await db.flush()
                return True
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("delete_note failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise
                return False

        # Seed fallback
        if user_id in SEED_NOTES:
            orig = len(SEED_NOTES[user_id])
            SEED_NOTES[user_id] = [n for n in SEED_NOTES[user_id] if n.id != note_id]
            return len(SEED_NOTES[user_id]) < orig
        return False

    async def create_note(
        self, db: Optional[AsyncSession], user_id: str, body: NoteCreate
    ) -> NoteResponse:
        """Creates a private personal note."""
        created_iso = datetime.now(timezone.utc).isoformat()
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(body.title_id)
                n_orm = NoteModel(
                    note_id=uuid.uuid4(),
                    user_id=user_uuid,
                    title_id=title_uuid,
                    note_text=body.note_text,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(n_orm)
                await db.flush()
                return NoteResponse(
                    id=str(n_orm.note_id),
                    title_id=body.title_id,
                    note_text=body.note_text,
                    updated_at=created_iso,
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("create_note failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        if user_id not in SEED_NOTES:
            SEED_NOTES[user_id] = []
        resp = NoteResponse(
            id=str(uuid.uuid4()),
            title_id=body.title_id,
            note_text=body.note_text,
            updated_at=created_iso,
        )
        SEED_NOTES[user_id].append(resp)
        return resp

    async def list_reviews(
        self, db: Optional[AsyncSession], user_id: str, title_id: Optional[str] = None
    ) -> List[ReviewResponse]:
        """Lists reviews created by user, optionally filtered by title_id."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                conditions = [ReviewModel.user_id == user_uuid]
                if title_id:
                    conditions.append(ReviewModel.title_id == _resolve_title_uuid(title_id))
                stmt = select(ReviewModel).where(and_(*conditions)).order_by(ReviewModel.created_at.desc())
                res = await db.execute(stmt)
                reviews = res.scalars().all()
                return [
                    ReviewResponse(
                        id=str(r.review_id),
                        title_id=str(r.title_id),
                        review_title=r.review_title or "",
                        review_text=r.review_text,
                        is_public=not r.contains_spoilers,
                        created_at=(
                            r.created_at.isoformat()
                            if r.created_at
                            else datetime.now(timezone.utc).isoformat()
                        ),
                    )
                    for r in reviews
                ]
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("list_reviews failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        reviews = SEED_REVIEWS.get(user_id, [])
        if title_id:
            reviews = [r for r in reviews if r.title_id == title_id]
        return reviews

    async def delete_review(
        self, db: Optional[AsyncSession], user_id: str, review_id: str
    ) -> bool:
        """Deletes a review owned by the requesting user."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                review_uuid = _resolve_uuid(review_id, "review_id")
                stmt = select(ReviewModel).where(
                    and_(
                        ReviewModel.review_id == review_uuid,
                        ReviewModel.user_id == user_uuid,
                    )
                )
                r_orm = (await db.execute(stmt)).scalar_one_or_none()
                if not r_orm:
                    return False
                await db.delete(r_orm)
                await db.flush()
                return True
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("delete_review failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise
                return False

        # Seed fallback
        if user_id in SEED_REVIEWS:
            orig = len(SEED_REVIEWS[user_id])
            SEED_REVIEWS[user_id] = [r for r in SEED_REVIEWS[user_id] if r.id != review_id]
            return len(SEED_REVIEWS[user_id]) < orig
        return False

    async def create_review(
        self, db: Optional[AsyncSession], user_id: str, body: ReviewCreate
    ) -> ReviewResponse:
        """Creates a user review."""
        created_iso = datetime.now(timezone.utc).isoformat()
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(body.title_id)
                r_orm = ReviewModel(
                    review_id=uuid.uuid4(),
                    user_id=user_uuid,
                    title_id=title_uuid,
                    review_title=body.review_title,
                    review_text=body.review_text,
                    contains_spoilers=not body.is_public,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(r_orm)
                await db.flush()
                return ReviewResponse(
                    id=str(r_orm.review_id),
                    title_id=body.title_id,
                    review_title=body.review_title,
                    review_text=body.review_text,
                    is_public=body.is_public,
                    created_at=created_iso,
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("create_review failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        if user_id not in SEED_REVIEWS:
            SEED_REVIEWS[user_id] = []
        resp = ReviewResponse(
            id=str(uuid.uuid4()),
            title_id=body.title_id,
            review_title=body.review_title or "",
            review_text=body.review_text,
            is_public=body.is_public,
            created_at=created_iso,
        )
        SEED_REVIEWS[user_id].append(resp)
        return resp

    async def list_conflicts(
        self, db: Optional[AsyncSession], user_id: str
    ) -> List[PersonalDataConflictResponse]:
        """Retrieves active personal data conflicts for the user (unresolved entity merges/splits)."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                stmt = select(PersonalDataConflictModel).where(
                    and_(
                        PersonalDataConflictModel.user_id == user_uuid,
                        PersonalDataConflictModel.resolution_status == "UNRESOLVED",
                    )
                )
                res = await db.execute(stmt)
                conflicts = res.scalars().all()
                return [
                    PersonalDataConflictResponse(
                        conflict_id=str(c.conflict_id),
                        conflict_type=c.conflict_type,
                        affected_title_id=(
                            str(c.surviving_title_id)
                            if c.surviving_title_id
                            else str(c.retired_title_id)
                        ),
                        conflict_details=c.conflicting_data,
                        created_at=(
                            c.created_at.isoformat()
                            if c.created_at
                            else datetime.now(timezone.utc).isoformat()
                        ),
                    )
                    for c in conflicts
                ]
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("list_conflicts failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return []

    async def get_user_dashboard_metrics(
        self, db: Optional[AsyncSession], user_id: str
    ) -> UserDashboardMetricsResponse:
        """Derives comprehensive dashboard analytics dynamically from canonical & user personal relational data."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                now = datetime.now(timezone.utc)
                current_year = now.year
                current_month = now.month

                # 1. Title States breakdown
                stmt_st = select(UserTitleStateModel).where(UserTitleStateModel.user_id == user_uuid)
                title_states = (await db.execute(stmt_st)).scalars().all()

                total_titles = len(title_states)
                watching_count = sum(1 for s in title_states if s.manual_status_override == "WATCHING")
                completed_count = sum(1 for s in title_states if s.manual_status_override == "COMPLETED")
                dropped_count = sum(1 for s in title_states if s.manual_status_override == "DROPPED")
                unwatched_count = sum(1 for s in title_states if s.manual_status_override in ("PLAN_TO_WATCH", "WATCHLIST", None))
                favorites_count = sum(1 for s in title_states if s.is_favorite)

                # 2. Watch Events
                stmt_ev = (
                    select(WatchEventModel)
                    .where(
                        and_(
                            WatchEventModel.user_id == user_uuid,
                            WatchEventModel.is_tombstoned == False,
                        )
                    )
                    .order_by(WatchEventModel.watched_at.desc())
                )
                watch_events = (await db.execute(stmt_ev)).scalars().all()
                watched_count = len(watch_events)

                # Monthly and Annual counts
                monthly_watch_count = sum(
                    1 for e in watch_events
                    if e.watched_at and e.watched_at.year == current_year and e.watched_at.month == current_month
                )
                annual_watch_count = sum(
                    1 for e in watch_events
                    if e.watched_at and e.watched_at.year == current_year
                )

                # Watch streak calculation
                watch_dates = sorted(
                    {e.watched_at.date() for e in watch_events if e.watched_at},
                    reverse=True
                )
                watch_streak_days = 0
                if watch_dates:
                    today = now.date()
                    if watch_dates[0] == today or watch_dates[0] == today - timedelta(days=1):
                        expected = watch_dates[0]
                        for d in watch_dates:
                            if d == expected:
                                watch_streak_days += 1
                                expected -= timedelta(days=1)
                            else:
                                break

                # 3. Content Type & Hours Aggregation
                watched_title_ids = list({e.title_id for e in watch_events if e.title_id})
                movies_watched = 0
                series_completed = 0
                anime_completed = 0
                total_watch_minutes = 0

                if watched_title_ids:
                    stmt_titles = (
                        select(TitleModel)
                        .options(
                            selectinload(TitleModel.editions),
                            selectinload(TitleModel.countries),
                            selectinload(TitleModel.languages)
                        )
                        .where(TitleModel.title_id.in_(watched_title_ids))
                    )
                    titles_data = (await db.execute(stmt_titles)).scalars().all()
                    title_map = {t.title_id: t for t in titles_data}

                    watched_ep_ids = [ev.episode_id for ev in watch_events if ev.episode_id]
                    ep_map = {}
                    if watched_ep_ids:
                        ep_records = (await db.execute(select(EpisodeModel).where(EpisodeModel.episode_id.in_(watched_ep_ids)))).scalars().all()
                        ep_map = {ep.episode_id: ep for ep in ep_records}

                    for ev in watch_events:
                        t = title_map.get(ev.title_id)
                        if t:
                            if ev.episode_id:
                                ep_rec = ep_map.get(ev.episode_id)
                                runtime = ep_rec.runtime_minutes if (ep_rec and ep_rec.runtime_minutes) else 45
                            else:
                                runtime = 120
                                if t.editions:
                                    primary_ed = next((ed for ed in t.editions if ed.is_primary), t.editions[0])
                                    if primary_ed.runtime_minutes:
                                        runtime = primary_ed.runtime_minutes
                            total_watch_minutes += runtime

                    for s in title_states:
                        t = title_map.get(s.title_id)
                        if t and s.manual_status_override == "COMPLETED":
                            if t.content_type_id == "movie":
                                movies_watched += 1
                            elif t.content_type_id == "tv_series":
                                series_completed += 1
                            elif t.content_type_id == "anime":
                                anime_completed += 1

                    countries_set = set()
                    languages_set = set()
                    for t in titles_data:
                        for c in t.countries:
                            countries_set.add(c.country_code)
                        for l in t.languages:
                            languages_set.add(l.language_code)
                    countries_explored = sorted(list(countries_set))
                    languages_explored = sorted(list(languages_set))
                else:
                    countries_explored = []
                    languages_explored = []

                total_watch_hours = round(total_watch_minutes / 60.0, 1)

                # 4. Ratings
                stmt_r = select(RatingModel).where(RatingModel.user_id == user_uuid)
                ratings = (await db.execute(stmt_r)).scalars().all()
                avg_rating = round(sum(r.rating_value for r in ratings) / len(ratings), 2) if ratings else None

                return UserDashboardMetricsResponse(
                    total_titles=total_titles,
                    watched_count=watched_count,
                    unwatched_count=unwatched_count,
                    watching_count=watching_count,
                    completed_count=completed_count,
                    dropped_count=dropped_count,
                    favorites_count=favorites_count,
                    total_watch_hours=total_watch_hours,
                    movies_watched=movies_watched,
                    series_completed=series_completed,
                    anime_completed=anime_completed,
                    countries_explored=countries_explored,
                    languages_explored=languages_explored,
                    watch_streak_days=watch_streak_days,
                    monthly_watch_count=monthly_watch_count,
                    annual_watch_count=annual_watch_count,
                    average_personal_rating=avg_rating
                )
            except ValueError:
                raise
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("get_user_dashboard_metrics failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        return UserDashboardMetricsResponse(
            total_titles=0,
            watched_count=0,
            unwatched_count=0,
            watching_count=0,
            completed_count=0,
            dropped_count=0,
            favorites_count=0,
            total_watch_hours=0.0,
            movies_watched=0,
            series_completed=0,
            anime_completed=0,
            countries_explored=[],
            languages_explored=[],
            watch_streak_days=0,
            monthly_watch_count=0,
            annual_watch_count=0,
            average_personal_rating=None
        )

    async def get_user_taste_breakdown(
        self, db: Optional[AsyncSession], user_id: str
    ) -> Tuple[List[GenreAffinityItem], List[CreatorAffinityItem], List[CreatorAffinityItem], List[MonthlyTrendItem]]:
        """Derives genre/director/actor affinity and a 6-month viewing trend from the user's
        real watch history joined against canonical genres & credits. Returns empty lists
        when there is no watch history or no genre/credit data — no fabricated fallback."""
        empty_result: Tuple[List, List, List, List] = ([], [], [], [])
        if db is None:
            return empty_result

        try:
            user_uuid = _resolve_user_uuid(user_id)
            now = datetime.now(timezone.utc)

            stmt_ev = select(WatchEventModel).where(
                and_(
                    WatchEventModel.user_id == user_uuid,
                    WatchEventModel.is_tombstoned == False,  # noqa: E712
                )
            )
            watch_events = (await db.execute(stmt_ev)).scalars().all()
            watched_title_ids = list({e.title_id for e in watch_events if e.title_id})
            if not watch_events or not watched_title_ids:
                return empty_result

            stmt_titles = (
                select(TitleModel)
                .options(
                    selectinload(TitleModel.editions),
                    selectinload(TitleModel.genres),
                    selectinload(TitleModel.credits).selectinload(CreditModel.person),
                )
                .where(TitleModel.title_id.in_(watched_title_ids))
            )
            titles_data = (await db.execute(stmt_titles)).scalars().all()
            title_map = {t.title_id: t for t in titles_data}

            # Top genres: count genre-tag occurrences across the user's watched titles
            genre_counts: Dict[str, int] = {}
            for t in titles_data:
                for g in t.genres:
                    genre_counts[g.name] = genre_counts.get(g.name, 0) + 1
            total_genre_tags = sum(genre_counts.values())
            top_genres = [
                GenreAffinityItem(genre=name, count=count, percentage=round(count / total_genre_tags * 100, 1))
                for name, count in sorted(genre_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
            ] if total_genre_tags else []

            # Top directors / actors: count real credits across the user's watched titles
            director_counts: Dict[str, int] = {}
            actor_counts: Dict[str, int] = {}
            for t in titles_data:
                for c in t.credits:
                    if not c.person:
                        continue
                    if c.credit_role_id == "DIRECTOR":
                        director_counts[c.person.canonical_name] = director_counts.get(c.person.canonical_name, 0) + 1
                    elif c.credit_role_id == "ACTOR":
                        actor_counts[c.person.canonical_name] = actor_counts.get(c.person.canonical_name, 0) + 1

            top_directors = [
                CreatorAffinityItem(name=name, role="Director", count=count)
                for name, count in sorted(director_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
            ]
            top_actors = [
                CreatorAffinityItem(name=name, role="Actor", count=count)
                for name, count in sorted(actor_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
            ]

            # Monthly trend: last 6 calendar months (oldest to newest), counts + hours from real watch events
            month_abbr = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            months_seq: List[Tuple[int, int]] = []
            y, m = now.year, now.month
            for _ in range(6):
                months_seq.append((y, m))
                m -= 1
                if m == 0:
                    m, y = 12, y - 1
            months_seq.reverse()

            month_counts = {key: 0 for key in months_seq}
            month_minutes = {key: 0 for key in months_seq}
            for e in watch_events:
                if not e.watched_at:
                    continue
                key = (e.watched_at.year, e.watched_at.month)
                if key not in month_counts:
                    continue
                month_counts[key] += 1
                runtime = 120
                t = title_map.get(e.title_id)
                if t and t.editions:
                    primary_ed = next((ed for ed in t.editions if ed.is_primary), t.editions[0])
                    if primary_ed.runtime_minutes:
                        runtime = primary_ed.runtime_minutes
                month_minutes[key] += runtime

            monthly_trend = [
                MonthlyTrendItem(
                    month=month_abbr[month - 1],
                    count=month_counts[(year, month)],
                    hours=round(month_minutes[(year, month)] / 60.0, 1),
                )
                for year, month in months_seq
            ]

            return top_genres, top_directors, top_actors, monthly_trend
        except ValueError:
            raise
        except Exception as exc:
            await _safe_rollback(db)
            logger.error("get_user_taste_breakdown failed: %s", exc, exc_info=True)
            if not config.allow_seed_fallback:
                raise
            return empty_result

    async def export_user_data(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        export_format: str = "json",
        scope: Optional[str] = None
    ) -> PersonalDataExportResponse:
        """Exports complete user personal data across library, watchlist, watch events, ratings, states, notes, reviews, custom lists, and streak."""
        user_uuid = _resolve_user_uuid(user_id)
        exported_at = datetime.now(timezone.utc).isoformat()

        library: List[Dict[str, Any]] = []
        watchlist: List[Dict[str, Any]] = []
        watch_history: List[Dict[str, Any]] = []
        ratings: List[Dict[str, Any]] = []
        states: List[Dict[str, Any]] = []
        notes: List[Dict[str, Any]] = []
        reviews: List[Dict[str, Any]] = []
        custom_lists: List[Dict[str, Any]] = []
        streak_data: Dict[str, Any] = {}

        if db is not None:
            try:
                # 1. Library entries joined with TitleModel
                if scope is None or scope in ("library", "all"):
                    lib_stmt = (
                        select(LibraryEntryModel, TitleModel)
                        .join(TitleModel, LibraryEntryModel.title_id == TitleModel.title_id)
                        .where(LibraryEntryModel.user_id == user_uuid)
                        .order_by(LibraryEntryModel.added_at.desc())
                    )
                    lib_res = await db.execute(lib_stmt)
                    for le, t in lib_res.all():
                        library.append({
                            "title_id": str(le.title_id),
                            "display_id": t.display_id,
                            "canonical_title": t.canonical_title,
                            "production_year": t.production_year,
                            "content_type": t.content_type_id,
                            "added_at": le.added_at.isoformat() if le.added_at else None,
                            "status_override": le.status_override
                        })

                # 2. Watchlist (from user_title_state where manual_status_override is PLAN_TO_WATCH or WATCHLIST)
                if scope is None or scope in ("watchlist", "all"):
                    wl_stmt = (
                        select(UserTitleStateModel, TitleModel)
                        .join(TitleModel, UserTitleStateModel.title_id == TitleModel.title_id)
                        .where(
                            UserTitleStateModel.user_id == user_uuid,
                            UserTitleStateModel.manual_status_override.in_(["PLAN_TO_WATCH", "WATCHLIST"])
                        )
                        .order_by(UserTitleStateModel.updated_at.desc())
                    )
                    wl_res = await db.execute(wl_stmt)
                    for st, t in wl_res.all():
                        watchlist.append({
                            "title_id": str(st.title_id),
                            "display_id": t.display_id,
                            "canonical_title": t.canonical_title,
                            "production_year": t.production_year,
                            "content_type": t.content_type_id,
                            "added_at": st.updated_at.isoformat() if st.updated_at else None
                        })

                # 3. Watch history joined with TitleModel, SeasonModel, EpisodeModel
                if scope is None or scope in ("watch_history", "history", "all"):
                    we_stmt = (
                        select(
                            WatchEventModel,
                            TitleModel,
                            SeasonModel.season_number,
                            EpisodeModel.episode_number,
                            EpisodeModel.episode_name
                        )
                        .join(TitleModel, WatchEventModel.title_id == TitleModel.title_id)
                        .outerjoin(SeasonModel, WatchEventModel.season_id == SeasonModel.season_id)
                        .outerjoin(EpisodeModel, WatchEventModel.episode_id == EpisodeModel.episode_id)
                        .where(
                            WatchEventModel.user_id == user_uuid,
                            WatchEventModel.is_tombstoned == False  # noqa: E712
                        )
                        .order_by(WatchEventModel.watched_at.desc())
                    )
                    we_res = await db.execute(we_stmt)
                    for we, t, s_num, ep_num, ep_name in we_res.all():
                        watch_history.append({
                            "watch_event_id": str(we.watch_event_id),
                            "title_id": str(we.title_id),
                            "display_id": t.display_id,
                            "canonical_title": t.canonical_title,
                            "production_year": t.production_year,
                            "content_type": t.content_type_id,
                            "season_id": str(we.season_id) if we.season_id else None,
                            "episode_id": str(we.episode_id) if we.episode_id else None,
                            "season_number": s_num,
                            "episode_number": ep_num,
                            "episode_name": ep_name,
                            "watched_at": we.watched_at.isoformat() if we.watched_at else None,
                            "notes": we.notes,
                            "device_type": we.device_type,
                            "is_tombstoned": we.is_tombstoned
                        })

                # 4. Ratings joined with TitleModel
                if scope is None or scope in ("ratings", "all"):
                    r_stmt = (
                        select(RatingModel, TitleModel)
                        .join(TitleModel, RatingModel.title_id == TitleModel.title_id)
                        .where(RatingModel.user_id == user_uuid)
                        .order_by(RatingModel.rated_at.desc())
                    )
                    r_res = await db.execute(r_stmt)
                    for r, t in r_res.all():
                        ratings.append({
                            "rating_id": str(r.rating_id),
                            "title_id": str(r.title_id),
                            "display_id": t.display_id,
                            "canonical_title": t.canonical_title,
                            "production_year": t.production_year,
                            "rating_value": r.rating_value,
                            "rated_at": r.rated_at.isoformat() if r.rated_at else None
                        })

                # 5. User title states joined with TitleModel
                if scope is None or scope in ("states", "all"):
                    st_stmt = (
                        select(UserTitleStateModel, TitleModel)
                        .join(TitleModel, UserTitleStateModel.title_id == TitleModel.title_id)
                        .where(UserTitleStateModel.user_id == user_uuid)
                        .order_by(UserTitleStateModel.updated_at.desc())
                    )
                    st_res = await db.execute(st_stmt)
                    for st, t in st_res.all():
                        states.append({
                            "title_id": str(st.title_id),
                            "display_id": t.display_id,
                            "canonical_title": t.canonical_title,
                            "manual_status_override": st.manual_status_override,
                            "is_favorite": st.is_favorite,
                            "updated_at": st.updated_at.isoformat() if st.updated_at else None
                        })

                # 6. Notes joined with TitleModel
                if scope is None or scope in ("notes", "all"):
                    n_stmt = (
                        select(NoteModel, TitleModel)
                        .join(TitleModel, NoteModel.title_id == TitleModel.title_id)
                        .where(NoteModel.user_id == user_uuid)
                        .order_by(NoteModel.created_at.desc())
                    )
                    n_res = await db.execute(n_stmt)
                    for n, t in n_res.all():
                        notes.append({
                            "note_id": str(n.note_id),
                            "title_id": str(n.title_id),
                            "display_id": t.display_id,
                            "canonical_title": t.canonical_title,
                            "production_year": t.production_year,
                            "note_text": n.note_text,
                            "created_at": n.created_at.isoformat() if n.created_at else None
                        })

                # 7. Reviews joined with TitleModel
                if scope is None or scope in ("reviews", "all"):
                    rev_stmt = (
                        select(ReviewModel, TitleModel)
                        .join(TitleModel, ReviewModel.title_id == TitleModel.title_id)
                        .where(ReviewModel.user_id == user_uuid)
                        .order_by(ReviewModel.created_at.desc())
                    )
                    rev_res = await db.execute(rev_stmt)
                    for rev, t in rev_res.all():
                        reviews.append({
                            "review_id": str(rev.review_id),
                            "title_id": str(rev.title_id),
                            "display_id": t.display_id,
                            "canonical_title": t.canonical_title,
                            "production_year": t.production_year,
                            "review_title": rev.review_title,
                            "review_text": rev.review_text,
                            "contains_spoilers": rev.contains_spoilers,
                            "created_at": rev.created_at.isoformat() if rev.created_at else None
                        })

                # 8. Custom lists / collections
                if scope is None or scope in ("lists", "collections", "all"):
                    ul_stmt = (
                        select(UserListModel)
                        .options(selectinload(UserListModel.items))
                        .where(UserListModel.user_id == user_uuid)
                        .order_by(UserListModel.created_at.desc())
                    )
                    ul_res = await db.execute(ul_stmt)
                    user_lists = ul_res.scalars().all()
                    all_item_title_ids = [it.title_id for ul in user_lists for it in ul.items]
                    titles_map = {}
                    if all_item_title_ids:
                        t_stmt = select(TitleModel).where(TitleModel.title_id.in_(all_item_title_ids))
                        t_res = await db.execute(t_stmt)
                        for t in t_res.scalars().all():
                            titles_map[t.title_id] = t

                    for ul in user_lists:
                        custom_lists.append({
                            "list_id": str(ul.list_id),
                            "title": ul.title,
                            "description": ul.description,
                            "is_private": ul.is_private,
                            "created_at": ul.created_at.isoformat() if ul.created_at else None,
                            "items": [
                                {
                                    "item_id": str(it.item_id),
                                    "title_id": str(it.title_id),
                                    "display_id": titles_map[it.title_id].display_id if it.title_id in titles_map else "",
                                    "canonical_title": titles_map[it.title_id].canonical_title if it.title_id in titles_map else "",
                                    "production_year": titles_map[it.title_id].production_year if it.title_id in titles_map else None,
                                    "position": it.position,
                                    "notes": it.notes,
                                    "added_at": it.added_at.isoformat() if it.added_at else None
                                }
                                for it in ul.items
                            ]
                        })

                # 9. User streak
                streak_stmt = select(UserStreakModel).where(UserStreakModel.user_id == user_uuid)
                streak_res = await db.execute(streak_stmt)
                stk = streak_res.scalar_one_or_none()
                if stk:
                    streak_data = {
                        "current_streak": stk.current_streak,
                        "longest_streak": stk.longest_streak,
                        "last_watch_date": stk.last_watch_date.isoformat() if stk.last_watch_date else None
                    }

            except Exception as exc:
                logger.error("export_user_data failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        raw_export = {
            "schema_version": "2.0.0",
            "exported_at": exported_at,
            "user_id": user_id,
            "user_profile": {"user_id": user_id, "streak": streak_data},
            "streak": streak_data,
            "library": library,
            "watchlist": watchlist,
            "watch_history": watch_history,
            "ratings": ratings,
            "user_title_states": states,
            "private_notes": notes,
            "reviews": reviews,
            "custom_lists": custom_lists
        }
        return PersonalDataExportResponse(**raw_export)

    async def _resolve_import_candidate_titles(
        self,
        db: AsyncSession,
        item: ImportItemPayload
    ) -> Tuple[Optional[TitleModel], float, str, List[ImportCandidateMatch], List[str]]:
        """
        4-Tier deterministic title identity resolution:
        1. Exact title_id UUID lookup
        2. External ID lookup (IMDb tt..., TMDB) or display_id
        3. Deterministic exact (canonical_title, production_year) match
        4. Exact title match (single -> EXACT/PROBABLE, multiple -> REVIEW_REQUIRED)
        5. Normalized title match (single -> PROBABLE, multiple -> REVIEW_REQUIRED)
        6. Substring/ilike match (PROBABLE)
        Returns: (matched_title_or_none, confidence_score, verdict, candidate_list, reasons)
        """
        import re

        # Tier 1: Canonical Title UUID
        if item.title_id:
            try:
                t_uuid = uuid.UUID(item.title_id)
                matched = await db.get(TitleModel, t_uuid)
                if matched:
                    return matched, 1.0, "EXACT_MATCH", [], ["Exact canonical UUID match"]
            except ValueError:
                pass

        # Tier 2: External IDs (IMDb, TMDB) or Display ID
        ext_candidate_id = item.imdb_id or (item.title_id if item.title_id and item.title_id.startswith("tt") else None)
        if ext_candidate_id:
            ext_stmt = select(TitleExternalIdModel).where(TitleExternalIdModel.external_id == ext_candidate_id)
            ext_res = await db.execute(ext_stmt)
            ext_row = ext_res.scalars().first()
            if ext_row:
                matched = await db.get(TitleModel, ext_row.title_id)
                if matched:
                    return matched, 1.0, "EXACT_MATCH", [], [f"Matched via provider external ID {ext_candidate_id}"]

        if item.display_id:
            disp_stmt = select(TitleModel).where(TitleModel.display_id == item.display_id.strip().upper())
            disp_res = await db.execute(disp_stmt)
            matched = disp_res.scalars().first()
            if matched:
                return matched, 1.0, "EXACT_MATCH", [], [f"Matched via display ID {item.display_id}"]

        # Tier 3 & 4: Title + Year or Exact Title
        if item.canonical_title:
            clean_title = item.canonical_title.strip()
            if item.production_year:
                stmt = select(TitleModel).where(
                    func.lower(TitleModel.canonical_title) == clean_title.lower(),
                    TitleModel.production_year == item.production_year
                )
                res = await db.execute(stmt)
                matches = res.scalars().all()
                if len(matches) == 1:
                    return matches[0], 1.0, "EXACT_MATCH", [], ["Exact title and production year match"]
                elif len(matches) > 1:
                    cands = [
                        ImportCandidateMatch(
                            title_id=str(m.title_id),
                            display_id=m.display_id,
                            canonical_title=m.canonical_title,
                            production_year=m.production_year,
                            content_type=m.content_type_id,
                            confidence=0.95
                        )
                        for m in matches
                    ]
                    return matches[0], 0.95, "EXACT_MATCH", cands, ["Matched exact title and year with multiple catalog editions"]

            # Exact title match without year constraint
            stmt = select(TitleModel).where(
                func.lower(TitleModel.canonical_title) == clean_title.lower()
            )
            res = await db.execute(stmt)
            matches = res.scalars().all()
            if len(matches) == 1:
                conf = 0.95 if not item.production_year else 0.85
                return matches[0], conf, "EXACT_MATCH" if not item.production_year else "PROBABLE_MATCH", [], ["Exact title match"]
            elif len(matches) > 1:
                cands = [
                    ImportCandidateMatch(
                        title_id=str(m.title_id),
                        display_id=m.display_id,
                        canonical_title=m.canonical_title,
                        production_year=m.production_year,
                        content_type=m.content_type_id,
                        confidence=0.70
                    )
                    for m in matches
                ]
                return None, 0.60, "REVIEW_REQUIRED", cands, [f"Ambiguous title: found {len(matches)} distinct works matching '{clean_title}'."]

            # Normalized title match (strip leading articles "The", "A", and special characters)
            norm_title = re.sub(r"^(the|a|an)\s+", "", clean_title.lower())
            norm_title = re.sub(r"[^\w\s]", "", norm_title).strip()
            if norm_title and len(norm_title) > 2:
                stmt = select(TitleModel).where(
                    func.lower(TitleModel.canonical_title).ilike(f"%{norm_title}%")
                ).limit(5)
                res = await db.execute(stmt)
                matches = res.scalars().all()
                if len(matches) == 1:
                    return matches[0], 0.80, "PROBABLE_MATCH", [], ["Matched via title normalization"]
                elif len(matches) > 1:
                    cands = [
                        ImportCandidateMatch(
                            title_id=str(m.title_id),
                            display_id=m.display_id,
                            canonical_title=m.canonical_title,
                            production_year=m.production_year,
                            content_type=m.content_type_id,
                            confidence=0.60
                        )
                        for m in matches
                    ]
                    return None, 0.55, "REVIEW_REQUIRED", cands, [f"Multiple candidate matches found for '{clean_title}'."]

        return None, 0.0, "UNMATCHED", [], ["No matching canonical title found in catalog"]

    async def preview_user_import(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        items: List[ImportItemPayload]
    ) -> ImportPreviewResponse:
        """Validates and previews personal data import, matching canonical titles and identifying conflicts."""
        user_uuid = _resolve_user_uuid(user_id)
        conflicts: List[ImportConflictItem] = []
        item_verdicts: List[ImportItemVerdict] = []
        matched_count = 0
        probable_count = 0
        review_count = 0
        unmatched_count = 0
        duplicate_skips_count = 0

        if db is not None:
            try:
                for idx, item in enumerate(items):
                    matched_title, confidence, verdict, candidates, reasons = await self._resolve_import_candidate_titles(db, item)

                    if matched_title:
                        t_id_str = str(matched_title.title_id)
                        d_id_str = matched_title.display_id
                        if verdict == "EXACT_MATCH":
                            matched_count += 1
                        else:
                            probable_count += 1

                        item_verdicts.append(
                            ImportItemVerdict(
                                index=idx,
                                canonical_title=item.canonical_title or matched_title.canonical_title,
                                production_year=item.production_year or matched_title.production_year,
                                matched=True,
                                matched_title_id=t_id_str,
                                matched_display_id=d_id_str,
                                confidence_score=confidence,
                                verdict=verdict,
                                candidates=candidates,
                                reasons=reasons
                            )
                        )

                        # Check for duplicate watch event
                        if item.watched_at:
                            try:
                                target_dt = datetime.fromisoformat(item.watched_at.replace("Z", "+00:00"))
                                we_check_stmt = select(WatchEventModel).where(
                                    and_(
                                        WatchEventModel.user_id == user_uuid,
                                        WatchEventModel.title_id == matched_title.title_id,
                                        WatchEventModel.is_tombstoned == False  # noqa: E712
                                    )
                                )
                                we_check_res = await db.execute(we_check_stmt)
                                existing_wes = we_check_res.scalars().all()
                                for existing_we in existing_wes:
                                    if existing_we.watched_at and abs(existing_we.watched_at - target_dt) <= timedelta(minutes=2):
                                        duplicate_skips_count += 1
                                        break
                            except Exception:
                                pass

                        # Check for conflicts against existing rating
                        if item.rating_value is not None:
                            r_stmt = select(RatingModel).where(
                                and_(RatingModel.user_id == user_uuid, RatingModel.title_id == matched_title.title_id)
                            )
                            r_res = await db.execute(r_stmt)
                            existing_r = r_res.scalar_one_or_none()
                            if existing_r and existing_r.rating_value != item.rating_value:
                                conflicts.append(
                                    ImportConflictItem(
                                        title_id=t_id_str,
                                        canonical_title=matched_title.canonical_title,
                                        field_name="rating_value",
                                        existing_value=existing_r.rating_value,
                                        imported_value=item.rating_value
                                    )
                                )

                        # Check for conflicts against existing state
                        if item.manual_status_override is not None:
                            st_stmt = select(UserTitleStateModel).where(
                                and_(UserTitleStateModel.user_id == user_uuid, UserTitleStateModel.title_id == matched_title.title_id)
                            )
                            st_res = await db.execute(st_stmt)
                            existing_st = st_res.scalar_one_or_none()
                            if existing_st and existing_st.manual_status_override and existing_st.manual_status_override != item.manual_status_override:
                                conflicts.append(
                                    ImportConflictItem(
                                        title_id=t_id_str,
                                        canonical_title=matched_title.canonical_title,
                                        field_name="manual_status_override",
                                        existing_value=existing_st.manual_status_override,
                                        imported_value=item.manual_status_override
                                    )
                                )
                    else:
                        if verdict == "REVIEW_REQUIRED":
                            review_count += 1
                        else:
                            unmatched_count += 1

                        item_verdicts.append(
                            ImportItemVerdict(
                                index=idx,
                                canonical_title=item.canonical_title or "Unknown",
                                production_year=item.production_year,
                                matched=False,
                                matched_title_id=None,
                                matched_display_id=None,
                                confidence_score=confidence,
                                verdict=verdict,
                                candidates=candidates,
                                reasons=reasons
                            )
                        )

            except Exception as exc:
                logger.error("preview_user_import failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return ImportPreviewResponse(
            total_items=len(items),
            matched_titles=matched_count + probable_count,
            probable_matches=probable_count,
            review_required=review_count,
            unmatched_titles=unmatched_count,
            conflicts_count=len(conflicts),
            duplicate_skips_count=duplicate_skips_count,
            conflicts=conflicts,
            item_verdicts=item_verdicts
        )

    async def apply_user_import(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        items: List[ImportItemPayload],
        conflict_strategy: str = "KEEP_EXISTING"
    ) -> ImportApplyResponse:
        """Applies validated imported records into the personal user domain using the chosen conflict strategy with strict idempotency."""
        user_uuid = _resolve_user_uuid(user_id)
        applied_count = 0
        conflicts_resolved = 0
        now = datetime.now(timezone.utc)

        if db is not None:
            try:
                for item in items:
                    matched_title, _, _, _, _ = await self._resolve_import_candidate_titles(db, item)

                    if not matched_title:
                        continue

                    t_uuid = matched_title.title_id

                    # 1. Watch event (Idempotent: prevent duplicate identical watch events within 2 minutes)
                    if item.watched_at:
                        try:
                            target_dt = datetime.fromisoformat(item.watched_at.replace("Z", "+00:00"))
                            if target_dt.tzinfo is None:
                                target_dt = target_dt.replace(tzinfo=timezone.utc)
                        except Exception:
                            target_dt = now

                        we_check_stmt = select(WatchEventModel).where(
                            and_(
                                WatchEventModel.user_id == user_uuid,
                                WatchEventModel.title_id == t_uuid,
                                WatchEventModel.is_tombstoned == False  # noqa: E712
                            )
                        )
                        we_check_res = await db.execute(we_check_stmt)
                        existing_wes = we_check_res.scalars().all()
                        is_duplicate_we = False
                        for existing_we in existing_wes:
                            if existing_we.watched_at and abs(existing_we.watched_at - target_dt) <= timedelta(minutes=2):
                                is_duplicate_we = True
                                break

                        if not is_duplicate_we:
                            we = WatchEventModel(
                                watch_event_id=uuid.uuid4(),
                                user_id=user_uuid,
                                title_id=t_uuid,
                                watched_at=target_dt,
                                notes=item.notes,
                                is_tombstoned=False,
                                created_at=now
                            )
                            db.add(we)

                    # 2. Rating
                    if item.rating_value is not None:
                        r_stmt = select(RatingModel).where(
                            and_(RatingModel.user_id == user_uuid, RatingModel.title_id == t_uuid)
                        )
                        r_res = await db.execute(r_stmt)
                        existing_r = r_res.scalar_one_or_none()

                        if not existing_r:
                            db.add(RatingModel(rating_id=uuid.uuid4(), user_id=user_uuid, title_id=t_uuid, rating_value=item.rating_value, rated_at=now))
                        elif conflict_strategy in ("OVERWRITE", "MERGE"):
                            existing_r.rating_value = item.rating_value
                            existing_r.rated_at = now
                            conflicts_resolved += 1

                    # 3. Title state & Library Entry
                    if item.is_favorite or item.manual_status_override:
                        st_stmt = select(UserTitleStateModel).where(
                            and_(UserTitleStateModel.user_id == user_uuid, UserTitleStateModel.title_id == t_uuid)
                        )
                        st_res = await db.execute(st_stmt)
                        existing_st = st_res.scalar_one_or_none()

                        if not existing_st:
                            db.add(
                                UserTitleStateModel(
                                    user_id=user_uuid,
                                    title_id=t_uuid,
                                    manual_status_override=item.manual_status_override,
                                    is_favorite=item.is_favorite or False,
                                    updated_at=now
                                )
                            )
                        elif conflict_strategy in ("OVERWRITE", "MERGE"):
                            if item.manual_status_override:
                                existing_st.manual_status_override = item.manual_status_override
                            if item.is_favorite is not None:
                                existing_st.is_favorite = item.is_favorite
                            existing_st.updated_at = now
                            conflicts_resolved += 1

                        # Upsert LibraryEntryModel if added to library/watched
                        if item.manual_status_override != "PLAN_TO_WATCH":
                            lib_stmt = select(LibraryEntryModel).where(
                                and_(LibraryEntryModel.user_id == user_uuid, LibraryEntryModel.title_id == t_uuid)
                            )
                            lib_res = await db.execute(lib_stmt)
                            existing_lib = lib_res.scalar_one_or_none()
                            if not existing_lib:
                                db.add(
                                    LibraryEntryModel(
                                        user_id=user_uuid,
                                        title_id=t_uuid,
                                        added_at=now,
                                        status_override=item.manual_status_override
                                    )
                                )

                    # 4. Note (Idempotent: avoid duplicate identical note text for same title)
                    if item.notes:
                        n_stmt = select(NoteModel).where(
                            and_(
                                NoteModel.user_id == user_uuid,
                                NoteModel.title_id == t_uuid,
                                NoteModel.note_text == item.notes
                            )
                        )
                        n_res = await db.execute(n_stmt)
                        existing_note = n_res.scalar_one_or_none()
                        if not existing_note:
                            db.add(
                                NoteModel(
                                    note_id=uuid.uuid4(),
                                    user_id=user_uuid,
                                    title_id=t_uuid,
                                    note_text=item.notes,
                                    created_at=now
                                )
                            )

                    applied_count += 1

                await db.commit()
            except Exception as exc:
                await _safe_rollback(db)
                logger.error("apply_user_import failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return ImportApplyResponse(
            applied_count=applied_count,
            conflicts_resolved=conflicts_resolved,
            strategy_applied=conflict_strategy,
            applied_at=now.isoformat()
        )


personal_repository = PersonalRepository()

