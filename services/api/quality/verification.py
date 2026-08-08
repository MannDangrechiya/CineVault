# CineVault OS — Data Quality Verification Engine
# Multi-layered quality evaluation enforcing structural validity, field bounds, and false-match prevention (ADR-001, ADR-002)

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("cinevault.quality.verification")

class QualityVerificationEngine:
    """Evaluates payload, schema, field, and entity-level quality dimensions."""

    def verify_normalized_payload(self, normalized_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Runs sequential quality layer checks over a normalized title payload.
        Returns (is_valid, list_of_quality_errors).
        """
        errors: List[str] = []

        # Layer 3: Schema Quality (Mandatory Fields)
        if not normalized_data.get("canonical_title_proposal"):
            errors.append("SCHEMA_ERROR: Missing canonical_title_proposal")
        if not normalized_data.get("content_type"):
            errors.append("SCHEMA_ERROR: Missing content_type")

        # Layer 4: Field Quality (Bounds & Formats)
        production_year = normalized_data.get("production_year")
        if production_year is not None:
            if not isinstance(production_year, int) or production_year < 1888 or production_year > 2100:
                errors.append(f"FIELD_ERROR: Invalid production_year '{production_year}'. Must be between 1888 and 2100.")

        runtime = normalized_data.get("runtime_minutes")
        if runtime is not None:
            if not isinstance(runtime, int) or runtime <= 0:
                errors.append(f"FIELD_ERROR: Invalid runtime_minutes '{runtime}'. Must be a positive integer.")

        # Layer 5: Entity Quality (Logical Coherence)
        content_type = normalized_data.get("content_type")
        if content_type not in ("MOVIE", "TV_SERIES", "ANIME", "SHORT", "SPECIAL"):
            errors.append(f"ENTITY_ERROR: Invalid content_type classification '{content_type}'.")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Quality Verification Failed for {normalized_data.get('external_id')}: {errors}")
        return is_valid, errors

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
        if source_title.lower() == candidate_title.lower():
            if source_year and candidate_year and source_year != candidate_year:
                logger.info(f"False-Match Risk Detected: Titles match ('{source_title}') but years differ ({source_year} vs {candidate_year}). Treating as distinct entities.")
                return True
        return False

quality_verifier = QualityVerificationEngine()
