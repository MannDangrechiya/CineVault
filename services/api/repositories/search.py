# CineVault OS — Search Domain Repository
# Asynchronous PostgreSQL multi-entity search engine supporting multilingual titles, transliterations, aliases, genres, themes, and people (ADR-001, ERD V1)

import uuid
import unicodedata
import logging
import math
from typing import List, Optional, Set

from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import config
from ..schemas.search import SearchResultItem, SearchResponse
from ..models.canonical import TitleModel
from ..media_resolver import resolve_poster_url

logger = logging.getLogger("cinevault.repositories.search")

def normalize_search_query(q: str) -> str:
    if not q:
        return ""
    normalized = unicodedata.normalize("NFC", q).strip().lower()
    return normalized

class SearchRepository:
    """Provides async PostgreSQL search across canonical titles, aliases, people, and franchises."""

    async def search_catalog(
        self,
        db: Optional[AsyncSession],
        q: str,
        entity_type: Optional[str] = "ALL",
        content_type: Optional[str] = None,
        genre: Optional[str] = None,
        theme: Optional[str] = None,
        country: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 25,
        page: int = 1
    ) -> SearchResponse:
        clean_q = normalize_search_query(q)
        results: List[SearchResultItem] = []
        total_hits = 0
        total_pages = 1
        real_db_query_succeeded = False
        
        offset = (page - 1) * limit

        if db is not None and clean_q:
            try:
                # 1. Search Titles
                if entity_type in ("ALL", "TITLE"):
                    
                    if (
                        clean_q.startswith("mov-")
                        or clean_q.startswith("ani-")
                        or clean_q.startswith("tv-")
                        or clean_q.startswith("imdb-")
                        or clean_q.startswith("tmdb-")
                        or clean_q.startswith("kobis-")
                        or clean_q.startswith("tvdb-")
                        or clean_q.startswith("tt")
                    ):
                        stmt_id = select(TitleModel).where(
                            or_(
                                func.lower(TitleModel.display_id) == clean_q,
                                func.lower(TitleModel.display_id) == f"imdb-{clean_q}",
                                func.lower(TitleModel.display_id) == f"tmdb-{clean_q}",
                            )
                        )
                        exact_match = (await db.execute(stmt_id)).scalar_one_or_none()
                        if exact_match:
                            results.append(
                                SearchResultItem(
                                    id=str(exact_match.title_id),
                                    display_id=exact_match.display_id,
                                    canonical_title=exact_match.canonical_title,
                                    original_title=exact_match.original_title,
                                    poster_url=resolve_poster_url(exact_match.poster_url),
                                    entity_type="TITLE",
                                    content_type=exact_match.content_type_id,
                                    production_year=exact_match.production_year,
                                    relevance_score=1.0
                                )
                            )
                            return SearchResponse(query=q, total_hits=1, page=1, total_pages=1, results=results)

                    q_prefix = f"{clean_q}%"
                    sql_query = """
                        WITH candidate_scores AS (
                            SELECT 
                                t.title_id,
                                GREATEST(
                                    CASE WHEN lower(t.canonical_title) = :q THEN 1.0 ELSE 0 END,
                                    CASE WHEN lower(t.original_title) = :q THEN 0.95 ELSE 0 END,
                                    CASE WHEN t.canonical_title ILIKE :q_prefix THEN 0.85 ELSE 0 END,
                                    similarity(t.canonical_title, :q) * 0.8,
                                    similarity(t.original_title, :q) * 0.75,
                                    COALESCE(MAX(CASE WHEN lower(a.alias_name) = :q THEN 0.9 ELSE 0 END), 0),
                                    COALESCE(MAX(similarity(a.alias_name, :q) * 0.7), 0)
                                ) AS score
                            FROM canonical.title t
                            LEFT JOIN canonical.title_alias a ON t.title_id = a.title_id
                            WHERE 
                                t.canonical_title ILIKE :q_prefix
                                OR t.canonical_title % :q 
                                OR t.original_title % :q
                                OR a.alias_name % :q
                            GROUP BY t.title_id
                        )
                        SELECT 
                            t.title_id, t.display_id, t.canonical_title, t.original_title, t.poster_url, 
                            t.content_type_id, t.production_year, cs.score,
                            COUNT(*) OVER() as full_count
                        FROM candidate_scores cs
                        JOIN canonical.title t ON t.title_id = cs.title_id
                        WHERE cs.score > 0.1
                    """
                    
                    params = {"q": clean_q, "q_prefix": q_prefix, "limit": limit, "offset": offset}
                    
                    where_clauses = []
                    if content_type:
                        where_clauses.append("t.content_type_id = :content_type")
                        params["content_type"] = content_type
                    if year:
                        where_clauses.append("t.production_year = :year")
                        params["year"] = year
                    if genre:
                        where_clauses.append("EXISTS (SELECT 1 FROM canonical.title_genre tg WHERE tg.title_id = t.title_id AND tg.genre_id = :genre)")
                        params["genre"] = genre
                    if theme:
                        where_clauses.append("EXISTS (SELECT 1 FROM canonical.title_theme th WHERE th.title_id = t.title_id AND th.theme_id = :theme)")
                        params["theme"] = theme
                    if country:
                        where_clauses.append("EXISTS (SELECT 1 FROM canonical.title_country tc WHERE tc.title_id = t.title_id AND tc.country_code = :country)")
                        params["country"] = country

                    if where_clauses:
                        sql_query += " AND " + " AND ".join(where_clauses)
                        
                    sql_query += " ORDER BY cs.score DESC, t.title_id DESC LIMIT :limit OFFSET :offset"

                    title_res = await db.execute(text(sql_query), params)
                    rows = title_res.all()

                    if rows:
                        total_hits = rows[0].full_count
                        total_pages = math.ceil(total_hits / limit)
                        
                    for r in rows:
                        results.append(
                            SearchResultItem(
                                id=str(r.title_id),
                                display_id=r.display_id,
                                canonical_title=r.canonical_title,
                                original_title=r.original_title,
                                poster_url=resolve_poster_url(r.poster_url),
                                entity_type="TITLE",
                                content_type=r.content_type_id,
                                production_year=r.production_year,
                                relevance_score=float(r.score)
                            )
                        )

                if page == 1 and not (genre or theme or country or year or content_type):
                    seen_ids = set([r.id for r in results])
                    
                    if entity_type in ("ALL", "FRANCHISE") and len(results) < limit:
                        franchise_sql = """
                            WITH cs AS (
                                SELECT franchise_id, name,
                                GREATEST(
                                    CASE WHEN lower(name) = :q THEN 1.0 ELSE 0 END,
                                    similarity(name, :q) * 0.9
                                ) AS score
                                FROM canonical.franchise
                                WHERE name % :q OR name ILIKE :q_prefix
                            )
                            SELECT franchise_id, name, score FROM cs WHERE score > 0.1 ORDER BY score DESC LIMIT :lim
                        """
                        franchise_res = await db.execute(text(franchise_sql), {"q": clean_q, "q_prefix": f"{clean_q}%", "lim": limit})
                        for r in franchise_res.all():
                            f_id = str(r.franchise_id)
                            if f_id in seen_ids: continue
                            seen_ids.add(f_id)
                            results.append(
                                SearchResultItem(
                                    id=f_id, display_id=f"FRAN-{f_id[:6].upper()}",
                                    canonical_title=r.name, entity_type="FRANCHISE",
                                    relevance_score=float(r.score)
                                )
                            )

                    if entity_type in ("ALL", "PERSON") and len(results) < limit:
                        person_sql = """
                            WITH cs AS (
                                SELECT p.person_id, p.canonical_name,
                                GREATEST(
                                    CASE WHEN lower(p.canonical_name) = :q THEN 1.0 ELSE 0 END,
                                    similarity(p.canonical_name, :q) * 0.9,
                                    COALESCE(MAX(CASE WHEN lower(pn.name_value) = :q THEN 0.85 ELSE 0 END), 0),
                                    COALESCE(MAX(similarity(pn.name_value, :q) * 0.8), 0)
                                ) AS score
                                FROM canonical.person p
                                LEFT JOIN canonical.person_name pn ON p.person_id = pn.person_id
                                WHERE p.canonical_name % :q OR pn.name_value % :q OR p.canonical_name ILIKE :q_prefix
                                GROUP BY p.person_id, p.canonical_name
                            )
                            SELECT person_id, canonical_name, score FROM cs WHERE score > 0.1 ORDER BY score DESC LIMIT :lim
                        """
                        person_res = await db.execute(text(person_sql), {"q": clean_q, "q_prefix": f"{clean_q}%", "lim": limit})
                        for r in person_res.all():
                            p_id = str(r.person_id)
                            if p_id in seen_ids: continue
                            seen_ids.add(p_id)
                            results.append(
                                SearchResultItem(
                                    id=p_id, display_id=f"PER-{p_id[:6].upper()}",
                                    canonical_title=r.canonical_name, entity_type="PERSON",
                                    relevance_score=float(r.score)
                                )
                            )
                            
                    results.sort(key=lambda x: x.relevance_score, reverse=True)
                    if entity_type == "ALL" and total_hits == 0:
                        total_hits = len(results)
                        total_pages = 1
                
                real_db_query_succeeded = True
            except Exception as e:
                logger.error(f"Database query search_catalog failed: {e}", exc_info=True)
                if not config.allow_seed_fallback:
                    raise

        if not results and clean_q and not real_db_query_succeeded:
            pass 

        return SearchResponse(
            query=q,
            total_hits=total_hits,
            page=page,
            total_pages=total_pages,
            results=results[:limit]
        )

search_repository = SearchRepository()
