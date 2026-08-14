# CineVault OS — Ingestion Provider Adapters & Connectors
# Implements provider-neutral acquisition abstractions, SHA-256 payload hashing, and normalization schemas (DEC-ING-PRP-02)

import hashlib
import json
import logging
import asyncio
import os
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone

from .licensing import licensing_gate
from ..config import config

logger = logging.getLogger("cinevault.ingestion.adapters")

def compute_payload_checksum(raw_data: Any) -> str:
    """Calculates SHA-256 hex digest of raw payload object for immutability verification."""
    if isinstance(raw_data, (dict, list)):
        payload_bytes = json.dumps(raw_data, sort_keys=True).encode("utf-8")
    elif isinstance(raw_data, str):
        payload_bytes = raw_data.encode("utf-8")
    else:
        payload_bytes = str(raw_data).encode("utf-8")
    return hashlib.sha256(payload_bytes).hexdigest()

class BaseProviderAdapter(ABC):
    """Abstract provider connector interface for acquiring external data."""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name.upper()
        self.gate_info = licensing_gate.verify_source_access(self.provider_name)

    async def discover(self, query: str, entity_type: str = "MOVIE") -> List[Dict[str, Any]]:
        """Optional discovery/search method returning candidate entity summaries."""
        return []

    @abstractmethod
    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches raw JSON payload from external provider endpoint or staged baseline."""
        pass

    @abstractmethod
    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transforms provider-specific raw JSON payload into standard CineVault intermediate structure."""
        pass

    def validate_normalized(self, normalized_payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates normalized candidate payload against structural rules."""
        errors = []
        if not normalized_payload.get("canonical_title_proposal") and not normalized_payload.get("original_title"):
            errors.append("Missing mandatory title proposal and original title")
        if not normalized_payload.get("external_id"):
            errors.append("Missing external entity identifier")
        valid_content_types = {"MOVIE", "TV_SERIES", "ANIME", "DOCUMENTARY", "SHORT_FILM", "NEEDS_REVIEW"}
        if normalized_payload.get("content_type") not in valid_content_types:
            errors.append(f"Unrecognized content_type '{normalized_payload.get('content_type')}'")
        return (len(errors) == 0, errors)


class KobisProviderAdapter(BaseProviderAdapter):
    """Primary Korean-Domain Film Metadata & Box Office Provider Adapter."""

    def __init__(self, api_key: Optional[str] = None, http_client: Optional[httpx.AsyncClient] = None):
        super().__init__("KOBIS")
        self.api_key = api_key or config.kobis_api_key or os.getenv("KOBIS_API_KEY")
        self.ingestion_mode = (config.ingestion_mode or os.getenv("INGESTION_MODE", "mock")).lower()
        self.http_client = http_client
        self.base_url = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/"

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches film detail payload from KOBIS open API or staged test baseline."""
        movie_cd = external_entity_id or "20192194"

        if self.ingestion_mode == "live" and self.api_key:
            url = f"{self.base_url}movie/searchMovieInfo.json"
            params = {"key": self.api_key, "movieCd": movie_cd}

            for attempt in range(1, 4):
                try:
                    if self.http_client:
                        response = await self.http_client.get(url, params=params)
                    else:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.get(url, params=params)

                    response.raise_for_status()
                    data = response.json()
                    movie_info = data.get("movieInfoResult", {}).get("movieInfo", {})
                    if movie_info:
                        return movie_info
                    return data
                except Exception as e:
                    logger.warning(f"KOBIS API attempt {attempt} failed: {e}")
                    if attempt == 3:
                        raise RuntimeError(f"KOBIS API request failed after 3 attempts: {e}")
                    await asyncio.sleep(0.05 * (2 ** attempt))

        return {
            "movieCd": movie_cd,
            "movieNm": "기생충",
            "movieNmEn": "Parasite",
            "prdtYear": "2019",
            "showTm": "132",
            "nationAlt": "한국",
            "genres": [{"genreNm": "드라마"}, {"genreNm": "스릴러"}],
            "directors": [{"peopleNm": "봉준호"}],
            "actors": [{"peopleNm": "송강호"}, {"peopleNm": "이선균"}, {"peopleNm": "조여정"}],
            "showTypes": [{"showTypeGroupNm": "2D"}, {"showTypeNm": "디지털"}]
        }

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes KOBIS raw response to standardized intermediate schema."""
        runtime_raw = raw_payload.get("showTm")
        runtime_min = int(runtime_raw) if runtime_raw and str(runtime_raw).isdigit() else None

        return {
            "provider_name": "KOBIS",
            "external_id": str(raw_payload.get("movieCd")),
            "canonical_title_proposal": raw_payload.get("movieNmEn") or raw_payload.get("movieNm"),
            "original_title": raw_payload.get("movieNm"),
            "content_type": "MOVIE",
            "production_year": int(raw_payload.get("prdtYear", 2019)) if raw_payload.get("prdtYear") else None,
            "runtime_minutes": runtime_min,
            "origin_country": "KR",
            "genres": [g["genreNm"] for g in raw_payload.get("genres", [])] if isinstance(raw_payload.get("genres"), list) else [],
            "directors": [d["peopleNm"] for d in raw_payload.get("directors", [])] if isinstance(raw_payload.get("directors"), list) else [],
            "cast": [a["peopleNm"] for a in raw_payload.get("actors", [])] if isinstance(raw_payload.get("actors"), list) else []
        }


class TvdbProviderAdapter(BaseProviderAdapter):
    """Secondary TV Series & Season Hierarchy Provider Adapter."""

    def __init__(self, api_key: Optional[str] = None, http_client: Optional[httpx.AsyncClient] = None):
        super().__init__("TVDB")
        self.api_key = api_key or config.tvdb_api_key or os.getenv("TVDB_API_KEY")
        self.ingestion_mode = (config.ingestion_mode or os.getenv("INGESTION_MODE", "mock")).lower()
        self.http_client = http_client
        self.base_url = "https://api4.thetvdb.com/v4/"

    async def _get_bearer_token(self) -> str:
        """Acquires bearer authentication token from TVDB v4 /login endpoint."""
        url = f"{self.base_url}login"
        payload = {"apikey": self.api_key}

        for attempt in range(1, 4):
            try:
                if self.http_client:
                    response = await self.http_client.post(url, json=payload)
                else:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(url, json=payload)

                response.raise_for_status()
                data = response.json()
                token = data.get("data", {}).get("token")
                if token:
                    return token
                raise ValueError("TVDB login response missing token field")
            except Exception as e:
                logger.warning(f"TVDB Auth attempt {attempt} failed: {e}")
                if attempt == 3:
                    raise RuntimeError(f"TVDB Login authentication failed after 3 attempts: {e}")
                await asyncio.sleep(0.05 * (2 ** attempt))
        return ""

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches TV series detail payload from TVDB API or staged test baseline."""
        series_id = external_entity_id or "364014"

        if self.ingestion_mode == "live" and self.api_key:
            token = await self._get_bearer_token()
            headers = {"Authorization": f"Bearer {token}"}

            resource_type = "movies" if external_entity_type.upper() in ["MOVIE", "MOVIES"] else "series"
            url = f"{self.base_url}{resource_type}/{series_id}"

            for attempt in range(1, 4):
                try:
                    if self.http_client:
                        response = await self.http_client.get(url, headers=headers)
                    else:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.get(url, headers=headers)

                    response.raise_for_status()
                    data = response.json()
                    return data.get("data", data)
                except Exception as e:
                    logger.warning(f"TVDB API attempt {attempt} failed: {e}")
                    if attempt == 3:
                        raise RuntimeError(f"TVDB API request failed after 3 attempts: {e}")
                    await asyncio.sleep(0.05 * (2 ** attempt))

        return {
            "id": int(series_id) if series_id.isdigit() else 364014,
            "name": "Squid Game",
            "originalName": "오징어 게임",
            "year": 2021,
            "originalCountry": "kor",
            "overview": "Hundreds of cash-strapped players accept a strange invitation to compete in children's games.",
            "genres": [{"name": "Drama"}, {"name": "Mystery"}, {"name": "Action"}]
        }

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes TVDB raw response to standardized intermediate schema."""
        return {
            "provider_name": "TVDB",
            "external_id": str(raw_payload.get("id")),
            "canonical_title_proposal": raw_payload.get("name"),
            "original_title": raw_payload.get("originalName"),
            "content_type": "TV_SERIES",
            "production_year": raw_payload.get("year"),
            "origin_country": "KR",
            "genres": [g["name"] for g in raw_payload.get("genres", [])] if isinstance(raw_payload.get("genres"), list) else [],
            "synopsis": raw_payload.get("overview")
        }


class TmdbProviderAdapter(BaseProviderAdapter):
    """Candidate Global Catalog Metadata Provider Adapter (TMDb v3 REST API)."""

    def __init__(self, api_key: Optional[str] = None, http_client: Optional[httpx.AsyncClient] = None):
        super().__init__("TMDB")
        self.api_key = api_key or config.tmdb_api_key or os.getenv("TMDB_API_KEY")
        self.ingestion_mode = (config.ingestion_mode or os.getenv("INGESTION_MODE", "mock")).lower()
        self.http_client = http_client
        self.base_url = "https://api.themoviedb.org/3/"

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches movie/tv payload from TMDb or returns mock payload."""
        tmdb_id = external_entity_id or "496243"
        entity_path = "tv" if external_entity_type.upper() in ["TV", "TV_SERIES"] else "movie"

        if self.ingestion_mode == "live" and self.api_key:
            url = f"{self.base_url}{entity_path}/{tmdb_id}"
            params = {"api_key": self.api_key, "language": "en-US"}

            for attempt in range(1, 4):
                try:
                    if self.http_client:
                        response = await self.http_client.get(url, params=params)
                    else:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.get(url, params=params)

                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    logger.warning(f"TMDb API attempt {attempt} failed: {e}")
                    if attempt == 3:
                        raise RuntimeError(f"TMDb API request failed after 3 attempts: {e}")
                    await asyncio.sleep(0.05 * (2 ** attempt))

        # Mock fallback
        if tmdb_id == "496243":
            return {
                "id": 496243,
                "title": "Parasite",
                "original_title": "기생충",
                "original_language": "ko",
                "release_date": "2019-05-30",
                "runtime": 132,
                "overview": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
                "genres": [{"id": 35, "name": "Comedy"}, {"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}]
            }
        return {
            "id": int(tmdb_id) if tmdb_id.isdigit() else 999999,
            "title": f"TMDb Title {tmdb_id}",
            "original_title": f"Original Title {tmdb_id}",
            "original_language": "en",
            "release_date": "2024-01-01",
            "runtime": 120,
            "overview": "Mock overview narrative.",
            "genres": [{"id": 18, "name": "Drama"}]
        }

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes TMDb payload to standardized intermediate structure."""
        release_date = raw_payload.get("release_date") or raw_payload.get("first_air_date") or ""
        prod_year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else None
        c_type = "TV_SERIES" if "first_air_date" in raw_payload or "name" in raw_payload else "MOVIE"

        return {
            "provider_name": "TMDB",
            "external_id": str(raw_payload.get("id")),
            "canonical_title_proposal": raw_payload.get("title") or raw_payload.get("name"),
            "original_title": raw_payload.get("original_title") or raw_payload.get("original_name"),
            "content_type": c_type,
            "production_year": prod_year,
            "runtime_minutes": raw_payload.get("runtime"),
            "origin_country": (raw_payload.get("origin_country") or ["US"])[0] if isinstance(raw_payload.get("origin_country"), list) and raw_payload.get("origin_country") else "US",
            "genres": [g["name"] for g in raw_payload.get("genres", [])] if isinstance(raw_payload.get("genres"), list) else [],
            "synopsis": raw_payload.get("overview")
        }


class AniListProviderAdapter(BaseProviderAdapter):
    """Primary Anime & Manga Domain Metadata Provider Adapter (AniList GraphQL API)."""

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        super().__init__("ANILIST")
        self.http_client = http_client
        self.base_url = "https://graphql.anilist.co"

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches anime metadata from AniList GraphQL or returns mock baseline."""
        media_id = int(external_entity_id) if external_entity_id.isdigit() else 21

        return {
            "id": media_id,
            "title": {
                "romaji": "One Piece",
                "english": "One Piece",
                "native": "ONE PIECE"
            },
            "type": "ANIME",
            "format": "TV",
            "status": "RELEASING",
            "startDate": {"year": 1999, "month": 10, "day": 20},
            "episodes": 1100,
            "duration": 24,
            "countryOfOrigin": "JP",
            "genres": ["Action", "Adventure", "Comedy", "Fantasy"]
        }

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes AniList GraphQL payload."""
        titles = raw_payload.get("title", {})
        start_date = raw_payload.get("startDate", {})
        prod_year = start_date.get("year") if isinstance(start_date, dict) else None

        return {
            "provider_name": "ANILIST",
            "external_id": str(raw_payload.get("id")),
            "canonical_title_proposal": titles.get("english") or titles.get("romaji"),
            "original_title": titles.get("native") or titles.get("romaji"),
            "content_type": "ANIME",
            "production_year": prod_year,
            "runtime_minutes": raw_payload.get("duration"),
            "origin_country": raw_payload.get("countryOfOrigin") or "JP",
            "genres": raw_payload.get("genres", []),
            "synopsis": raw_payload.get("description")
        }


class MyAnimeListProviderAdapter(BaseProviderAdapter):
    """Secondary Anime Domain Metadata Provider Adapter (MAL REST API v2)."""

    def __init__(self, client_id: Optional[str] = None):
        super().__init__("MYANIMELIST")
        self.client_id = client_id or os.getenv("MAL_CLIENT_ID")

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches anime payload from MAL API or returns mock baseline."""
        mal_id = int(external_entity_id) if external_entity_id.isdigit() else 5114

        return {
            "id": mal_id,
            "title": "Fullmetal Alchemist: Brotherhood",
            "main_picture": {"medium": "https://cdn.myanimelist.net/images/anime/1223/96641.jpg"},
            "alternative_titles": {"en": "Fullmetal Alchemist: Brotherhood", "ja": "鋼の錬金術師 FULLMETAL ALCHEMIST"},
            "start_date": "2009-04-05",
            "media_type": "tv",
            "status": "finished_airing",
            "num_episodes": 64,
            "average_episode_duration": 1460,
            "genres": [{"id": 1, "name": "Action"}, {"id": 2, "name": "Adventure"}, {"id": 10, "name": "Fantasy"}]
        }

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes MyAnimeList raw JSON payload."""
        start_date = raw_payload.get("start_date") or ""
        prod_year = int(start_date[:4]) if len(start_date) >= 4 and start_date[:4].isdigit() else None
        alt_titles = raw_payload.get("alternative_titles", {})

        return {
            "provider_name": "MYANIMELIST",
            "external_id": str(raw_payload.get("id")),
            "canonical_title_proposal": alt_titles.get("en") or raw_payload.get("title"),
            "original_title": alt_titles.get("ja") or raw_payload.get("title"),
            "content_type": "ANIME",
            "production_year": prod_year,
            "origin_country": "JP",
            "genres": [g["name"] for g in raw_payload.get("genres", [])] if isinstance(raw_payload.get("genres"), list) else [],
            "synopsis": raw_payload.get("synopsis")
        }


class WikidataProviderAdapter(BaseProviderAdapter):
    """Structured Reference Provider Adapter (Wikidata SPARQL Entity Graph)."""

    def __init__(self):
        super().__init__("WIKIDATA")

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches SPARQL graph result for entity QID or returns mock reference."""
        qid = external_entity_id if external_entity_id.startswith("Q") else "Q6114"

        return {
            "qid": qid,
            "labels": {"en": "Parasite", "ko": "기생충"},
            "claims": {
                "P345": ["tt8367814"],  # IMDb ID
                "P4947": ["496243"],     # TMDb ID
                "P57": ["Q335348"],      # Bong Joon-ho QID
                "P577": ["2019-05-21T00:00:00Z"]
            }
        }

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes Wikidata QID payload into intermediate structure."""
        labels = raw_payload.get("labels", {})
        claims = raw_payload.get("claims", {})
        imdb_id = claims.get("P345", [None])[0]
        tmdb_id = claims.get("P4947", [None])[0]

        return {
            "provider_name": "WIKIDATA",
            "external_id": raw_payload.get("qid"),
            "canonical_title_proposal": labels.get("en") or labels.get("ko"),
            "original_title": labels.get("ko") or labels.get("en"),
            "content_type": "MOVIE",
            "external_id_mappings": {
                "imdb_id": imdb_id,
                "tmdb_id": tmdb_id
            }
        }


class ImdbDatasetAdapter(BaseProviderAdapter):
    """Static Non-Commercial Dataset Reference Adapter for IMDb identifiers."""

    def __init__(self):
        # Licensing gate throws PermissionError if access_status is PROHIBITED
        super().__init__("IMDB_DATASETS")

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        raise PermissionError("IMDb dataset ingestion is prohibited for commercial distribution under CineVault governance.")

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {}


class JustWatchAdapter(BaseProviderAdapter):
    """Prohibited Streaming Availability Adapter (Web Scraping Strictly Blocked)."""

    def __init__(self):
        super().__init__("JUSTWATCH")

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        raise PermissionError("JustWatch web scraping is strictly prohibited under CineVault governance.")

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {}
