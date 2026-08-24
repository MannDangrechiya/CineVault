# CineVault OS — Identity Resolution & Deduplication Engine
# Multi-level identity matching enforcing Level 1-4 signals, Edition boundaries (ADR-002),
# Multilingual title comparison, and External ID collision detection (Day 5 Architecture)

import logging
import re
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple

from .verification import quality_verifier
from .normalization import normalize_for_matching, is_transliteration_candidate

logger = logging.getLogger("cinevault.quality.identity_resolution")

class MatchState(str, Enum):
    MATCH_EXACT = "MATCH_EXACT"
    MATCH_AMBIGUOUS = "MATCH_AMBIGUOUS"
    NO_MATCH = "NO_MATCH"
    MERGE_CANDIDATE = "MERGE_CANDIDATE"
    SPLIT_CANDIDATE = "SPLIT_CANDIDATE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"

class IdentityResolutionEngine:
    """Evaluates multi-level identity signals for canonical entity matching and deduplication."""

    def resolve_identity(
        self,
        normalized_data: Dict[str, Any],
        existing_canonical_titles: List[Dict[str, Any]]
    ) -> Tuple[MatchState, Optional[str], float, str]:
        """
        Evaluates normalized payload against existing canonical catalog entries across 4 matching levels:
        Level 1: Exact External ID
        Level 2: CineVault UUID / display_id
        Level 3: Deterministic multi-signal (title + orig_title + year + country + runtime + director)
        Level 4: Probabilistic matching
        """
        provider_name = normalized_data.get("provider_name", "UNKNOWN").upper()
        external_id = str(normalized_data.get("external_id", ""))
        title_prop = normalized_data.get("canonical_title_proposal") or normalized_data.get("canonical_title") or ""
        orig_title = normalized_data.get("original_title", "")
        year = normalized_data.get("production_year")
        country = normalized_data.get("production_country")
        runtime = normalized_data.get("runtime_minutes")
        director = normalized_data.get("director")
        edition_name = normalized_data.get("edition_name")

        key_prop = normalize_for_matching(title_prop)
        key_orig = normalize_for_matching(orig_title)

        # ----------------------------------------------------------------------
        # COMBINED SCAN: LEVEL 1, LEVEL 2, AND LEVEL 3 MATCHING
        # Single-pass iteration preserves specification priority while eliminating
        # redundant full-catalog traversals.
        # ----------------------------------------------------------------------
        id_matches = []
        target_uuid = str(normalized_data.get("title_id") or normalized_data.get("id") or "")
        target_display_id = normalized_data.get("display_id")
        candidate_matches = []

        for ct in existing_canonical_titles:
            # Level 1: Exact Provider External ID Match
            ext_mappings = ct.get("external_ids", {})
            if ext_mappings.get(provider_name) == external_id or ext_mappings.get(provider_name.lower()) == external_id:
                id_matches.append(ct["id"])

            # Level 2: Canonical Identity / Display ID Match
            if target_uuid and str(ct.get("id")) == target_uuid:
                return (MatchState.MATCH_EXACT, ct["id"], 1.000, "RULE-LEVEL2-CANONICAL-UUID-MATCH")
            if target_display_id and ct.get("display_id") == target_display_id:
                return (MatchState.MATCH_EXACT, ct["id"], 1.000, "RULE-LEVEL2-DISPLAY-ID-MATCH")

            # Level 3: Deterministic Multi-Signal Candidate Match
            c_title = ct.get("canonical_title", "")
            c_orig = ct.get("original_title", "")
            c_year = ct.get("production_year")
            c_country = ct.get("production_country")
            c_runtime = ct.get("runtime_minutes")
            c_director = ct.get("director")

            c_key_title = ct.get("_norm_canonical_title") or normalize_for_matching(c_title)
            c_key_orig = ct.get("_norm_original_title") or (normalize_for_matching(c_orig) if c_orig else "")

            # False-match protection check (ADR-002)
            if quality_verifier.check_false_match_risk(title_prop, year, c_title, c_year):
                continue

            # Exact title key match
            name_exact_match = (key_prop and key_prop == c_key_title) or (key_orig and c_key_orig and key_orig == c_key_orig)

            # Multilingual title comparison candidate check
            multilingual_match = False
            if not name_exact_match and c_orig and (year is not None and c_year is not None and year == c_year):
                if orig_title:
                    multilingual_match = is_transliteration_candidate(orig_title, c_orig)
                if not multilingual_match and title_prop:
                    multilingual_match = is_transliteration_candidate(title_prop, c_orig)

            if name_exact_match or multilingual_match:
                if year is not None and c_year is not None and year == c_year:
                    score = 0.950
                    if edition_name and edition_name.lower() in ("director's cut", "extended cut", "theatrical cut", "uncut"):
                        rule = "RULE-LEVEL3-TITLE-EDITION-MATCH"
                    else:
                        rule = "RULE-LEVEL3-TITLE-YEAR-EXACT-MATCH"
                    candidate_matches.append((ct["id"], score, rule))
                elif name_exact_match and (country and country == c_country or runtime and abs(runtime - (c_runtime or 0)) <= 3):
                    candidate_matches.append((ct["id"], 0.910, "RULE-LEVEL3-MULTI-SIGNAL-MATCH"))

        # Evaluate Level 1 priority
        if len(id_matches) == 1:
            logger.info(f"Identity Resolution Level 1: Exact provider ID match for {provider_name}:{external_id} -> Title '{id_matches[0]}'")
            return (MatchState.MATCH_EXACT, id_matches[0], 1.000, "RULE-LEVEL1-EXACT-EXTERNAL-ID")
        elif len(id_matches) > 1:
            logger.error(f"External ID Collision Detected: Provider ID {provider_name}:{external_id} mapped to multiple titles {id_matches}. Requires review.")
            return (MatchState.REQUIRES_REVIEW, None, 0.500, "RULE-LEVEL1-EXTERNAL-ID-COLLISION")

        # Evaluate Level 3 priority
        if len(candidate_matches) == 1:
            matched_id, score, rule = candidate_matches[0]
            return (MatchState.MATCH_EXACT, matched_id, score, rule)
        elif len(candidate_matches) > 1:
            logger.warning(f"Identity Resolution Level 3: Multiple candidates matched for '{title_prop}' ({year}). Result: MATCH_AMBIGUOUS")
            return (MatchState.MATCH_AMBIGUOUS, None, 0.650, "RULE-LEVEL3-AMBIGUOUS-MULTIPLE-MATCHES")

        # ----------------------------------------------------------------------
        # LEVEL 4: PROBABILISTIC CANDIDATE MATCHING
        # ----------------------------------------------------------------------
        probabilistic_candidates = []
        STOP_WORDS = {
            "the", "a", "an", "of", "and", "in", "to", "catalog", "entry", "movie", "series", "season", "episode",
            "director", "directors", "cut", "special", "edition", "extended", "remastered", "unrated", "theatrical", "version"
        }
        words_p = set(key_prop.split()) if key_prop else set()
        words_p_filtered = words_p - STOP_WORDS
        if words_p_filtered:
            len_p = len(words_p_filtered)
            digits_p = set(re.findall(r"\d+", key_prop))
            for ct in existing_canonical_titles:
                c_title = ct.get("canonical_title", "")
                c_year = ct.get("production_year")
                c_key_title = ct.get("_norm_canonical_title") or normalize_for_matching(c_title)

                if not c_key_title:
                    continue

                # Years must not conflict if both are known
                if year and c_year and year != c_year:
                    continue

                # Digits/numbers in title must not conflict (e.g. 'Entry 1' vs 'Entry 2')
                digits_c = ct.get("_digits_title")
                if digits_c is None:
                    digits_c = set(re.findall(r"\d+", c_key_title))
                    ct["_digits_title"] = digits_c
                if digits_p and digits_c and digits_p != digits_c:
                    continue

                words_c = ct.get("_words_title_filtered")
                if words_c is None:
                    raw_words_c = ct.get("_words_title") or set(c_key_title.split())
                    words_c = raw_words_c - STOP_WORDS
                    ct["_words_title_filtered"] = words_c

                if words_c:
                    common_words = words_p_filtered & words_c
                    if common_words:
                        token_ratio = len(common_words) / max(len_p, len(words_c))
                        if token_ratio >= 0.80:
                            sim_score = 0.70 + (0.15 * token_ratio)
                            if year and c_year and year == c_year:
                                sim_score += 0.10
                            if sim_score >= 0.70:
                                probabilistic_candidates.append((ct["id"], min(sim_score, 0.890)))

            if probabilistic_candidates:
                probabilistic_candidates.sort(key=lambda x: x[1], reverse=True)
                best_id, best_score = probabilistic_candidates[0]
                if best_score >= 0.70:
                    logger.info(f"Identity Resolution Level 4: Probabilistic match candidate for '{title_prop}' -> Title '{best_id}' (score: {best_score:.3f})")
                    return (MatchState.REQUIRES_REVIEW, best_id, best_score, "RULE-LEVEL4-PROBABILISTIC-REVIEW-CANDIDATE")



        # ----------------------------------------------------------------------
        # NO MATCH FOUND -> NO_MATCH
        # ----------------------------------------------------------------------
        return (MatchState.NO_MATCH, None, 0.000, "RULE-NO-EXISTING-CANONICAL-MATCH")

identity_resolver = IdentityResolutionEngine()
