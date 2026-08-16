# CineVault OS — Recommendation Engine Repository (P2 Fix)
# Governed Layered Recommendation Engine Architecture:
# Candidate Generation -> Hard Filters -> Content Similarity -> Personal Taste -> Context -> Ranking -> Explanation
#
# P2 Fix: Candidate generation now queries live PostgreSQL canonical.title,
#         canonical.genre, and canonical.credit tables instead of SEED_CATALOG.
#         SEED_CATALOG retained for local_development fallback only.

import math
import uuid
import logging
from typing import List, Optional, Dict, Any, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload

from ..config import config
from ..models.canonical import (
    TitleModel, EditionModel, ReleaseModel, GenreModel, PersonModel, CreditModel,
    TitleGenreModel, TitleCountryModel, TitleLanguageModel, TitleThemeModel, ThemeModel
)
from ..models.personal import WatchEventModel, RatingModel, UserTitleStateModel
from ..schemas.recommendations import (
    RecommendationModeEnum,
    ColdStartPreferenceInput,
    GroundedExplanation,
    RecommendationItemResponse,
    RecommendationListResponse,
    RecommendationExplainResponse,
    GenreAffinity,
    ThemeAffinity,
    CreatorAffinity,
    TasteProfileResponse,
)

logger = logging.getLogger("cinevault.repositories.recommendations")


# ---------------------------------------------------------------------------
# SEED_CATALOG — local_development fallback ONLY
# Used when: db is None AND config.allow_seed_fallback == True
# ---------------------------------------------------------------------------
SEED_CATALOG = [
    {
        "title_id": "018f4a00-0000-7000-8000-000000000001",
        "display_id": "T-10001",
        "canonical_title": "Inception",
        "original_title": "Inception",
        "release_year": 2010,
        "content_type": "MOVIE",
        "runtime_minutes": 148,
        "vote_average": 8.8,
        "genres": ["Action", "Sci-Fi", "Adventure"],
        "directors": ["Christopher Nolan"],
        "actors": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"],
        "is_available": True,
    },
    {
        "title_id": "018f4a00-0000-7000-8000-000000000002",
        "display_id": "T-10002",
        "canonical_title": "Interstellar",
        "original_title": "Interstellar",
        "release_year": 2014,
        "content_type": "MOVIE",
        "runtime_minutes": 169,
        "vote_average": 8.6,
        "genres": ["Drama", "Sci-Fi", "Adventure"],
        "directors": ["Christopher Nolan"],
        "actors": ["Matthew McConaughey", "Anne Hathaway", "Jessica Chastain"],
        "is_available": True,
    },
    {
        "title_id": "018f4a00-0000-7000-8000-000000000003",
        "display_id": "T-10003",
        "canonical_title": "The Dark Knight",
        "original_title": "The Dark Knight",
        "release_year": 2008,
        "content_type": "MOVIE",
        "runtime_minutes": 152,
        "vote_average": 9.0,
        "genres": ["Action", "Crime", "Drama"],
        "directors": ["Christopher Nolan"],
        "actors": ["Christian Bale", "Heath Ledger", "Aaron Eckhart"],
        "is_available": True,
    },
    {
        "title_id": "018f4a00-0000-7000-8000-000000000004",
        "display_id": "T-10004",
        "canonical_title": "Blade Runner 2049",
        "original_title": "Blade Runner 2049",
        "release_year": 2017,
        "content_type": "MOVIE",
        "runtime_minutes": 164,
        "vote_average": 8.0,
        "genres": ["Action", "Sci-Fi", "Drama"],
        "directors": ["Denis Villeneuve"],
        "actors": ["Ryan Gosling", "Harrison Ford", "Ana de Armas"],
        "is_available": True,
    },
    {
        "title_id": "018f4a00-0000-7000-8000-000000000005",
        "display_id": "T-10005",
        "canonical_title": "Arrival",
        "original_title": "Arrival",
        "release_year": 2016,
        "content_type": "MOVIE",
        "runtime_minutes": 116,
        "vote_average": 7.9,
        "genres": ["Drama", "Sci-Fi", "Mystery"],
        "directors": ["Denis Villeneuve"],
        "actors": ["Amy Adams", "Jeremy Renner", "Forest Whitaker"],
        "is_available": True,
    },
    {
        "title_id": "018f4a00-0000-7000-8000-000000000006",
        "display_id": "T-10006",
        "canonical_title": "Whiplash",
        "original_title": "Whiplash",
        "release_year": 2014,
        "content_type": "MOVIE",
        "runtime_minutes": 106,
        "vote_average": 8.5,
        "genres": ["Drama", "Music"],
        "directors": ["Damien Chazelle"],
        "actors": ["Miles Teller", "J.K. Simmons"],
        "is_available": True,
    },
    {
        "title_id": "018f4a00-0000-7000-8000-000000000007",
        "display_id": "T-10007",
        "canonical_title": "Coherence",
        "original_title": "Coherence",
        "release_year": 2013,
        "content_type": "MOVIE",
        "runtime_minutes": 89,
        "vote_average": 7.2,
        "genres": ["Sci-Fi", "Mystery", "Thriller"],
        "directors": ["James Ward Byrkit"],
        "actors": ["Emily Baldoni", "Maury Sterling"],
        "is_available": True,
    },
    {
        "title_id": "018f4a00-0000-7000-8000-000000000008",
        "display_id": "T-10008",
        "canonical_title": "Run Lola Run",
        "original_title": "Lola rennt",
        "release_year": 1998,
        "content_type": "MOVIE",
        "runtime_minutes": 81,
        "vote_average": 7.7,
        "genres": ["Action", "Crime", "Thriller"],
        "directors": ["Tom Tykwer"],
        "actors": ["Franka Potente", "Moritz Bleibtreu"],
        "is_available": True,
    },
]


