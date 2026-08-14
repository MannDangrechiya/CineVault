# CineVault OS — Source Authorization & Licensing Gate Module
# Enforces pre-acquisition licensing checks, authority roles, and prohibited source blocking (DS-01, DEC-ING-PRP-01, Day 6 Registry)

import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger("cinevault.ingestion.licensing")

class ActivationStatus(str, Enum):
    RESEARCH = "RESEARCH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"

class SourceAccessStatus(str, Enum):
    PERMITTED = "PERMITTED"
    PERMITTED_SERVER_ONLY = "PERMITTED_SERVER_ONLY"
    RESTRICTED = "RESTRICTED"
    PROHIBITED = "PROHIBITED"
    NEEDS_REVIEW = "NEEDS_REVIEW"

class AuthorityRole(str, Enum):
    PRIMARY_KOREAN = "PRIMARY_KOREAN"
    SECONDARY_TV = "SECONDARY_TV"
    CANDIDATE_GLOBAL = "CANDIDATE_GLOBAL"
    ANIME_SPECIALIST = "ANIME_SPECIALIST"
    REFERENCE_SPARQL = "REFERENCE_SPARQL"
    OFFICIAL_DISTRIBUTOR = "OFFICIAL_DISTRIBUTOR"
    UNAUTHORIZED = "UNAUTHORIZED"

