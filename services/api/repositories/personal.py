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
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.personal import (
    LibraryEntryModel, WatchEventModel, UserTitleStateModel,
    RatingModel, NoteModel, ReviewModel, PersonalDataConflictModel
)
from ..models.canonical import (
    TitleModel, EditionModel, TitleCountryModel, TitleLanguageModel
)
from ..schemas.personal import (
    WatchEventCreate, WatchEventResponse,
    UserTitleStateResponse, UserTitleStateUpdate,
    RatingCreate, RatingResponse,
    NoteCreate, NoteResponse,
    ReviewCreate, ReviewResponse,
    PersonalDataConflictResponse,
    UserDashboardMetricsResponse
)

logger = logging.getLogger("cinevault.repositories.personal")

# In-memory stores used ONLY in local_development when allow_seed_fallback=True
SEED_WATCH_EVENTS: Dict[str, List[WatchEventResponse]] = {}
SEED_RATINGS: Dict[str, List[RatingResponse]] = {}


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


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class PersonalRepository:
    """Provides async database operations for user personal library, watch history, and state."""

    async def list_watch_events(
        self, db: Optional[AsyncSession], user_id: str
    ) -> List[WatchEventResponse]:
        """Lists append-only watch events owned by the specified user (CAT-2)."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                stmt = (
                    select(WatchEventModel)
                    .where(
                        and_(
                            WatchEventModel.user_id == user_uuid,
                            WatchEventModel.is_tombstoned == False,  # noqa: E712
                        )
                    )
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
                await db.rollback()
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

                # Automatically maintain user title state
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
                        manual_status_override="COMPLETED",
                        is_favorite=False,
                        preferred_edition_id=edition_uuid,
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(st_orm)

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
                await db.rollback()
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
                await db.rollback()
                logger.error("get_user_title_state failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
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
        """Updates user title library state."""
        updated_iso = datetime.now(timezone.utc).isoformat()
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                title_uuid = _resolve_title_uuid(title_id)
                pref_ed_uuid = _resolve_edition_uuid(body.preferred_edition_id)

                stmt = select(UserTitleStateModel).where(
                    and_(
                        UserTitleStateModel.user_id == user_uuid,
                        UserTitleStateModel.title_id == title_uuid,
                    )
                )
                res = await db.execute(stmt)
                st = res.scalar_one_or_none()

                fav = body.is_favorite if body.is_favorite is not None else (st.is_favorite if st else False)
                status_override = body.manual_status_override or (st.manual_status_override if st else None)

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
                    preferred_edition_id=body.preferred_edition_id,
                    updated_at=updated_iso,
                )
            except ValueError:
                raise
            except Exception as exc:
                await db.rollback()
                logger.error("update_user_title_state failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return UserTitleStateResponse(
            title_id=title_id,
            derived_status=body.manual_status_override or "UNWATCHED",
            manual_status_override=body.manual_status_override,
            is_favorite=body.is_favorite if body.is_favorite is not None else False,
            preferred_edition_id=body.preferred_edition_id,
            updated_at=updated_iso,
        )

    async def list_ratings(
        self, db: Optional[AsyncSession], user_id: str
    ) -> List[RatingResponse]:
        """Lists ratings created by user."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                stmt = select(RatingModel).where(RatingModel.user_id == user_uuid)
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
                await db.rollback()
                logger.error("list_ratings failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return SEED_RATINGS.get(user_id, [])

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
                await db.rollback()
                logger.error("set_rating failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        resp = RatingResponse(
            id=str(uuid.uuid4()),
            title_id=body.title_id,
            rating_value=body.rating_value,
            updated_at=rated_iso,
        )
        if user_id not in SEED_RATINGS:
            SEED_RATINGS[user_id] = []
        SEED_RATINGS[user_id].append(resp)
        return resp

    async def list_notes(
        self, db: Optional[AsyncSession], user_id: str
    ) -> List[NoteResponse]:
        """Lists private personal notes created by user."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                stmt = select(NoteModel).where(NoteModel.user_id == user_uuid)
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
                await db.rollback()
                logger.error("list_notes failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return []

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
                await db.rollback()
                logger.error("create_note failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return NoteResponse(
            id=str(uuid.uuid4()),
            title_id=body.title_id,
            note_text=body.note_text,
            updated_at=created_iso,
        )

    async def list_reviews(
        self, db: Optional[AsyncSession], user_id: str
    ) -> List[ReviewResponse]:
        """Lists reviews created by user."""
        if db is not None:
            try:
                user_uuid = _resolve_user_uuid(user_id)
                stmt = select(ReviewModel).where(ReviewModel.user_id == user_uuid)
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
                await db.rollback()
                logger.error("list_reviews failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return []

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
                await db.rollback()
                logger.error("create_review failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        return ReviewResponse(
            id=str(uuid.uuid4()),
            title_id=body.title_id,
            review_title=body.review_title,
            review_text=body.review_text,
            is_public=body.is_public,
            created_at=created_iso,
        )

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
                await db.rollback()
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

                    for ev in watch_events:
                        t = title_map.get(ev.title_id)
                        if t:
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
                await db.rollback()
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


personal_repository = PersonalRepository()

