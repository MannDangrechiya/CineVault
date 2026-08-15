# CineVault OS — Text & Script Normalization Engine
# Implements deterministic text normalization, NFKC Unicode normalization, script handling, and matching keys (Day 5 Data Quality)

import re
import unicodedata
import difflib
from typing import Dict, Any, Optional

from unidecode import unidecode as _unidecode

# Below this ratio, a cross-script phonetic comparison is not trusted as a
# transliteration candidate at all. Calibrated against real title pairs:
# Korean Hangul <-> its common Latin romanization scores ~0.95 (e.g.
# "기생충" vs "Gisaengchung"); two DIFFERENT Korean titles score ~0.2-0.3;
# Devanagari <-> Latin romanization scores ~0.70-0.80 (unidecode drops
# implicit vowels in this script, so fidelity is weaker); Japanese Kanji
# scores low (~0.45) because unidecode's CJK ideograph table produces
# Mandarin-pinyin-style readings that are frequently wrong for Japanese
# on'yomi/kun'yomi — see normalize_for_phonetic_matching's docstring.
PHONETIC_MATCH_THRESHOLD = 0.80

def normalize_title_text(text: Optional[str]) -> str:
    """
    Cleans title string with NFKC Unicode normalization and whitespace trimming.
    NEVER mutates or destroys the original stored text in payloads.
    """
    if not text:
        return ""
    # 1. Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", str(text))
    # 2. Collapse whitespace & trim
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

def strip_accents(text: str) -> str:
    """Decomposes Unicode characters and removes diacritic accent marks."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

def normalize_for_matching(text: Optional[str]) -> str:
    """
    Generates a normalized comparison key for identity matching & duplicate detection.
    Strips punctuation, diacritics, and leading articles ('the', 'a', 'an').
    """
    if not text:
        return ""

    # Base NFKC normalization
    base = normalize_title_text(text).lower()

    # Strip diacritics
    base = strip_accents(base)

    # Remove leading articles for matching
    for article in ["the ", "a ", "an "]:
        if base.startswith(article):
            base = base[len(article):]
            break

    # Strip non-alphanumeric characters except spaces
    cleaned = re.sub(r"[^\w\s]", "", base)

    # Collapse remaining whitespace
    return re.sub(r"\s+", " ", cleaned).strip()

def normalize_for_phonetic_matching(text: Optional[str]) -> str:
    """
    Deterministic, offline, script-independent comparison key. Transliterates
    non-Latin scripts to an ASCII approximation via unidecode (no network
    calls, no paid API — pure Python, bundled Unicode tables), then applies
    the same cleanup as normalize_for_matching.

    KNOWN LIMITATION: unidecode uses one generic CJK ideograph table that
    approximates Mandarin-style readings for Han characters. This is
    frequently WRONG for Japanese Kanji, whose on'yomi/kun'yomi readings
    often differ entirely from Mandarin pinyin (e.g. 君の名は "Kimi no Na
    wa" transliterates to something like "jun no ming ha", nowhere close).
    Correctly resolving Japanese Kanji readings requires dictionary-based
    morphological analysis (e.g. MeCab+IPADIC) — genuinely out of scope for
    a lightweight, dependency-light matcher. Do not trust this function for
    Japanese/Chinese Han-character comparisons; it is safe to rely on for
    Korean Hangul, Devanagari, Cyrillic, and other alphabetic/syllabic
    scripts, where unidecode's approximation is a reasonable phonetic guide
    (with weaker fidelity for Devanagari specifically, since unidecode drops
    some implicit vowels in that script).
    """
    if not text:
        return ""
    ascii_approx = _unidecode(normalize_title_text(text))
    return normalize_for_matching(ascii_approx)


def phonetic_similarity(text_a: Optional[str], text_b: Optional[str]) -> float:
    """
    Returns a 0.0-1.0 similarity ratio between the phonetic (transliterated)
    comparison keys of two title strings, via stdlib difflib. Transliteration
    is inherently approximate, so this is a similarity score, not an exact
    equality check — see normalize_for_phonetic_matching for what it is and
    is not reliable for.
    """
    key_a = normalize_for_phonetic_matching(text_a)
    key_b = normalize_for_phonetic_matching(text_b)
    if not key_a or not key_b:
        return 0.0
    return difflib.SequenceMatcher(None, key_a, key_b).ratio()


def is_transliteration_candidate(orig_title: str, prop_title: str) -> bool:
    """
    Determines if two title strings (e.g. Korean/Devanagari original title
    vs. a Latin-script proposal) could represent the same title.

    Two tiers:
      1. Exact/substring match on the script-preserving normalized key —
         handles same-script variants (e.g. "The Godfather" vs "Godfather").
      2. Phonetic similarity >= PHONETIC_MATCH_THRESHOLD on the
         transliterated key — handles cross-script romanization variants
         (e.g. Korean Hangul vs. its common Latin romanization).

    This is a CANDIDATE signal only. Callers (see
    quality/identity_resolution.py Level 3) must still require a
    corroborating signal — production year, country, or runtime — before
    treating it as an automatic match. A transliteration candidate is never
    sufficient on its own to auto-merge two titles.
    """
    key1 = normalize_for_matching(orig_title)
    key2 = normalize_for_matching(prop_title)

    if key1 and key2 and (key1 == key2 or key1 in key2 or key2 in key1):
        return True

    return phonetic_similarity(orig_title, prop_title) >= PHONETIC_MATCH_THRESHOLD
