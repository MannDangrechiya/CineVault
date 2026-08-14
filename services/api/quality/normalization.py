# CineVault OS — Text & Script Normalization Engine
# Implements deterministic text normalization, NFKC Unicode normalization, script handling, and matching keys (Day 5 Data Quality)

import re
import unicodedata
from typing import Dict, Any, Optional

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

def is_transliteration_candidate(orig_title: str, prop_title: str) -> bool:
    """
    Determines if two title strings (e.g. Japanese/Korean original title vs Romanized English)
    could represent the same title based on normalized matching keys.
    """
    key1 = normalize_for_matching(orig_title)
    key2 = normalize_for_matching(prop_title)

    if not key1 or not key2:
        return False

    return key1 == key2 or key1 in key2 or key2 in key1
