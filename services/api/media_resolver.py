# CineVault OS — Canonical Media & Image URL Normalization Layer
# Enforces single-source-of-truth URL resolution across PostgreSQL, Ingestion, and API responses

from typing import Optional
from urllib.parse import urlparse

from .config import config

TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/w1280"

# R1 hardening pass: this used to hardcode "cdn.cinevault.org" below, which
# only ever matched CineVault's own placeholder domain and never a real
# deployment's actual CDN host. Derived instead from CDN_BASE_URL (config.py),
# which docker-compose.prod.yml already sets from CDN_HOSTNAME — same fix
# pattern as apps/web's next.config.ts / lib/media.ts. Empty in the unlikely
# case CDN_BASE_URL has no host, which just means this upgrade never matches
# (safe no-op, not an error).
_CDN_HOSTNAME = urlparse(config.cdn_base_url).netloc


def normalize_media_url(
    url: Optional[str],
    media_type: str = "poster"
) -> Optional[str]:
    """
    Safely resolves and normalizes media / artwork URLs.
    
    Handles:
    - None or empty string -> None
    - Absolute HTTPS URLs -> preserved
    - Absolute HTTP URLs -> upgraded to HTTPS where appropriate (e.g. image.tmdb.org)
    - Provider-relative paths (e.g. '/7IiTTgloJzvGI1TAYGlC2z2zOZB.jpg' or '7IiTTgloJzvGI1TAYGlC2z2zOZB.jpg') -> resolved against provider base
    - Local asset paths (e.g. '/assets/...' or '/images/...') -> preserved as local paths
    - Whitespace / invalid strings -> safely cleaned or rejected
    """
    if not url:
        return None
    
    clean_url = str(url).strip()
    if not clean_url or clean_url.lower() in ("null", "none", "undefined"):
        return None

    # Disallow fake Unsplash stock photos as canonical artwork
    if "images.unsplash.com" in clean_url.lower():
        return None
    
    # 1. Local Next.js / CineVault public asset paths
    if clean_url.startswith("/assets/") or clean_url.startswith("/images/"):
        return clean_url
    
    # 2. Absolute URLs (http / https)
    if clean_url.startswith("http://") or clean_url.startswith("https://"):
        try:
            parsed = urlparse(clean_url)
            if not parsed.netloc:
                return None
            
            # Upgrade insecure HTTP for known secure CDNs
            if parsed.scheme == "http" and parsed.netloc in ("image.tmdb.org", "m.media-amazon.com", _CDN_HOSTNAME):
                clean_url = "https://" + clean_url[7:]
            return clean_url
        except Exception:
            return None
    
    # 3. Provider-relative paths (e.g., TMDB poster / backdrop paths like '/abc123.jpg')
    # Standard TMDB image filenames are alphanumeric + underscore/hyphen + .jpg / .png / .webp
    path = clean_url if clean_url.startswith("/") else f"/{clean_url}"
    
    base_url = TMDB_BACKDROP_BASE_URL if media_type == "backdrop" else TMDB_POSTER_BASE_URL
    return f"{base_url}{path}"


def resolve_poster_url(url: Optional[str]) -> Optional[str]:
    """Resolves poster artwork URL with w500 default resolution."""
    return normalize_media_url(url, media_type="poster")


def resolve_backdrop_url(url: Optional[str]) -> Optional[str]:
    """Resolves backdrop hero artwork URL with w1280 default resolution."""
    return normalize_media_url(url, media_type="backdrop")