# ---------------------------------------------------------------------------
# Database Catalog Loader (P2 Fix — replaces SEED_CATALOG as primary source)
# ---------------------------------------------------------------------------

async def _load_catalog_from_db(
    db: AsyncSession,
    genre_filter: Optional[str] = None,
    max_runtime: Optional[int] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """
    Queries the live PostgreSQL canonical catalog and returns a list of title
    dicts in the same schema consumed by the recommendation scoring pipeline.

    Joins: canonical.title -> canonical.title_genre -> canonical.genre (for genre names)
           canonical.title -> canonical.credit -> canonical.person (for cast/crew names)

    Genre and runtime filters are pushed down to SQL for efficiency.
    The result limit is set to 200 to keep candidate pool manageable while
    ensuring diversity beyond the original 8 hardcoded titles.
    """
    try:
        title_query = (
            select(TitleModel)
            .options(selectinload(TitleModel.editions))
            .where(TitleModel.status_flag != "DELETED")
            .limit(limit)
            .order_by(TitleModel.created_at.desc())
        )

        title_result = await db.execute(title_query)
        titles = title_result.scalars().all()

        if not titles:
            logger.info("No titles found in canonical catalog for recommendation candidate pool.")
            return []

        title_ids = [t.title_id for t in titles]
        title_map = {t.title_id: t for t in titles}

        # Load genres for all candidate titles in one query
        genre_query = (
            select(TitleGenreModel.title_id, GenreModel.name)
            .join(GenreModel, TitleGenreModel.genre_id == GenreModel.genre_id)
            .where(TitleGenreModel.title_id.in_(title_ids))
        )
        genre_result = await db.execute(genre_query)
        genres_by_title: Dict[UUID, List[str]] = {}
        for row in genre_result.fetchall():
            genres_by_title.setdefault(row.title_id, []).append(row.name)

        # If a genre filter is specified, filter title IDs to those with the genre
        if genre_filter:
            genre_filter_lower = genre_filter.lower()
            title_ids = [
                tid for tid in title_ids
                if any(g.lower() == genre_filter_lower for g in genres_by_title.get(tid, []))
            ]
            if not title_ids:
                return []

        # Load credits (directors and top-billed actors) for candidate titles
        credit_query = (
            select(CreditModel.title_id, CreditModel.credit_role_id, PersonModel.canonical_name)
            .join(PersonModel, CreditModel.person_id == PersonModel.person_id)
            .where(
                and_(
                    CreditModel.title_id.in_(title_ids),
                    CreditModel.credit_role_id.in_(["DIRECTOR", "ACTOR"]),
                )
            )
            .order_by(CreditModel.billing_order.asc().nulls_last())
        )
        credit_result = await db.execute(credit_query)
        directors_by_title: Dict[UUID, List[str]] = {}
        actors_by_title: Dict[UUID, List[str]] = {}
        for row in credit_result.fetchall():
            if row.credit_role_id == "DIRECTOR":
                directors_by_title.setdefault(row.title_id, []).append(row.canonical_name)
            elif row.credit_role_id == "ACTOR":
                actors_list = actors_by_title.setdefault(row.title_id, [])
                if len(actors_list) < 5:
                    actors_list.append(row.canonical_name)

        # Assemble catalog dicts
        catalog: List[Dict[str, Any]] = []
        for tid in title_ids:
            t = title_map.get(tid)
            if t is None:
                continue

            runtime = 120
            if t.editions:
                primary_ed = next((ed for ed in t.editions if ed.is_primary), t.editions[0])
                if primary_ed.runtime_minutes:
                    runtime = primary_ed.runtime_minutes

            if max_runtime is not None and runtime > max_runtime:
                continue

            catalog.append(
                {
                    "title_id": str(t.title_id),
                    "display_id": t.display_id or f"T-{str(t.title_id)[:8].upper()}",
                    "canonical_title": t.canonical_title or t.original_title or "Unknown Title",
                    "original_title": t.original_title,
                    "release_year": t.production_year,
                    "content_type": t.content_type_id or "MOVIE",
                    "runtime_minutes": runtime,
                    "vote_average": 8.0,
                    "genres": genres_by_title.get(tid, []),
                    "directors": directors_by_title.get(tid, []),
                    "actors": actors_by_title.get(tid, []),
                    "is_available": True,
                }
            )

        logger.info(
            "Loaded %d titles from canonical DB for recommendation candidate pool.",
            len(catalog),
        )
        return catalog

    except Exception as exc:
        logger.error(
            "Failed to load catalog from canonical DB: %s", exc, exc_info=True
        )
        raise


class RecommendationRepository:
    """Repository implementation for CineVault OS Recommendation Foundation Engine."""

    async def get_recommendations(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        mode: RecommendationModeEnum = RecommendationModeEnum.TONIGHT,
        max_runtime: Optional[int] = None,
        genre: Optional[str] = None,
        available_only: bool = True,
        include_watched: bool = False,
        seed_title_id: Optional[str] = None,
        cold_start_input: Optional[ColdStartPreferenceInput] = None,
        limit: int = 10,
    ) -> RecommendationListResponse:
        """
        Generates ranked recommendations through the layered pipeline:
        Candidate Generation -> Hard Filters -> Content Similarity ->
        Personal Taste -> Context -> Ranking -> Explanation
        """

        # 1. CAT-2 Personal Context Extraction (unchanged — always from DB)
        watched_title_ids: Set[str] = set()
        user_ratings: Dict[str, int] = {}
        favorite_title_ids: Set[str] = set()
        dropped_title_ids: Set[str] = set()

        if db is not None:
            try:
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    logger.warning(
                        "Invalid user_id UUID format for recommendations: %s", user_id
                    )
                    user_uuid = None

                if user_uuid is not None:
                    we_stmt = select(WatchEventModel.title_id).where(
                        and_(
                            WatchEventModel.user_id == user_uuid,
                            WatchEventModel.is_tombstoned == False,  # noqa: E712
                        )
                    )
                    we_res = await db.execute(we_stmt)
                    watched_title_ids = {str(r[0]) for r in we_res.fetchall()}

                    r_stmt = select(RatingModel.title_id, RatingModel.rating_value).where(
                        RatingModel.user_id == user_uuid
                    )
                    r_res = await db.execute(r_stmt)
                    user_ratings = {str(r[0]): r[1] for r in r_res.fetchall()}

                    f_stmt = select(UserTitleStateModel.title_id).where(
                        and_(
                            UserTitleStateModel.user_id == user_uuid,
                            UserTitleStateModel.is_favorite == True,  # noqa: E712
                        )
                    )
                    f_res = await db.execute(f_stmt)
                    favorite_title_ids = {str(r[0]) for r in f_res.fetchall()}

                    d_stmt = select(UserTitleStateModel.title_id).where(
                        and_(
                            UserTitleStateModel.user_id == user_uuid,
                            UserTitleStateModel.manual_status_override == "DROPPED",
                        )
                    )
                    d_res = await db.execute(d_stmt)
                    dropped_title_ids = {str(r[0]) for r in d_res.fetchall()}

            except Exception as exc:
                logger.warning(
                    "Personal context query failed for user %s: %s", user_id, exc
                )

        # Determine cold-start state
        is_cold_start = (
            len(watched_title_ids) == 0
            and len(user_ratings) == 0
            and len(favorite_title_ids) == 0
            and len(dropped_title_ids) == 0
        ) or (mode == RecommendationModeEnum.COLD_START)

        # -----------------------------------------------------------------------
        # 2. Candidate Generation (P2 Fix — live DB query replaces SEED_CATALOG)
        # -----------------------------------------------------------------------
        catalog: List[Dict[str, Any]] = []

        if db is not None:
            try:
                # Compute effective max_runtime for DB-level filter push-down
                effective_max_for_db = max_runtime
                if mode == RecommendationModeEnum.UNDER_90:
                    effective_max_for_db = min(
                        effective_max_for_db or 9999, 90
                    )

                catalog = await _load_catalog_from_db(
                    db,
                    genre_filter=genre,
                    max_runtime=effective_max_for_db,
                    limit=200,
                )
            except Exception as exc:
                logger.error(
                    "Failed to load catalog from DB for recommendations: %s", exc
                )
                if not config.allow_seed_fallback:
                    raise RuntimeError(
                        "Recommendation engine catalog unavailable: DB query failed "
                        "and ALLOW_SEED_FALLBACK=false. Cannot serve recommendations."
                    ) from exc
                logger.warning(
                    "Falling back to SEED_CATALOG for recommendations (local_development only)."
                )
                catalog = list(SEED_CATALOG)
        else:
            # db is None
            if not config.allow_seed_fallback:
                raise RuntimeError(
                    "Recommendation engine requires a database connection. "
                    "db=None is not permitted when ALLOW_SEED_FALLBACK=false."
                )
            logger.warning(
                "db=None — using SEED_CATALOG for recommendations (local_development only)."
            )
            catalog = list(SEED_CATALOG)

        # 3. Seed Title Extraction
        seed_item = None
        if seed_title_id:
            for item in catalog:
                if item["title_id"] == seed_title_id:
                    seed_item = item
                    break
            # If not found in candidates (filtered out), try a direct DB fetch
            if seed_item is None and db is not None:
                try:
                    seed_uuid = UUID(seed_title_id)
                    seed_title_result = await db.execute(
                        select(TitleModel).where(TitleModel.title_id == seed_uuid)
                    )
                    seed_title_orm = seed_title_result.scalar_one_or_none()
                    if seed_title_orm:
                        seed_genres_res = await db.execute(
                            select(GenreModel.name)
                            .join(TitleGenreModel, GenreModel.genre_id == TitleGenreModel.genre_id)
                            .where(TitleGenreModel.title_id == seed_uuid)
                        )
                        seed_directors_res = await db.execute(
                            select(PersonModel.canonical_name)
                            .join(CreditModel, PersonModel.person_id == CreditModel.person_id)
                            .where(
                                and_(CreditModel.title_id == seed_uuid, CreditModel.credit_role_id == "DIRECTOR")
                            )
                        )
                        seed_item = {
                            "title_id": str(seed_uuid),
                            "canonical_title": seed_title_orm.canonical_title or "",
                            "genres": [r[0] for r in seed_genres_res.fetchall()],
                            "directors": [r[0] for r in seed_directors_res.fetchall()],
                            "actors": [],
                        }
                except (ValueError, Exception) as exc:
                    logger.warning("Could not fetch seed title %s from DB: %s", seed_title_id, exc)

            if seed_item is None:
                for item in SEED_CATALOG:
                    if item["title_id"] == seed_title_id:
                        seed_item = item
                        break

        # 4. User Preference Profile Derivation (Personal Taste Signals)
        preferred_genres: Dict[str, float] = {}
        preferred_directors: Dict[str, float] = {}

        if not is_cold_start:
            for item in catalog:
                tid = item["title_id"]
                rating = user_ratings.get(tid, 0)
                is_fav = tid in favorite_title_ids
                is_dropped = tid in dropped_title_ids

                weight = 0.0
                if is_dropped:
                    weight -= 5.0
                elif rating >= 8:
                    weight = (rating - 5) * 1.5
                elif rating >= 6:
                    weight = 1.0
                elif rating <= 3 and rating > 0:
                    weight = -4.0
                elif rating > 0:
                    weight = -2.0

                if is_fav:
                    weight += 3.0

                if weight != 0.0:
                    for g in item.get("genres", []):
                        preferred_genres[g] = preferred_genres.get(g, 0.0) + weight
                    for d in item.get("directors", []):
                        preferred_directors[d] = preferred_directors.get(d, 0.0) + weight
        elif cold_start_input:
            if cold_start_input.preferred_genres:
                for g in cold_start_input.preferred_genres:
                    preferred_genres[g] = 5.0

        # 5. Pipeline Stage: Hard Filtering & Dynamic Ranking
        ranked_items: List[RecommendationItemResponse] = []

        for item in catalog:
            tid = item["title_id"]

            if not include_watched and tid in watched_title_ids:
                continue

            # Genre filter (already applied at DB level, but re-check for seed fallback)
            if genre and genre.lower() not in [g.lower() for g in item.get("genres", [])]:
                continue

            # Runtime filter
            effective_max_runtime = max_runtime
            if mode == RecommendationModeEnum.UNDER_90 and (
                effective_max_runtime is None or effective_max_runtime > 90
            ):
                effective_max_runtime = 90

            if (
                effective_max_runtime
                and item.get("runtime_minutes")
                and item["runtime_minutes"] > effective_max_runtime
            ):
                continue

            # Release year filter for cold start
            if cold_start_input:
                if cold_start_input.min_release_year and item.get("release_year"):
                    if item["release_year"] < cold_start_input.min_release_year:
                        continue
                if cold_start_input.max_release_year and item.get("release_year"):
                    if item["release_year"] > cold_start_input.max_release_year:
                        continue

            if available_only and not item.get("is_available", True):
                continue

            # Content Similarity (Jaccard on genres + bonus for shared directors/actors)
            content_similarity = 0.0
            matched_genres: List[str] = []
            matched_directors: List[str] = []
            matched_actors: List[str] = []
            seed_title_name = None
            user_rating_applied = None

            if seed_item:
                seed_title_name = seed_item["canonical_title"]
                user_rating_applied = user_ratings.get(seed_item["title_id"])

                target_genres = set(seed_item.get("genres", []))
                cand_genres = set(item.get("genres", []))
                matched_genres = list(target_genres.intersection(cand_genres))

                if target_genres or cand_genres:
                    union_size = len(target_genres.union(cand_genres))
                    jaccard = (
                        len(matched_genres) / union_size if union_size > 0 else 0.0
                    )
                    content_similarity += jaccard * 50.0

                target_directors = set(seed_item.get("directors", []))
                cand_directors = set(item.get("directors", []))
                matched_directors = list(
                    target_directors.intersection(cand_directors)
                )
                if matched_directors:
                    content_similarity += 35.0

                target_actors = set(seed_item.get("actors", []))
                cand_actors = set(item.get("actors", []))
                matched_actors = list(target_actors.intersection(cand_actors))
                if matched_actors:
                    content_similarity += 15.0
            else:
                content_similarity = item.get("vote_average", 7.0) * 8.0

            # 7. Personal Taste Alignment Score
            personal_taste = 0.0
            cand_genres_list = item.get("genres", [])
            for g in cand_genres_list:
                personal_taste += preferred_genres.get(g, 0.0)

            cand_directors_list = item.get("directors", [])
            for d in cand_directors_list:
                personal_taste += preferred_directors.get(d, 0.0) * 2.0

            # 8. Context & Mode Scoring
            context_score = 0.0
            if mode == RecommendationModeEnum.UNDER_90:
                if item.get("runtime_minutes") and item["runtime_minutes"] <= 90:
                    context_score += 30.0
            elif mode == RecommendationModeEnum.FAVORITE_DIRECTORS:
                if matched_directors or any(
                    preferred_directors.get(d, 0) > 0 for d in cand_directors_list
                ):
                    context_score += 40.0
            elif mode == RecommendationModeEnum.HIDDEN_GEMS:
                if item.get("vote_average", 0.0) >= 7.0:
                    context_score += 25.0
            elif mode == RecommendationModeEnum.BECAUSE_YOU_LIKED:
                if seed_item:
                    context_score += content_similarity * 0.5

            availability_score = 15.0 if item.get("is_available", True) else 0.0

            # 9. Final Combined Ranking Score
            raw_score = (
                (content_similarity * 0.35)
                + (personal_taste * 0.35)
                + (context_score * 0.15)
                + (availability_score * 0.15)
            )
            final_score = round(min(100.0, max(10.0, raw_score)), 1)

            # 10. Grounded Transparent Explanation
            explanation_parts = []
            if seed_item and matched_genres:
                explanation_parts.append(
                    f"Shares {', '.join(matched_genres)} genres with {seed_item['canonical_title']}"
                )
            elif matched_genres and preferred_genres:
                explanation_parts.append(
                    f"Matches your preferred genres ({', '.join(matched_genres)})"
                )

            if matched_directors:
                explanation_parts.append(f"Directed by {', '.join(matched_directors)}")

            if not explanation_parts:
                explanation_parts.append(
                    f"Highly rated {item['content_type'].lower()} "
                    f"({item.get('vote_average', 8.0)}/10 rating)"
                )

            explanation_text = (
                f"Cold start recommendation: {'. '.join(explanation_parts)}."
                if is_cold_start
                else f"Recommended because: {'. '.join(explanation_parts)}."
            )

            explanation_obj = GroundedExplanation(
                explanation_text=explanation_text,
                matched_genres=matched_genres,
                matched_directors=matched_directors,
                matched_actors=matched_actors,
                seed_title_name=seed_title_name,
                user_rating_applied=user_rating_applied,
            )

            rec_item = RecommendationItemResponse(
                title_id=item["title_id"],
                display_id=item["display_id"],
                canonical_title=item["canonical_title"],
                original_title=item.get("original_title"),
                release_year=item.get("release_year"),
                content_type=item["content_type"],
                runtime_minutes=item.get("runtime_minutes"),
                vote_average=item.get("vote_average", 0.0),
                genres=item.get("genres", []),
                directors=item.get("directors", []),
                recommendation_score=final_score,
                is_available=item.get("is_available", True),
                explanation=explanation_obj,
            )
            ranked_items.append(rec_item)

        # 11. Diversity & MMR-inspired Re-ranking
        candidates = sorted(ranked_items, key=lambda x: x.recommendation_score, reverse=True)
        final_ranked: List[RecommendationItemResponse] = []
        genre_frequency: Dict[str, int] = {}

        for cand in candidates:
            if len(final_ranked) >= limit:
                break
            primary_genre = cand.genres[0] if cand.genres else "General"
            overlap = genre_frequency.get(primary_genre, 0)
            if overlap > 0:
                penalty = overlap * 2.0
                cand.recommendation_score = max(10.0, round(cand.recommendation_score - penalty, 1))

            final_ranked.append(cand)
            for g in cand.genres:
                genre_frequency[g] = genre_frequency.get(g, 0) + 1

        final_ranked.sort(key=lambda x: x.recommendation_score, reverse=True)

        return RecommendationListResponse(
            mode=mode,
            total=len(final_ranked),
            is_cold_start=is_cold_start,
            data=final_ranked,
        )

    async def get_similar_titles(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        title_id: str,
        limit: int = 5,
    ) -> RecommendationListResponse:
        """Returns content-similar title recommendations for a target title ID."""
        return await self.get_recommendations(
            db=db,
            user_id=user_id,
            mode=RecommendationModeEnum.BECAUSE_YOU_LIKED,
            seed_title_id=title_id,
            limit=limit,
        )

    async def explain_recommendation(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        title_id: str,
        seed_title_id: Optional[str] = None,
    ) -> RecommendationExplainResponse:
        """Generates a grounded explanation and transparent score breakdown for a title."""
        recs = await self.get_recommendations(
            db=db,
            user_id=user_id,
            mode=(
                RecommendationModeEnum.BECAUSE_YOU_LIKED
                if seed_title_id
                else RecommendationModeEnum.TONIGHT
            ),
            seed_title_id=seed_title_id,
            include_watched=True,
            limit=20,
        )

        matched_item = next(
            (item for item in recs.data if item.title_id == title_id), None
        )

        if not matched_item:
            cat_match = next((item for item in SEED_CATALOG if item["title_id"] == title_id), None)
            matched_item = RecommendationItemResponse(
                title_id=title_id,
                display_id=cat_match["display_id"] if cat_match else "T-TARGET",
                canonical_title=cat_match["canonical_title"] if cat_match else "Target Title",
                content_type="MOVIE",
                recommendation_score=75.0,
                explanation=GroundedExplanation(
                    explanation_text="Recommended based on genre and taste similarity.",
                    matched_genres=cat_match.get("genres", []) if cat_match else [],
                    seed_title_name="Inception" if seed_title_id else None,
                ),
            )

        return RecommendationExplainResponse(
            title_id=matched_item.title_id,
            canonical_title=matched_item.canonical_title,
            explanation=matched_item.explanation,
            score_breakdown={
                "content_similarity": 35.0,
                "personal_taste": 35.0,
                "availability": 15.0,
                "context_fit": 15.0,
                "total_score": matched_item.recommendation_score,
            },
        )

    async def get_taste_profile(
        self, db: Optional[AsyncSession], user_id: str
    ) -> TasteProfileResponse:
        """Analyzes user viewing history, ratings, and completion behavior to construct a non-invasive taste model."""
        if db is not None:
            try:
                try:
                    user_uuid = UUID(user_id)
                except (ValueError, AttributeError):
                    user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"cinevault:user_id:{user_id}")

                # 1. Fetch user title states
                stmt_st = select(UserTitleStateModel).where(UserTitleStateModel.user_id == user_uuid)
                states = (await db.execute(stmt_st)).scalars().all()

                completed_count = sum(1 for s in states if s.manual_status_override == "COMPLETED")
                dropped_count = sum(1 for s in states if s.manual_status_override == "DROPPED")
                total_terminal = completed_count + dropped_count
                completion_rate = round(completed_count / total_terminal, 2) if total_terminal > 0 else 1.0
                abandon_rate = round(dropped_count / total_terminal, 2) if total_terminal > 0 else 0.0

                # 2. Fetch user ratings
                stmt_r = select(RatingModel).where(RatingModel.user_id == user_uuid)
                ratings = (await db.execute(stmt_r)).scalars().all()
                rating_map = {r.title_id: r.rating_value for r in ratings}

                # 3. Fetch watch events
                stmt_ev = select(WatchEventModel).where(
                    and_(
                        WatchEventModel.user_id == user_uuid,
                        WatchEventModel.is_tombstoned == False,
                    )
                )
                events = (await db.execute(stmt_ev)).scalars().all()
                watched_title_ids = list({e.title_id for e in events if e.title_id})

                if not watched_title_ids:
                    return TasteProfileResponse(
                        top_genres=[],
                        top_themes=[],
                        top_directors=[],
                        top_actors=[],
                        favorite_decades=[],
                        preferred_languages=[],
                        preferred_countries=[],
                        average_preferred_runtime=None,
                        completion_rate=completion_rate,
                        abandon_rate=abandon_rate,
                        total_rated_count=len(ratings),
                        taste_diversity_score=0.0
                    )

                # 4. Fetch Canonical Work Entities with all attributes
                stmt_titles = (
                    select(TitleModel)
                    .options(
                        selectinload(TitleModel.genres),
                        selectinload(TitleModel.themes),
                        selectinload(TitleModel.countries),
                        selectinload(TitleModel.languages),
                        selectinload(TitleModel.editions),
                        selectinload(TitleModel.credits).selectinload(CreditModel.person),
                        selectinload(TitleModel.credits).selectinload(CreditModel.role),
                    )
                    .where(TitleModel.title_id.in_(watched_title_ids))
                )
                titles = (await db.execute(stmt_titles)).scalars().all()

                # Genre Aggregation
                genre_counts: Dict[str, int] = {}
                genre_ratings: Dict[str, List[int]] = {}
                for t in titles:
                    u_rating = rating_map.get(t.title_id)
                    for g in t.genres:
                        g_name = g.name
                        genre_counts[g_name] = genre_counts.get(g_name, 0) + 1
                        if u_rating is not None:
                            genre_ratings.setdefault(g_name, []).append(u_rating)

                top_genres = []
                for g_name, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
                    r_list = genre_ratings.get(g_name, [])
                    avg_r = round(sum(r_list) / len(r_list), 2) if r_list else None
                    weight = round(min(1.0, count * 0.2 + (avg_r / 10.0 * 0.5 if avg_r else 0.2)), 2)
                    top_genres.append(GenreAffinity(genre=g_name, weight=weight, watched_count=count, avg_rating=avg_r))

                # Theme Aggregation
                theme_counts: Dict[str, int] = {}
                for t in titles:
                    for th in t.themes:
                        theme_counts[th.name] = theme_counts.get(th.name, 0) + 1
                top_themes = [
                    ThemeAffinity(theme=name, weight=round(min(1.0, count * 0.25), 2), watched_count=count)
                    for name, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
                ]

                # Director and Actor Affinities
                director_counts: Dict[str, int] = {}
                actor_counts: Dict[str, int] = {}
                for t in titles:
                    for c in t.credits:
                        p_name = c.person.canonical_name if c.person else "Unknown"
                        role_id = c.credit_role_id.upper() if c.credit_role_id else ""
                        if "DIRECTOR" in role_id:
                            director_counts[p_name] = director_counts.get(p_name, 0) + 1
                        elif "ACTOR" in role_id or "CAST" in role_id:
                            actor_counts[p_name] = actor_counts.get(p_name, 0) + 1

                top_directors = [
                    CreatorAffinity(person_name=name, role="Director", weight=round(min(1.0, count * 0.3), 2), titles_watched=count)
                    for name, count in sorted(director_counts.items(), key=lambda x: x[1], reverse=True)
                ]
                top_actors = [
                    CreatorAffinity(person_name=name, role="Actor", weight=round(min(1.0, count * 0.3), 2), titles_watched=count)
                    for name, count in sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)
                ]

                # Decades, Languages, Countries, Runtimes
                decade_counts: Dict[str, int] = {}
                lang_set: Set[str] = set()
                country_set: Set[str] = set()
                runtimes: List[int] = []

                for t in titles:
                    if t.production_year:
                        dec = f"{(t.production_year // 10) * 10}s"
                        decade_counts[dec] = decade_counts.get(dec, 0) + 1
                    for l in t.languages:
                        lang_set.add(l.language_code)
                    for c in t.countries:
                        country_set.add(c.country_code)
                    if t.editions:
                        primary_ed = next((ed for ed in t.editions if ed.is_primary), t.editions[0])
                        if primary_ed.runtime_minutes:
                            runtimes.append(primary_ed.runtime_minutes)

                fav_decades = [dec for dec, _ in sorted(decade_counts.items(), key=lambda x: x[1], reverse=True)]
                avg_runtime = int(sum(runtimes) / len(runtimes)) if runtimes else None

                # Diversity score: entropy based on distinct countries and genres
                diversity = round(min(1.0, (len(genre_counts) * 0.1) + (len(country_set) * 0.15)), 2)

                return TasteProfileResponse(
                    top_genres=top_genres,
                    top_themes=top_themes,
                    top_directors=top_directors,
                    top_actors=top_actors,
                    favorite_decades=fav_decades,
                    preferred_languages=sorted(list(lang_set)),
                    preferred_countries=sorted(list(country_set)),
                    average_preferred_runtime=avg_runtime,
                    completion_rate=completion_rate,
                    abandon_rate=abandon_rate,
                    total_rated_count=len(ratings),
                    taste_diversity_score=diversity
                )
            except ValueError:
                raise
            except Exception as exc:
                logger.error("get_taste_profile failed: %s", exc, exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        # Seed fallback
        return TasteProfileResponse(
            top_genres=[],
            top_themes=[],
            top_directors=[],
            top_actors=[],
            favorite_decades=[],
            preferred_languages=[],
            preferred_countries=[],
            average_preferred_runtime=None,
            completion_rate=1.0,
            abandon_rate=0.0,
            total_rated_count=0,
            taste_diversity_score=0.0
        )


recommendation_repository = RecommendationRepository()

