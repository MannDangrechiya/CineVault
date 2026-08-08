# CineVault OS — Ingestion Provider Adapters & Connectors
# Implements provider-neutral acquisition abstractions, SHA-256 payload hashing, and normalization schemas (DEC-ING-PRP-02)

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .licensing import licensing_gate

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

    def __init__(self):
        super().__init__("KOBIS")

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches film detail payload from KOBIS open API or staged test baseline."""
        return {
            "movieCd": external_entity_id or "20192194",
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
            "genres": [g["genreNm"] for g in raw_payload.get("genres", [])],
            "directors": [d["peopleNm"] for d in raw_payload.get("directors", [])],
            "cast": [a["peopleNm"] for a in raw_payload.get("actors", [])]
        }

class TvdbProviderAdapter(BaseProviderAdapter):
    """Secondary TV Series & Season Hierarchy Provider Adapter."""

    def __init__(self):
        super().__init__("TVDB")

    async def fetch_raw_payload(self, external_entity_type: str, external_entity_id: str) -> Dict[str, Any]:
        """Fetches TV series detail payload from TVDB API or staged test baseline."""
        return {
            "id": int(external_entity_id) if external_entity_id.isdigit() else 364014,
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
            "genres": [g["name"] for g in raw_payload.get("genres", [])],
            "synopsis": raw_payload.get("overview")
        }
