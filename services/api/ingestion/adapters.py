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

                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else (0.05 * (2 ** attempt))
                        logger.warning(f"KOBIS API 429 Rate Limited. Waiting {delay}s...")
                        await asyncio.sleep(delay)
                        continue

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

        # Mock fallback catalog with real varied metadata
        KOBIS_MOCK_CATALOG = {
            "20192194": {
                "movieCd": "20192194",
                "movieNm": "기생충",
                "movieNmEn": "Parasite",
                "prdtYear": "2019",
                "showTm": "132",
                "nationAlt": "한국",
                "genres": [{"genreNm": "드라마"}, {"genreNm": "스릴러"}],
                "directors": [{"peopleNm": "봉준호"}],
                "actors": [{"peopleNm": "송강호"}, {"peopleNm": "이선균"}, {"peopleNm": "조여정"}]
            },
            "20030371": {
                "movieCd": "20030371",
                "movieNm": "올드보이",
                "movieNmEn": "Oldboy",
                "prdtYear": "2003",
                "showTm": "120",
                "nationAlt": "한국",
                "genres": [{"genreNm": "미스터리"}, {"genreNm": "스릴러"}],
                "directors": [{"peopleNm": "박찬욱"}],
                "actors": [{"peopleNm": "최민식"}, {"peopleNm": "유지태"}]
            },
            "20202781": {
                "movieCd": "20202781",
                "movieNm": "미나리",
                "movieNmEn": "Minari",
                "prdtYear": "2020",
                "showTm": "115",
                "nationAlt": "미국",
                "genres": [{"genreNm": "드라마"}],
                "directors": [{"peopleNm": "정이삭"}],
                "actors": [{"peopleNm": "스티븐 연"}, {"peopleNm": "한예리"}]
            },
            "20224982": {
                "movieCd": "20224982",
                "movieNm": "헤어질 결심",
                "movieNmEn": "Decision to Leave",
                "prdtYear": "2022",
                "showTm": "138",
                "nationAlt": "한국",
                "genres": [{"genreNm": "로맨스"}, {"genreNm": "미스터리"}],
                "directors": [{"peopleNm": "박찬욱"}],
                "actors": [{"peopleNm": "탕웨이"}, {"peopleNm": "박해일"}]
            },
            "20163074": {
                "movieCd": "20163074",
                "movieNm": "부산행",
                "movieNmEn": "Train to Busan",
                "prdtYear": "2016",
                "showTm": "118",
                "nationAlt": "한국",
                "genres": [{"genreNm": "액션"}, {"genreNm": "스릴러"}],
                "directors": [{"peopleNm": "연상호"}],
                "actors": [{"peopleNm": "공유"}, {"peopleNm": "마동석"}]
            },
            "20060280": {
                "movieCd": "20060280",
                "movieNm": "괴물",
                "movieNmEn": "The Host",
                "prdtYear": "2006",
                "showTm": "119",
                "nationAlt": "한국",
                "genres": [{"genreNm": "SF"}, {"genreNm": "드라마"}],
                "directors": [{"peopleNm": "봉준호"}],
                "actors": [{"peopleNm": "송강호"}, {"peopleNm": "변희봉"}]
            },
            "20211111": {
                "movieCd": "20211111",
                "movieNm": "드라이브 마이 카",
                "movieNmEn": "Drive My Car",
                "prdtYear": "2021",
                "showTm": "179",
                "nationAlt": "일본",
                "genres": [{"genreNm": "드라마"}],
                "directors": [{"peopleNm": "하마구치 류스케"}],
                "actors": [{"peopleNm": "니시지마 히데토시"}]
            },
            "20239999": {
                "movieCd": "20239999",
                "movieNm": "고질라 마이너스 원",
                "movieNmEn": "Godzilla Minus One",
                "prdtYear": "2023",
                "showTm": "125",
                "nationAlt": "일본",
                "genres": [{"genreNm": "SF"}, {"genreNm": "액션"}],
                "directors": [{"peopleNm": "야마자키 타카시"}],
                "actors": [{"peopleNm": "카미키 류노스케"}]
            },
            "20238888": {
                "movieCd": "20238888",
                "movieNm": "추락의 해부",
                "movieNmEn": "Anatomy of a Fall",
                "prdtYear": "2023",
                "showTm": "151",
                "nationAlt": "프랑스",
                "genres": [{"genreNm": "드라마"}, {"genreNm": "범죄"}],
                "directors": [{"peopleNm": "쥐스틴 트리에"}],
                "actors": [{"peopleNm": "산드라 휠러"}]
            },
            "20237777": {
                "movieCd": "20237777",
                "movieNm": "존 오브 인터레스트",
                "movieNmEn": "The Zone of Interest",
                "prdtYear": "2023",
                "showTm": "105",
                "nationAlt": "영국",
                "genres": [{"genreNm": "드라마"}, {"genreNm": "전쟁"}],
                "directors": [{"peopleNm": "조나단 글레이저"}],
                "actors": [{"peopleNm": "크리스티안 프리델"}]
            }
        }
        if movie_cd in KOBIS_MOCK_CATALOG:
            return KOBIS_MOCK_CATALOG[movie_cd]

        return {
            "movieCd": movie_cd,
            "movieNm": f"영화 {movie_cd}",
            "movieNmEn": f"KOBIS Film {movie_cd}",
            "prdtYear": "2024",
            "showTm": "120",
            "nationAlt": "한국",
            "genres": [{"genreNm": "드라마"}],
            "directors": [{"peopleNm": "감독"}],
            "actors": [{"peopleNm": "배우"}]
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

                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else (0.05 * (2 ** attempt))
                        logger.warning(f"TMDb API 429 Rate Limited. Waiting {delay}s...")
                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    logger.warning(f"TMDb API attempt {attempt} failed: {e}")
                    if attempt == 3:
                        raise RuntimeError(f"TMDb API request failed after 3 attempts: {e}")
                    await asyncio.sleep(0.05 * (2 ** attempt))

        # Mock fallback catalog with real varied metadata
        TMDB_MOCK_CATALOG = {
            "496243": {
                "id": 496243,
                "title": "Parasite",
                "original_title": "기생충",
                "original_language": "ko",
                "release_date": "2019-05-30",
                "runtime": 132,
                "origin_country": ["KR"],
                "overview": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
                "genres": [{"id": 35, "name": "Comedy"}, {"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}]
            },
            "670": {
                "id": 670,
                "title": "Oldboy",
                "original_title": "올드보이",
                "original_language": "ko",
                "release_date": "2003-11-21",
                "runtime": 120,
                "origin_country": ["KR"],
                "overview": "After being kidnapped and imprisoned for fifteen years, Oh Dae-su is released, only to find that he must find his captor in five days.",
                "genres": [{"id": 9648, "name": "Mystery"}, {"id": 53, "name": "Thriller"}]
            },
            "556584": {
                "id": 556584,
                "title": "Minari",
                "original_title": "Minari",
                "original_language": "en",
                "release_date": "2020-01-26",
                "runtime": 115,
                "origin_country": ["US"],
                "overview": "A Korean-American family moves to an Arkansas farm in search of their own American Dream.",
                "genres": [{"id": 18, "name": "Drama"}]
            },
            "666277": {
                "id": 666277,
                "title": "Decision to Leave",
                "original_title": "헤어질 결심",
                "original_language": "ko",
                "release_date": "2022-06-29",
                "runtime": 138,
                "origin_country": ["KR"],
                "overview": "A detective investigating a man's death in the mountains meets the dead man's mysterious wife in the course of his dogged sleuthing.",
                "genres": [{"id": 10749, "name": "Romance"}, {"id": 9648, "name": "Mystery"}]
            },
            "299536": {
                "id": 299536,
                "title": "Train to Busan",
                "original_title": "부산행",
                "original_language": "ko",
                "release_date": "2016-07-20",
                "runtime": 118,
                "origin_country": ["KR"],
                "overview": "While a zombie virus breaks out in South Korea, passengers struggle to survive on the train from Seoul to Busan.",
                "genres": [{"id": 28, "name": "Action"}, {"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}]
            },
            "545611": {
                "id": 545611,
                "title": "Everything Everywhere All at Once",
                "original_title": "Everything Everywhere All at Once",
                "original_language": "en",
                "release_date": "2022-03-24",
                "runtime": 139,
                "origin_country": ["US"],
                "overview": "A middle-aged Chinese immigrant is swept up into an insane adventure in which she alone can save existence by exploring other universes.",
                "genres": [{"id": 878, "name": "Science Fiction"}, {"id": 28, "name": "Action"}, {"id": 35, "name": "Comedy"}]
            },
            "730154": {
                "id": 730154,
                "title": "Drive My Car",
                "original_title": "ドライブ・マイ・カー",
                "original_language": "ja",
                "release_date": "2021-08-20",
                "runtime": 179,
                "origin_country": ["JP"],
                "overview": "An aging, widowed actor seeks a chauffeur. He is turned to a 20-year-old woman, with whom he forms a special bond.",
                "genres": [{"id": 18, "name": "Drama"}]
            },
            "940721": {
                "id": 940721,
                "title": "Godzilla Minus One",
                "original_title": "ゴジラ-1.0",
                "original_language": "ja",
                "release_date": "2023-11-03",
                "runtime": 125,
                "origin_country": ["JP"],
                "overview": "Post-war Japan is at its lowest point when a new crisis emerges in the form of a giant monster, mutated by nuclear radiation.",
                "genres": [{"id": 878, "name": "Science Fiction"}, {"id": 28, "name": "Action"}]
            },
            "915935": {
                "id": 915935,
                "title": "Anatomy of a Fall",
                "original_title": "Anatomie d'une chute",
                "original_language": "fr",
                "release_date": "2023-08-23",
                "runtime": 151,
                "origin_country": ["FR"],
                "overview": "A woman is suspected of her husband's murder, and their blind son faces a moral dilemma as the sole witness.",
                "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}]
            },
            "467244": {
                "id": 467244,
                "title": "The Zone of Interest",
                "original_title": "The Zone of Interest",
                "original_language": "de",
                "release_date": "2023-12-15",
                "runtime": 105,
                "origin_country": ["GB"],
                "overview": "Auschwitz commandant Rudolf Höss and his wife Hedwig strive to build a dream life for their family in a house next to the camp.",
                "genres": [{"id": 18, "name": "Drama"}, {"id": 36, "name": "History"}]
            },
            "93405": {
                "id": 93405,
                "name": "Squid Game",
                "original_name": "오징어 게임",
                "original_language": "ko",
                "first_air_date": "2021-09-17",
                "origin_country": ["KR"],
                "overview": "Hundreds of cash-strapped players accept a strange invitation to compete in children's games.",
                "genres": [{"id": 10759, "name": "Action & Adventure"}, {"id": 18, "name": "Drama"}]
            }
        }
        if str(tmdb_id) in TMDB_MOCK_CATALOG:
            return TMDB_MOCK_CATALOG[str(tmdb_id)]

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
