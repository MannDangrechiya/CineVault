# CineVault OS — Multilingual Identity Matching Regression Tests (Day 1-7 remediation, Batch 4)
# Proves the phonetic transliteration tier added to quality/normalization.py
# actually resolves the required real-world cross-script cases, is honest
# about its known Japanese-Kanji limitation, and never auto-merges without
# a corroborating signal (production year / country / runtime).

import unittest

from services.api.quality.normalization import (
    normalize_for_matching,
    normalize_for_phonetic_matching,
    phonetic_similarity,
    is_transliteration_candidate,
)
from services.api.quality.identity_resolution import identity_resolver, MatchState


class TestPhoneticNormalization(unittest.TestCase):
    def test_korean_hangul_matches_its_romanization(self):
        # Parasite: 기생충 (Hangul) vs. Gisaengchung (common Latin romanization)
        self.assertGreaterEqual(phonetic_similarity("기생충", "Gisaengchung"), 0.90)
        self.assertTrue(is_transliteration_candidate("기생충", "Gisaengchung"))

    def test_korean_hangul_does_not_match_a_different_korean_title(self):
        # 기생충 (Parasite) vs 옥자 (Okja) — must NOT be treated as a candidate
        self.assertLess(phonetic_similarity("기생충", "옥자"), 0.5)
        self.assertFalse(is_transliteration_candidate("기생충", "옥자"))

    def test_devanagari_matches_its_romanization(self):
        # Dangal: दंगल (Devanagari) vs. Dangal (Latin)
        self.assertGreaterEqual(phonetic_similarity("दंगल", "Dangal"), 0.75)
        self.assertTrue(is_transliteration_candidate("दंगल", "Dangal"))

    def test_latin_accents_already_handled_by_exact_tier(self):
        # Accented Latin script matches via normalize_for_matching's existing
        # strip_accents step (tier 1) — no transliteration needed.
        self.assertEqual(normalize_for_matching("Amélie"), normalize_for_matching("Amelie"))
        self.assertTrue(is_transliteration_candidate("Amélie", "Amelie"))

    def test_japanese_kanji_is_a_known_untrusted_limitation(self):
        """
        Documents current, honest behavior: unidecode's CJK ideograph table
        produces Mandarin-pinyin-style readings for Japanese Kanji, which is
        frequently wrong (e.g. it will NOT correctly derive "Kimi no Na wa"
        from 君の名は). Rather than silently claiming a fix that doesn't
        work, this test asserts the phonetic tier stays conservative here —
        it must not report high confidence for a transliteration it cannot
        actually get right.
        """
        similarity = phonetic_similarity("君の名は", "Kimi no Na wa")
        self.assertLess(similarity, 0.80)  # below PHONETIC_MATCH_THRESHOLD — correctly not a candidate this way

    def test_japanese_title_still_matches_when_exact_romaji_is_already_stored(self):
        # If the same known-good romaji string is what's actually stored
        # (as our own baseline / a provider's romaji field would do), the
        # exact/substring tier resolves it without needing transliteration.
        self.assertTrue(is_transliteration_candidate("Kimi no Na wa", "Your Name / Kimi no Na wa"))


class TestIdentityResolverMultilingualIntegration(unittest.TestCase):
    """Confirms the phonetic tier is wired into the actual Level 3 identity
    resolution path, and that it never auto-matches without corroboration."""

    def _catalog(self):
        return [{
            "id": "018f6f60-7a00-7000-8000-0000000000aa",
            "display_id": "MOV-PARASITE-2019",
            "canonical_title": "Parasite",
            "original_title": "기생충",
            "production_year": 2019,
            "external_ids": {},
        }]

    def test_cross_script_match_with_year_corroboration_auto_matches(self):
        # A payload arriving with the ROMANIZED Latin title (a genuinely
        # different script than the catalog's stored Hangul original_title)
        # plus the SAME production year should resolve via Level 3's
        # phonetic multilingual check + year corroboration.
        state, match_id, score, rule = identity_resolver.resolve_identity(
            {"canonical_title_proposal": "Gisaengchung", "production_year": 2019},
            self._catalog(),
        )
        self.assertEqual(state, MatchState.MATCH_EXACT)
        self.assertEqual(match_id, "018f6f60-7a00-7000-8000-0000000000aa")

    def test_cross_script_match_without_year_does_not_auto_merge(self):
        # Same cross-script title match, but no production year to
        # corroborate — must NOT silently auto-merge on transliteration
        # similarity alone.
        state, match_id, score, rule = identity_resolver.resolve_identity(
            {"canonical_title_proposal": "Gisaengchung"},
            self._catalog(),
        )
        self.assertNotEqual(state, MatchState.MATCH_EXACT)

    def test_cross_script_match_with_wrong_year_does_not_auto_merge(self):
        state, match_id, score, rule = identity_resolver.resolve_identity(
            {"canonical_title_proposal": "Gisaengchung", "production_year": 1999},
            self._catalog(),
        )
        self.assertNotEqual(state, MatchState.MATCH_EXACT)


if __name__ == "__main__":
    unittest.main()
