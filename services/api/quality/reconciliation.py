# CineVault OS — Domain Reconciliation & Promotion Engine
# Resolves cross-source metadata conflicts using domain authority rules (DS-01, DEC-SRC-PRP-01, DEC-SRC-PRP-02)

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .identity_resolution import MatchState

logger = logging.getLogger("cinevault.quality.reconciliation")

class ReconciliationEngine:
    """Applies domain authority rules and handles human curation promotion to CAT-1."""

    AUTHORITY_MATRIX = {
        "KOBIS": {
            "primary_domains": ["KOREAN_FILM", "KOREAN_BOX_OFFICE", "KOREAN_CAST"],
            "rule_id": "RULE-KOREAN-FILM-PRIMARY-KOBIS",
            "weight": 1.00
        },
        "TVDB": {
            "primary_domains": ["TV_SERIES_STRUCTURE", "EPISODE_ORDER", "SEASON_HIERARCHY"],
            "rule_id": "RULE-TVDB-SECONDARY-TV",
            "weight": 0.90
        },
        "TMDB": {
            "primary_domains": ["GLOBAL_SYNOPSIS", "GLOBAL_ARTWORK"],
            "rule_id": "RULE-TMDB-GLOBAL-CANDIDATE",
            "weight": 0.85
        }
    }

    def resolve_attribute_conflict(
        self,
        attribute_name: str,
        observations: List[Dict[str, Any]],
        domain_type: str = "GLOBAL"
    ) -> Dict[str, Any]:
        """
        Resolves conflicting attribute observations based on domain authority weighting.
        Does NOT use blind last-write-wins.
        """
        best_obs = None
        best_weight = -1.0

        for obs in observations:
            provider = obs.get("provider_name", "UNKNOWN")
            val = obs.get("value")
            if val is None:
                continue

            auth = self.AUTHORITY_MATRIX.get(provider, {"weight": 0.50, "rule_id": "RULE-DEFAULT-FALLBACK"})
            weight = auth["weight"]

            # Elevate weight if provider is primary authority for domain
            if domain_type == "KOREAN_FILM" and provider == "KOBIS":
                weight = 1.00

            if weight > best_weight:
                best_weight = weight
                best_obs = {
                    "attribute_name": attribute_name,
                    "winning_value": val,
                    "winning_provider": provider,
                    "applied_rule_id": auth.get("rule_id", "RULE-DEFAULT-FALLBACK"),
                    "confidence_score": weight
                }

        return best_obs or {
            "attribute_name": attribute_name,
            "winning_value": None,
            "winning_provider": "NONE",
            "applied_rule_id": "RULE-NO-OBSERVATION",
            "confidence_score": 0.00
        }

reconciliation_engine = ReconciliationEngine()
