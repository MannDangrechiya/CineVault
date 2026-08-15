# CineVault OS — Data Quality Verification Engine
# Multi-layered quality evaluation enforcing 4 validation layers (Schema, Referential, Semantic, Cross-Field),
# Data Quality Status taxonomy, and Confidence evaluation (Day 5 Architecture)

import logging
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger("cinevault.quality.verification")

class QualityStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    IMPORTED = "IMPORTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFLICTING = "CONFLICTING"
    DEPRECATED = "DEPRECATED"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"

class QualityVerificationEngine:
    """Evaluates payload across 4 sequential validation layers and assigns quality status & confidence."""

    def evaluate_provider_confidence(self, provider_name: str, is_official: bool = False) -> ConfidenceLevel:
        """Determines initial confidence level based on source provider rank and metadata authority."""
        prov = (provider_name or "").upper()
        if is_official or prov in ("OFFICIAL_STUDIO", "OFFICIAL_FESTIVAL", "KOBIS"):
            return ConfidenceLevel.HIGH
        elif prov in ("TVDB", "TMDB"):
            return ConfidenceLevel.HIGH
        elif prov in ("ANILIST", "MYANIMELIST", "WIKIDATA"):
            return ConfidenceLevel.MEDIUM
        elif prov in ("UNVERIFIED", "UNKNOWN"):
            return ConfidenceLevel.LOW
        return ConfidenceLevel.MEDIUM

    def verify_normalized_payload(self, normalized_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Executes sequential 4-layer validation checks over a normalized title/entity payload.
        Returns (is_valid, list_of_quality_errors).
        """
        errors: List[str] = []
        entity_type = normalized_data.get("entity_type", "TITLE")

        # ----------------------------------------------------------------------
        # LAYER 1: SCHEMA VALIDATION (Type checks, mandatory fields, enum bounds)
        # ----------------------------------------------------------------------
        if entity_type == "TITLE":
            title_prop = normalized_data.get("canonical_title_proposal") or normalized_data.get("canonical_title")
            if not title_prop or not str(title_prop).strip():
                errors.append("SCHEMA_ERROR: Missing or empty canonical_title_proposal")

            c_type = normalized_data.get("content_type")
            if not c_type:
                errors.append("SCHEMA_ERROR: Missing content_type")
            elif c_type not in ("MOVIE", "TV_SERIES", "ANIME", "DOCUMENTARY", "SHORT_FILM", "SHORT", "SPECIAL"):
                errors.append(f"SCHEMA_ERROR: Invalid content_type classification '{c_type}'")

        # Type validation (e.g. production_year = "abc")
        year_raw = normalized_data.get("production_year")
        if year_raw is not None and not isinstance(year_raw, int):
            errors.append(f"SCHEMA_ERROR: Invalid production_year data type '{type(year_raw).__name__}'. Must be an integer.")

        runtime_raw = normalized_data.get("runtime_minutes")
        if runtime_raw is not None and not isinstance(runtime_raw, int):
            errors.append(f"SCHEMA_ERROR: Invalid runtime_minutes data type '{type(runtime_raw).__name__}'. Must be an integer.")

        # ----------------------------------------------------------------------
        # LAYER 2: REFERENTIAL VALIDATION (FK Integrity & Parent-Child Bounds)
        # ----------------------------------------------------------------------
        if entity_type == "EPISODE":
            season_id = normalized_data.get("season_id")
            season_num = normalized_data.get("season_number")
            if season_id is None and season_num is None:
                errors.append("REFERENTIAL_ERROR: Episode entity missing required parent season reference (season_id or season_number).")

        elif entity_type == "RELEASE":
            edition_id = normalized_data.get("edition_id")
            if not edition_id:
                errors.append("REFERENTIAL_ERROR: Release entity missing required parent edition_id.")

        elif entity_type == "EDITION":
            title_id = normalized_data.get("title_id")
            if not title_id:
                errors.append("REFERENTIAL_ERROR: Edition entity missing required parent title_id.")

        # ----------------------------------------------------------------------
        # LAYER 3: SEMANTIC VALIDATION (Attribute Range Bounds & Logical Values)
        # ----------------------------------------------------------------------
        production_year = normalized_data.get("production_year")
        if isinstance(production_year, int):
            current_year = datetime.now().year
            if production_year < 1888 or production_year > current_year + 5:
                errors.append(f"FIELD_ERROR: Invalid production_year '{production_year}'. Must be between 1888 and {current_year + 5}.")

        runtime = normalized_data.get("runtime_minutes")
        if isinstance(runtime, int):
            if runtime <= 0:
                errors.append(f"FIELD_ERROR: Invalid runtime_minutes '{runtime}'. Must be a positive integer.")
            elif entity_type == "EPISODE" and runtime > 300:
                errors.append(f"SEMANTIC_ERROR: Improbable episode runtime '{runtime}' minutes exceeds 300 minute limit.")
            elif entity_type == "TITLE" and runtime > 900:
                errors.append(f"SEMANTIC_ERROR: Improbable title runtime '{runtime}' minutes exceeds 900 minute limit.")

        # Person birth/death date semantic check
        birth_date = normalized_data.get("birth_date")
        death_date = normalized_data.get("death_date")
        if birth_date and death_date and birth_date > death_date:
            errors.append(f"SEMANTIC_ERROR: Person death_date '{death_date}' precedes birth_date '{birth_date}'.")

        # ----------------------------------------------------------------------
        # LAYER 4: CROSS-FIELD VALIDATION (Inter-attribute Coherence)
        # ----------------------------------------------------------------------
        content_type = normalized_data.get("content_type")
        season_count = normalized_data.get("season_count")
        if content_type == "MOVIE" and season_count is not None and season_count > 0:
            errors.append(f"CROSS_FIELD_ERROR: Content type is MOVIE but season_count is '{season_count}'. Movies cannot contain seasons.")

        if content_type == "TV_SERIES" and normalized_data.get("season_number") is not None and normalized_data.get("season_number") < 0:
            errors.append("CROSS_FIELD_ERROR: TV Series season_number cannot be negative.")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Quality Verification Failed for external_id '{normalized_data.get('external_id')}': {errors}")
        return is_valid, errors

    def determine_quality_status(self, is_valid: bool, has_conflict: bool, confidence: ConfidenceLevel) -> QualityStatus:
        """Assigns controlled Data Quality Status enum based on validation and conflict results."""
        if not is_valid:
            return QualityStatus.NEEDS_REVIEW
        if has_conflict:
            return QualityStatus.CONFLICTING
        if confidence == ConfidenceLevel.HIGH:
            return QualityStatus.VERIFIED
        elif confidence == ConfidenceLevel.MEDIUM:
            return QualityStatus.PARTIALLY_VERIFIED
        return QualityStatus.IMPORTED

    def check_false_match_risk(
        self,
        source_title: str,
        source_year: Optional[int],
        candidate_title: str,
        candidate_year: Optional[int]
    ) -> bool:
        """
        False-match prevention check protecting Title / Edition / Release boundaries (ADR-002).
        Returns True if high risk of false-match (e.g. remake with different release year).
        """
        if not source_title or not candidate_title:
            return False
        if source_title.lower() == candidate_title.lower():
            if source_year and candidate_year and source_year != candidate_year:
                logger.info(f"False-Match Risk Detected: Titles match ('{source_title}') but years differ ({source_year} vs {candidate_year}). Treating as distinct entities.")
                return True
        return False

quality_verifier = QualityVerificationEngine()
