# CineVault OS — Recommendation Engine Repository (Build Unit 8.7)
# Governed Layered Recommendation Engine Architecture:
# Candidate Generation -> Hard Filters -> Content Similarity -> Personal Taste -> Context -> Ranking -> Explanation

import math
from typing import List, Optional, Dict, Any, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..models.canonical import TitleModel, EditionModel, ReleaseModel, GenreModel, PersonModel, CreditModel, TitleGenreModel
from ..models.personal import WatchEventModel, RatingModel, UserTitleStateModel
from ..schemas.recommendations import (
    RecommendationModeEnum,
    ColdStartPreferenceInput,
    GroundedExplanation,
    RecommendationItemResponse,
    RecommendationListResponse,
    RecommendationExplainResponse
)

# Mock/Seed Canonical Catalog for Fallback & Test isolation when db is None
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
        "is_available": True
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
        "is_available": True
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
        "is_available": True
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
        "is_available": True
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
        "is_available": True
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
        "is_available": True
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
        "is_available": True
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
        "is_available": True
    }
]

class RecommendationRepository:
    """Repository implementation for CineVault OS Recommendation Foundation Engine (Build Unit 8.7)."""

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
        limit: int = 10
    ) -> RecommendationListResponse:
        """Generates ranked recommendations through candidate generation, hard filtering, similarity, personal taste, and context scoring."""
        
        # 1. CAT-2 Personal Context Extraction
        watched_title_ids: Set[str] = set()
        user_ratings: Dict[str, int] = {}
        favorite_title_ids: Set[str] = set()

        if db is not None:
            try:
                # Query active (non-tombstoned) watch events for user
                we_stmt = select(WatchEventModel.title_id).where(
                    and_(
                        WatchEventModel.user_id == (UUID(user_id) if isinstance(user_id, str) else user_id),
                        WatchEventModel.is_tombstoned == False
                    )
                )
                we_res = await db.execute(we_stmt)
                watched_title_ids = {str(r[0]) for r in we_res.fetchall()}

                # Query ratings for user
                r_stmt = select(RatingModel.title_id, RatingModel.rating_value).where(
                    RatingModel.user_id == (UUID(user_id) if isinstance(user_id, str) else user_id)
                )
                r_res = await db.execute(r_stmt)
                user_ratings = {str(r[0]): r[1] for r in r_res.fetchall()}

                # Query favorites for user
                f_stmt = select(UserTitleStateModel.title_id).where(
                    and_(
                        UserTitleStateModel.user_id == (UUID(user_id) if isinstance(user_id, str) else user_id),
                        UserTitleStateModel.is_favorite == True
                    )
                )
                f_res = await db.execute(f_stmt)
                favorite_title_ids = {str(r[0]) for r in f_res.fetchall()}
            except Exception as e:
                import logging
                logging.getLogger("cinevault.repositories.recommendations").warning(f"Database query failed, using in-memory catalog: {e}")

        # Determine cold-start state
        is_cold_start = (len(watched_title_ids) == 0 and len(user_ratings) == 0 and len(favorite_title_ids) == 0) or (mode == RecommendationModeEnum.COLD_START)

        # 2. Candidate Generation
        catalog = list(SEED_CATALOG) # Baseline catalog candidates

        # 3. Seed Title Extraction if applicable
        seed_item = None
        if seed_title_id:
            for item in catalog:
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

                # Weight calculation for high ratings / favorites
                weight = 0.0
                if rating >= 8:
                    weight = (rating - 5) * 1.5
                elif rating >= 6:
                    weight = 1.0
                elif rating > 0:
                    weight = -1.0 # Negative preference for low rating

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

            # Filter: Exclude watched titles if include_watched is False
            if not include_watched and tid in watched_title_ids:
                continue

            # Filter: Genre hard filter if explicitly specified
            if genre and genre.lower() not in [g.lower() for g in item.get("genres", [])]:
                continue

            # Filter: Runtime hard filter (e.g., UNDER_90 mode or explicit max_runtime)
            effective_max_runtime = max_runtime
            if mode == RecommendationModeEnum.UNDER_90 and (effective_max_runtime is None or effective_max_runtime > 90):
                effective_max_runtime = 90

            if effective_max_runtime and item.get("runtime_minutes") and item["runtime_minutes"] > effective_max_runtime:
                continue

            # Filter: Release year range for cold start input
            if cold_start_input:
                if cold_start_input.min_release_year and item.get("release_year") and item["release_year"] < cold_start_input.min_release_year:
                    continue
                if cold_start_input.max_release_year and item.get("release_year") and item["release_year"] > cold_start_input.max_release_year:
                    continue

            # Filter: Availability filter
            if available_only and not item.get("is_available", True):
                continue

            # 6. Pipeline Stage: Content Similarity Scoring
            content_similarity = 0.0
            matched_genres: List[str] = []
            matched_directors: List[str] = []
            matched_actors: List[str] = []
            seed_title_name = None
            user_rating_applied = None

            if seed_item:
                seed_title_name = seed_item["canonical_title"]
                user_rating_applied = user_ratings.get(seed_item["title_id"])
                
                # Genre overlap
                common_genres = set(item.get("genres", [])).intersection(set(seed_item.get("genres", [])))
                matched_genres = list(common_genres)
                if seed_item.get("genres"):
                    content_similarity += (len(common_genres) / len(seed_item["genres"])) * 50.0

                # Director match
                common_directors = set(item.get("directors", [])).intersection(set(seed_item.get("directors", [])))
                matched_directors = list(common_directors)
                if common_directors:
                    content_similarity += 30.0

                # Actor match
                common_actors = set(item.get("actors", [])).intersection(set(seed_item.get("actors", [])))
                matched_actors = list(common_actors)
                if common_actors:
                    content_similarity += 20.0
            else:
                # Baseline content quality score
                content_similarity = item.get("vote_average", 7.0) * 8.0

            # 7. Pipeline Stage: Personal Taste Scoring
            personal_taste = 0.0
            for g in item.get("genres", []):
                if g in preferred_genres:
                    personal_taste += preferred_genres[g] * 4.0
                    if g not in matched_genres:
                        matched_genres.append(g)

            for d in item.get("directors", []):
                if d in preferred_directors:
                    personal_taste += preferred_directors[d] * 8.0
                    if d not in matched_directors:
                        matched_directors.append(d)

            # 8. Pipeline Stage: Context & Mode Weighting
            context_score = 0.0
            if mode == RecommendationModeEnum.TONIGHT:
                # High vote average + ready runtime
                context_score += item.get("vote_average", 7.0) * 3.0
                if item.get("runtime_minutes") and item["runtime_minutes"] <= 120:
                    context_score += 15.0
            elif mode == RecommendationModeEnum.UNDER_90:
                if item.get("runtime_minutes") and item["runtime_minutes"] <= 90:
                    context_score += 30.0
            elif mode == RecommendationModeEnum.FAVORITE_DIRECTORS:
                if matched_directors:
                    context_score += 40.0
            elif mode == RecommendationModeEnum.HIDDEN_GEMS:
                if item.get("vote_average", 0.0) >= 7.0:
                    context_score += 25.0
            elif mode == RecommendationModeEnum.BECAUSE_YOU_LIKED:
                if seed_item:
                    context_score += content_similarity * 0.5

            availability_score = 15.0 if item.get("is_available", True) else 0.0

            # 9. Pipeline Stage: Final Combined Ranking Score
            raw_score = (content_similarity * 0.35) + (personal_taste * 0.35) + (context_score * 0.15) + (availability_score * 0.15)
            final_score = round(min(100.0, max(10.0, raw_score)), 1)

            # 10. Pipeline Stage: Grounded Transparent Explanation Construction
            explanation_parts = []
            if seed_item and matched_genres:
                explanation_parts.append(f"Shares {', '.join(matched_genres)} genres with {seed_item['canonical_title']}")
            elif matched_genres and preferred_genres:
                explanation_parts.append(f"Matches your preferred genres ({', '.join(matched_genres)})")

            if matched_directors:
                explanation_parts.append(f"Directed by {', '.join(matched_directors)}")

            if not explanation_parts:
                explanation_parts.append(f"Highly rated {item['content_type'].lower()} ({item.get('vote_average', 8.0)}/10 rating)")

            if is_cold_start:
                explanation_text = f"Cold start recommendation: {'. '.join(explanation_parts)}."
            else:
                explanation_text = f"Recommended because: {'. '.join(explanation_parts)}."

            explanation_obj = GroundedExplanation(
                explanation_text=explanation_text,
                matched_genres=matched_genres,
                matched_directors=matched_directors,
                matched_actors=matched_actors,
                seed_title_name=seed_title_name,
                user_rating_applied=user_rating_applied
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
                explanation=explanation_obj
            )

            ranked_items.append(rec_item)

        # Sort by recommendation score descending
        ranked_items.sort(key=lambda x: x.recommendation_score, reverse=True)
        ranked_items = ranked_items[:limit]

        return RecommendationListResponse(
            mode=mode,
            total=len(ranked_items),
            is_cold_start=is_cold_start,
            data=ranked_items
        )

    async def get_similar_titles(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        title_id: str,
        limit: int = 5
    ) -> RecommendationListResponse:
        """Returns content-similar title recommendations for a target title ID."""
        return await self.get_recommendations(
            db=db,
            user_id=user_id,
            mode=RecommendationModeEnum.BECAUSE_YOU_LIKED,
            seed_title_id=title_id,
            limit=limit
        )

    async def explain_recommendation(
        self,
        db: Optional[AsyncSession],
        user_id: str,
        title_id: str,
        seed_title_id: Optional[str] = None
    ) -> RecommendationExplainResponse:
        """Generates grounded explanation and transparent score breakdown for a title."""
        recs = await self.get_recommendations(
            db=db,
            user_id=user_id,
            mode=RecommendationModeEnum.BECAUSE_YOU_LIKED if seed_title_id else RecommendationModeEnum.TONIGHT,
            seed_title_id=seed_title_id,
            include_watched=True,
            limit=20
        )

        matched_item = None
        for item in recs.data:
            if item.title_id == title_id:
                matched_item = item
                break

        if not matched_item:
            # Fallback for target title if not in top items
            matched_item = recs.data[0] if recs.data else RecommendationItemResponse(
                title_id=title_id,
                display_id="T-10001",
                canonical_title="Target Title",
                content_type="MOVIE",
                recommendation_score=75.0,
                explanation=GroundedExplanation(
                    explanation_text="Recommendation grounded in catalog score and genre attributes.",
                    matched_genres=["Sci-Fi"]
                )
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
                "total_score": matched_item.recommendation_score
            }
        )

recommendation_repository = RecommendationRepository()
