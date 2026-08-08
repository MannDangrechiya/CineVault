# CineVault OS — Identity Resolution & Match Engine
# Resolves external observations against canonical catalog entities adhering to approved match taxonomy (ADR-001, DS-01)

import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple

from .verification import quality_verifier

logger = logging.getLogger("cinevault.quality.identity_resolution")

class MatchState(str, Enum):
    MATCH_EXACT = "MATCH_EXACT"
    MATCH_AMBIGUOUS = "MATCH_AMBIGUOUS"
    NO_MATCH = "NO_MATCH"
    MERGE_CANDIDATE = "MERGE_CANDIDATE"
    SPLIT_CANDIDATE = "SPLIT_CANDIDATE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"

class IdentityResolutionEngine:
    """Evaluates match signals and determines identity resolution match state."""

    def resolve_identity(
        self,
        normalized_data: Dict[str, Any],
        existing_canonical_titles: List[Dict[str, Any]]
    ) -> Tuple[MatchState, Optional[str], float, str]:
        """
        Evaluates normalized payload against existing canonical catalog entries.
        Returns (match_state, matched_title_id, confidence_score, applied_rule_id).
        """
        provider_name = normalized_data.get("provider_name", "UNKNOWN")
        external_id = normalized_data.get("external_id")
        title_prop = normalized_data.get("canonical_title_proposal", "")
        orig_title = normalized_data.get("original_title", "")
        year = normalized_data.get("production_year")

        # 1. Match Rule 1: Exact Provider External ID Match -> MATCH_EXACT
        for ct in existing_canonical_titles:
            ext_mappings = ct.get("external_ids", {})
            if ext_mappings.get(provider_name) == external_id:
                logger.info(f"Identity Resolution: Exact provider ID match for {provider_name}:{external_id} -> Title '{ct['id']}'")
                return (MatchState.MATCH_EXACT, ct["id"], 1.000, "RULE-EXACT-PROVIDER-EXTERNAL-ID")

        # 2. Match Rule 2: Title Name + Production Year Match
        candidate_matches = []
        for ct in existing_canonical_titles:
            c_title = ct.get("canonical_title", "")
            c_orig = ct.get("original_title", "")
            c_year = ct.get("production_year")

            name_match = (title_prop.lower() == c_title.lower()) or (orig_title and orig_title == c_orig)

            if name_match:
                if year == c_year:
                    candidate_matches.append((ct["id"], 0.950, "RULE-TITLE-YEAR-EXACT-MATCH"))
                else:
                    # False-match protection: same title, different year (remake or adaptation) -> NO_MATCH
                    if quality_verifier.check_false_match_risk(title_prop, year, c_title, c_year):
                        continue

        if len(candidate_matches) == 1:
            matched_id, score, rule = candidate_matches[0]
            return (MatchState.MATCH_EXACT, matched_id, score, rule)
        elif len(candidate_matches) > 1:
            logger.warning(f"Identity Resolution: Multiple candidates matched for '{title_prop}' ({year}). Result: MATCH_AMBIGUOUS")
            return (MatchState.MATCH_AMBIGUOUS, None, 0.650, "RULE-AMBIGUOUS-MULTIPLE-MATCHES")

        # 3. No match found -> NO_MATCH
        return (MatchState.NO_MATCH, None, 0.000, "RULE-NO-EXISTING-CANONICAL-MATCH")

identity_resolver = IdentityResolutionEngine()