class LicensingGateManager:
    """Evaluates provider authorization status prior to any network request or ingestion run."""

    PROVIDER_RULES: Dict[str, Dict[str, Any]] = {
        "KOBIS": {
            "provider": "KOBIS",
            "provider_name": "KOBIS",
            "dataset_api": "KOBIS OpenAPI REST",
            "source_type": "OFFICIAL_BOX_OFFICE",
            "official_url": "http://www.kobis.or.kr/",
            "license": "Public Data Open License (Type 1)",
            "attribution_requirement": "Source attribution required (KOBIS)",
            "commercial_use": "PERMITTED",
            "commercial_use_status": "PERMITTED",
            "redistribution": "PERMITTED_WITH_ATTRIBUTION",
            "redistribution_restrictions": "Commercial redistribution permitted with attribution",
            "rate_limit": "300 req/min",
            "rate_limit_per_min": 300,
            "update_frequency": "DAILY",
            "authentication_requirements": "API_KEY",
            "regions": ["KR"],
            "available_fields": ["title", "original_title", "directors", "cast", "release_year", "genres"],
            "reliability": 0.98,
            "reliability_score": 0.98,
            "last_reviewed": "2026-08-01",
            "activation_status": ActivationStatus.ACTIVE,
            "authority_role": AuthorityRole.PRIMARY_KOREAN,
            "access_status": SourceAccessStatus.PERMITTED,
            "requires_api_key": True,
            "scraping_permitted": False,
            "description": "Primary Korean-domain film box office & canonical catalog authority."
        },
        "TVDB": {
            "provider": "TVDB",
            "provider_name": "TVDB",
            "dataset_api": "TVDB API v4 REST",
            "source_type": "COMMERCIAL_METADATA_API",
            "official_url": "https://thetvdb.com/",
            "license": "TVDB API v4 Commercial License",
            "attribution_requirement": "Attribution required",
            "commercial_use": "LICENSED",
            "commercial_use_status": "LICENSED",
            "redistribution": "REQUIRES_SUBSCRIPTION",
            "redistribution_restrictions": "Requires paid API key subscription",
            "rate_limit": "1200 req/min",
            "rate_limit_per_min": 1200,
            "update_frequency": "HOURLY",
            "authentication_requirements": "BEARER_TOKEN",
            "regions": ["GLOBAL"],
            "available_fields": ["title", "seasons", "episodes", "overview", "genres", "release_year"],
            "reliability": 0.92,
            "reliability_score": 0.92,
            "last_reviewed": "2026-08-01",
            "activation_status": ActivationStatus.APPROVED,
            "authority_role": AuthorityRole.SECONDARY_TV,
            "access_status": SourceAccessStatus.PERMITTED,
            "requires_api_key": True,
            "scraping_permitted": False,
            "description": "Secondary TV series & episode structure authority."
        },
        "TMDB": {
            "provider": "TMDB",
            "provider_name": "TMDB",
            "dataset_api": "TMDb API v3 REST",
            "source_type": "GLOBAL_COMMUNITY_METADATA",
            "official_url": "https://www.themoviedb.org/",
            "license": "TMDb API Terms of Use",
            "attribution_requirement": "TMDb logo & attribution mandatory",
            "commercial_use": "SERVER_SIDE_ONLY",
            "commercial_use_status": "PERMITTED_SERVER_ONLY",
            "redistribution": "RESTRICTED_NO_BULK",
            "redistribution_restrictions": "Server-side integration only. No raw bulk redistribution.",
            "rate_limit": "2400 req/min",
            "rate_limit_per_min": 2400,
            "update_frequency": "REALTIME",
            "authentication_requirements": "API_KEY",
            "regions": ["GLOBAL"],
            "available_fields": ["title", "overview", "runtime", "release_date", "genres", "credits"],
            "reliability": 0.90,
            "reliability_score": 0.90,
            "last_reviewed": "2026-08-01",
            "activation_status": ActivationStatus.ACTIVE,
            "authority_role": AuthorityRole.CANDIDATE_GLOBAL,
            "access_status": SourceAccessStatus.PERMITTED_SERVER_ONLY,
            "requires_api_key": True,
            "scraping_permitted": False,
            "description": "Candidate global catalog provider (server-side integration only)."
        },
        "ANILIST": {
            "provider": "ANILIST",
            "provider_name": "ANILIST",
            "dataset_api": "AniList GraphQL API",
            "source_type": "GRAPHQL_COMMUNITY_API",
            "official_url": "https://anilist.co/",
            "license": "MIT / Community API",
            "attribution_requirement": "AniList API attribution recommended",
            "commercial_use": "PERMITTED",
            "commercial_use_status": "PERMITTED",
            "redistribution": "RESPECT_RATE_LIMITS",
            "redistribution_restrictions": "Respect GraphQL rate limits",
            "rate_limit": "90 req/min",
            "rate_limit_per_min": 90,
            "update_frequency": "HOURLY",
            "authentication_requirements": "NONE",
            "regions": ["GLOBAL", "JP"],
            "available_fields": ["title_romaji", "title_english", "title_native", "format", "episodes", "genres"],
            "reliability": 0.94,
            "reliability_score": 0.94,
            "last_reviewed": "2026-08-05",
            "activation_status": ActivationStatus.APPROVED,
            "authority_role": AuthorityRole.ANIME_SPECIALIST,
            "access_status": SourceAccessStatus.PERMITTED,
            "requires_api_key": False,
            "scraping_permitted": False,
            "description": "Primary anime & manga domain metadata authority via GraphQL."
        },
        "MYANIMELIST": {
            "provider": "MYANIMELIST",
            "provider_name": "MYANIMELIST",
            "dataset_api": "MAL REST API v2",
            "source_type": "COMMERCIAL_REST_API",
            "official_url": "https://myanimelist.net/",
            "license": "MAL API v2 Terms",
            "attribution_requirement": "MAL API attribution required",
            "commercial_use": "RESTRICTED",
            "commercial_use_status": "RESTRICTED",
            "redistribution": "MANDATORY_CLIENT_ID",
            "redistribution_restrictions": "Client ID authentication mandatory",
            "rate_limit": "180 req/min",
            "rate_limit_per_min": 180,
            "update_frequency": "DAILY",
            "authentication_requirements": "CLIENT_ID",
            "regions": ["GLOBAL", "JP"],
            "available_fields": ["title", "synopsis", "mean_rating", "rank", "media_type", "episodes"],
            "reliability": 0.91,
            "reliability_score": 0.91,
            "last_reviewed": "2026-08-05",
            "activation_status": ActivationStatus.APPROVED,
            "authority_role": AuthorityRole.ANIME_SPECIALIST,
            "access_status": SourceAccessStatus.PERMITTED,
            "requires_api_key": True,
            "scraping_permitted": False,
            "description": "Secondary anime domain catalog & community ranking provider."
        },
        "WIKIDATA": {
            "provider": "WIKIDATA",
            "provider_name": "WIKIDATA",
            "dataset_api": "Wikidata SPARQL / REST API",
            "source_type": "OPEN_SPARQL_GRAPH",
            "official_url": "https://www.wikidata.org/",
            "license": "CC0 1.0 Public Domain",
            "attribution_requirement": "None (Public Domain)",
            "commercial_use": "PERMITTED",
            "commercial_use_status": "PERMITTED",
            "redistribution": "PERMITTED_UNRESTRICTED",
            "redistribution_restrictions": "None",
            "rate_limit": "600 req/min",
            "rate_limit_per_min": 600,
            "update_frequency": "REALTIME",
            "authentication_requirements": "NONE",
            "regions": ["GLOBAL"],
            "available_fields": ["qid", "label", "imdb_id", "tmdb_id", "country_of_origin", "inception"],
            "reliability": 0.88,
            "reliability_score": 0.88,
            "last_reviewed": "2026-08-01",
            "activation_status": ActivationStatus.ACTIVE,
            "authority_role": AuthorityRole.REFERENCE_SPARQL,
            "access_status": SourceAccessStatus.PERMITTED,
            "requires_api_key": False,
            "scraping_permitted": False,
            "description": "Structured reference authority for SPARQL cross-linking."
        },
        "OFFICIAL_STUDIO": {
            "provider": "OFFICIAL_STUDIO",
            "provider_name": "OFFICIAL_STUDIO",
            "dataset_api": "Studio Press Direct Feed",
            "source_type": "OFFICIAL_DISTRIBUTOR_PRESS",
            "official_url": "https://cinevault.internal/official-sources",
            "license": "Proprietary Direct License",
            "attribution_requirement": "Studio copyright notice",
            "commercial_use": "PERMITTED",
            "commercial_use_status": "PERMITTED",
            "redistribution": "DIRECT_PRESS_AGREEMENT",
            "redistribution_restrictions": "Direct studio press agreement",
            "rate_limit": "1000 req/min",
            "rate_limit_per_min": 1000,
            "update_frequency": "AD_HOC",
            "authentication_requirements": "INTERNAL_AUTH",
            "regions": ["GLOBAL"],
            "available_fields": ["canonical_title", "original_title", "runtime", "credits", "release_date"],
            "reliability": 1.00,
            "reliability_score": 1.00,
            "last_reviewed": "2026-08-10",
            "activation_status": ActivationStatus.APPROVED,
            "authority_role": AuthorityRole.OFFICIAL_DISTRIBUTOR,
            "access_status": SourceAccessStatus.PERMITTED,
            "requires_api_key": True,
            "scraping_permitted": False,
            "description": "Official studio press kit & direct distributor metadata feeds."
        },
        "JUSTWATCH": {
            "provider": "JUSTWATCH",
            "provider_name": "JUSTWATCH",
            "dataset_api": "Public Web Scraping (Unauthorized)",
            "source_type": "STREAMING_AVAILABILITY_SCRAPER",
            "official_url": "https://www.justwatch.com/",
            "license": "UNAUTHORIZED_SCRAPING",
            "attribution_requirement": "N/A",
            "commercial_use": "PROHIBITED",
            "commercial_use_status": "PROHIBITED",
            "redistribution": "STRICTLY_FORBIDDEN",
            "redistribution_restrictions": "Web scraping strictly forbidden",
            "rate_limit": "0 req/min",
            "rate_limit_per_min": 0,
            "update_frequency": "NEVER",
            "authentication_requirements": "NONE",
            "regions": ["GLOBAL"],
            "available_fields": [],
            "reliability": 0.00,
            "reliability_score": 0.00,
            "last_reviewed": "2026-08-01",
            "activation_status": ActivationStatus.SUSPENDED,
            "authority_role": AuthorityRole.UNAUTHORIZED,
            "access_status": SourceAccessStatus.PROHIBITED,
            "requires_api_key": False,
            "scraping_permitted": False,
            "description": "Streaming availability scraping is strictly prohibited."
        },
        "IMDB_DATASETS": {
            "provider": "IMDB_DATASETS",
            "provider_name": "IMDB_DATASETS",
            "dataset_api": "IMDb Non-Commercial TSV Dumps",
            "source_type": "PUBLIC_TSV_DATASET",
            "official_url": "https://developer.imdb.com/non-commercial-datasets/",
            "license": "IMDb Non-Commercial Dataset License",
            "attribution_requirement": "IMDb attribution required",
            "commercial_use": "NON_COMMERCIAL_ONLY",
            "commercial_use_status": "NON_COMMERCIAL_ONLY",
            "redistribution": "COMMERCIAL_REDISTRIBUTION_PROHIBITED",
            "redistribution_restrictions": "Non-commercial evaluation only. Direct commercial redistribution prohibited.",
            "rate_limit": "60 req/min",
            "rate_limit_per_min": 60,
            "update_frequency": "DAILY",
            "authentication_requirements": "NONE",
            "regions": ["GLOBAL"],
            "available_fields": ["tconst", "primaryTitle", "originalTitle", "startYear", "runtimeMinutes", "genres"],
            "reliability": 0.95,
            "reliability_score": 0.95,
            "last_reviewed": "2026-08-01",
            "activation_status": ActivationStatus.RETIRED,
            "authority_role": AuthorityRole.UNAUTHORIZED,
            "access_status": SourceAccessStatus.PROHIBITED,
            "requires_api_key": False,
            "scraping_permitted": False,
            "description": "Direct IMDb public dataset ingestion is excluded due to commercial licensing terms."
        },
        "UNKNOWN_SOURCE": {
            "provider": "UNKNOWN_SOURCE",
            "provider_name": "UNKNOWN_SOURCE",
            "dataset_api": "Unverified Third Party Endpoint",
            "source_type": "UNVERIFIED_THIRD_PARTY",
            "official_url": "UNKNOWN",
            "license": "UNKNOWN",
            "attribution_requirement": "NEEDS_REVIEW",
            "commercial_use": "NEEDS_REVIEW",
            "commercial_use_status": "NEEDS_REVIEW",
            "redistribution": "UNVERIFIED",
            "redistribution_restrictions": "Unverified licensing status",
            "rate_limit": "0 req/min",
            "rate_limit_per_min": 0,
            "update_frequency": "NEVER",
            "authentication_requirements": "UNKNOWN",
            "regions": [],
            "available_fields": [],
            "reliability": 0.50,
            "reliability_score": 0.50,
            "last_reviewed": "2026-08-13",
            "activation_status": ActivationStatus.REVIEW_REQUIRED,
            "authority_role": AuthorityRole.UNAUTHORIZED,
            "access_status": SourceAccessStatus.NEEDS_REVIEW,
            "requires_api_key": True,
            "scraping_permitted": False,
            "description": "Unverified external provider requiring legal and licensing review."
        }
    }

    def verify_source_access(self, provider_name: str, is_scraping_attempt: bool = False) -> Dict[str, Any]:
        """
        Validates source authorization gate.
        Raises PermissionError if source is prohibited, review required, or if scraping is attempted.
        """
        provider = provider_name.upper()
        rule = self.PROVIDER_RULES.get(provider)

        if not rule:
            logger.warning(f"Licensing Gate: Unknown provider '{provider_name}' requested. Access DENIED.")
            raise PermissionError(f"Provider '{provider_name}' is not registered in Data Source Registry V1.")

        if is_scraping_attempt or not rule.get("scraping_permitted", False):
            if is_scraping_attempt:
                logger.error(f"Licensing Gate: Web scraping attempt detected for '{provider}'. Access DENIED.")
                raise PermissionError(f"Web scraping is strictly prohibited for provider '{provider}'.")

        if rule["access_status"] in (SourceAccessStatus.PROHIBITED, SourceAccessStatus.NEEDS_REVIEW):
            logger.error(f"Licensing Gate: Access to provider '{provider}' is {rule['access_status']}. {rule['description']}")
            raise PermissionError(f"Access to provider '{provider}' is blocked ({rule['access_status']}) by CineVault governance.")

        if rule.get("activation_status") in (ActivationStatus.REVIEW_REQUIRED, ActivationStatus.SUSPENDED, ActivationStatus.RETIRED):
            logger.error(f"Licensing Gate: Activation status for provider '{provider}' is {rule['activation_status']}.")
            raise PermissionError(f"Provider '{provider}' activation status is {rule['activation_status']}. Ingestion blocked.")

        return {
            "provider_name": provider,
            "authority_role": rule["authority_role"].value if isinstance(rule["authority_role"], Enum) else rule["authority_role"],
            "access_status": rule["access_status"].value if isinstance(rule["access_status"], Enum) else rule["access_status"],
            "activation_status": rule["activation_status"].value if isinstance(rule["activation_status"], Enum) else rule["activation_status"],
            "requires_api_key": rule["requires_api_key"],
            "rate_limit_per_min": rule.get("rate_limit_per_min", 60),
            "gate_passed": True
        }

    def get_source_registry(self) -> Dict[str, Dict[str, Any]]:
        """Returns the full data source registry metadata dict with 16 canonical attributes."""
        return {
            k: {
                **v,
                "authority_role": v["authority_role"].value if isinstance(v["authority_role"], Enum) else v["authority_role"],
                "access_status": v["access_status"].value if isinstance(v["access_status"], Enum) else v["access_status"],
                "activation_status": v["activation_status"].value if isinstance(v["activation_status"], Enum) else v["activation_status"],
            }
            for k, v in self.PROVIDER_RULES.items()
        }

licensing_gate = LicensingGateManager()
