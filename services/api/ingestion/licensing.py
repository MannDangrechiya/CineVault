# CineVault OS — Source Authorization & Licensing Gate Module
# Enforces pre-acquisition licensing checks, authority roles, and prohibited source blocking (DS-01, DEC-ING-PRP-01)

import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger("cinevault.ingestion.licensing")

class SourceAccessStatus(str, Enum):
    PERMITTED = "PERMITTED"
    PERMITTED_SERVER_ONLY = "PERMITTED_SERVER_ONLY"
    RESTRICTED = "RESTRICTED"
    PROHIBITED = "PROHIBITED"

class AuthorityRole(str, Enum):
    PRIMARY_KOREAN = "PRIMARY_KOREAN"
    SECONDARY_TV = "SECONDARY_TV"
    CANDIDATE_GLOBAL = "CANDIDATE_GLOBAL"
    REFERENCE_SPARQL = "REFERENCE_SPARQL"
    UNAUTHORIZED = "UNAUTHORIZED"

class LicensingGateManager:
    """Evaluates provider authorization status prior to any network request or ingestion run."""

    PROVIDER_RULES: Dict[str, Dict[str, Any]] = {
        "KOBIS": {
            "authority_role": AuthorityRole.PRIMARY_KOREAN,
            "access_status": SourceAccessStatus.PERMITTED,
            "requires_api_key": True,
            "scraping_permitted": False,
            "description": "Primary Korean-domain film box office & canonical catalog authority."
        },
        "TVDB": {
            "authority_role": AuthorityRole.SECONDARY_TV,
            "access_status": SourceAccessStatus.PERMITTED,
            "requires_api_key": True,
            "scraping_permitted": False,
            "description": "Secondary TV series & episode structure authority."
        },
        "TMDB": {
            "authority_role": AuthorityRole.CANDIDATE_GLOBAL,
            "access_status": SourceAccessStatus.PERMITTED_SERVER_ONLY,
            "requires_api_key": True,
            "scraping_permitted": False,
            "description": "Candidate global catalog provider (server-side integration only)."
        },
        "WIKIDATA": {
            "authority_role": AuthorityRole.REFERENCE_SPARQL,
            "access_status": SourceAccessStatus.PERMITTED,
            "requires_api_key": False,
            "scraping_permitted": False,
            "description": "Structured reference authority for SPARQL cross-linking."
        },
        "JUSTWATCH": {
            "authority_role": AuthorityRole.UNAUTHORIZED,
            "access_status": SourceAccessStatus.PROHIBITED,
            "requires_api_key": False,
            "scraping_permitted": False,
            "description": "Streaming availability scraping is strictly prohibited."
        },
        "IMDB_DATASETS": {
            "authority_role": AuthorityRole.UNAUTHORIZED,
            "access_status": SourceAccessStatus.PROHIBITED,
            "requires_api_key": False,
            "scraping_permitted": False,
            "description": "Direct IMDb public dataset ingestion is excluded due to commercial licensing terms."
        }
    }

    def verify_source_access(self, provider_name: str, is_scraping_attempt: bool = False) -> Dict[str, Any]:
        """
        Validates source authorization gate.
        Raises PermissionError if source is prohibited or if scraping is attempted.
        """
        provider = provider_name.upper()
        rule = self.PROVIDER_RULES.get(provider)

        if not rule:
            logger.warning(f"Licensing Gate: Unknown provider '{provider_name}' requested. Access DENIED.")
            raise PermissionError(f"Provider '{provider_name}' is not registered in Data Source Registry V1.")

        if is_scraping_attempt:
            logger.error(f"Licensing Gate: Web scraping attempt detected for '{provider}'. Access DENIED.")
            raise PermissionError(f"Web scraping is strictly prohibited for provider '{provider}'.")

        if rule["access_status"] == SourceAccessStatus.PROHIBITED:
            logger.error(f"Licensing Gate: Access to provider '{provider}' is PROHIBITED. {rule['description']}")
            raise PermissionError(f"Access to provider '{provider}' is PROHIBITED by CineVault governance.")

        return {
            "provider_name": provider,
            "authority_role": rule["authority_role"].value,
            "access_status": rule["access_status"].value,
            "requires_api_key": rule["requires_api_key"],
            "gate_passed": True
        }

licensing_gate = LicensingGateManager()
