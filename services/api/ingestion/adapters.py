# CineVault OS — Ingestion Provider Adapters & Connectors
# Implements provider-neutral acquisition abstractions, SHA-256 payload hashing, and normalization schemas (DEC-ING-PRP-02)

import hashlib
import json
import logging
import asyncio
import os
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
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
        self.provider_name = provider_name
        self.gate_info = licensing_gate.verify_source_access(provider_name)

    @abstractmethod
    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches raw JSON payload from external provider endpoint or staged baseline."""
        pass

    @abstractmethod
    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transforms provider-specific raw JSON payload into standard CineVault intermediate structure."""
        pass

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

        # Mock fallback baseline
        return {
            "movieCd": movie_cd,
            "movieNm": "기생충",
            "movieNmEn": "Parasite",
            "prdtYear": "2019",
            "nationAlt": "한국",
            "genres": [{"genreNm": "드라마"}, {"genreNm": "스릴러"}],
            "directors": [{"peopleNm": "봉준호"}],
            "actors": [{"peopleNm": "송강호"}, {"peopleNm": "이선균"}, {"peopleNm": "조여정"}],
            "showTypes": [{"showTypeGroupNm": "2D"}, {"showTypeNm": "디지털"}]
        }

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes KOBIS raw response to standardized intermediate schema."""
        return {
            "provider_name": "KOBIS",
            "external_id": raw_payload.get("movieCd"),
            "canonical_title_proposal": raw_payload.get("movieNmEn") or raw_payload.get("movieNm"),
            "original_title": raw_payload.get("movieNm"),
            "content_type": "MOVIE",
            "production_year": int(raw_payload.get("prdtYear", 2019)) if raw_payload.get("prdtYear") else None,
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

        # Mock fallback baseline
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
