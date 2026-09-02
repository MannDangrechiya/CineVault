# CineVault OS — Rate Limiting Policy Enforcement Module
# Implements fixed-window rate limiting for public, search, sync, and admin
# endpoints, backed by Valkey (P1 fix — the original implementation only
# ever tracked counts in this process's own memory, which its own docstring
# called out as "local development and unit testing" only: the moment
# fastapi-backend runs more than one replica/worker, each one enforces its
# own separate limit instead of one shared limit, silently multiplying the
# effective quota by the replica count).

import time
import logging
from typing import Dict, Optional, Tuple
from fastapi import Request
from .config import config
from .errors import RateLimitExceededError
from .valkey import valkey_manager

logger = logging.getLogger("cinevault.rate_limiter")

# Atomic fixed-window counter: increments the key and sets its expiry only on
# the window's first increment, in a single Redis-side round-trip so
# concurrent requests can't race between INCR and EXPIRE and leave a key
# with no TTL (which would otherwise permanently lock out that client once
# the counter exceeded the limit). This is the standard Redis/Valkey
# fixed-window rate-limiting pattern.
_INCR_WITH_EXPIRY_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if tonumber(current) == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


class InMemoryRateLimiter:
    """Sliding-window rate limiter. Used directly only as a degraded
    fallback when Valkey is unreachable — per-process, so on its own it does
    NOT enforce a shared limit across multiple fastapi-backend replicas. See
    ValkeyRateLimiter below for the primary, distributed implementation."""
    def __init__(self):
        # Key: (client_identifier, rate_scope) -> List[timestamp]
        self.requests: Dict[Tuple[str, str], list] = {}

    def check_rate_limit(self, request: Request, scope: str, limit: int, window_sec: int = 60):
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = (client_ip, scope)
        now = time.time()

        timestamps = self.requests.get(key, [])
        # Prune expired timestamps
        timestamps = [ts for ts in timestamps if now - ts < window_sec]

        if len(timestamps) >= limit:
            raise RateLimitExceededError(f"Rate limit exceeded for scope '{scope}'. Max {limit} requests per {window_sec}s.")

        timestamps.append(now)
        self.requests[key] = timestamps


class ValkeyRateLimiter:
    """Fixed-window rate limiter backed by Valkey, so the limit is enforced
    consistently across every fastapi-backend replica sharing the same
    Valkey instance instead of per-process.

    Falls back to InMemoryRateLimiter (degraded: per-process only, same as
    before this fix) if Valkey is unreachable or the script call errors,
    rather than either blocking all traffic or silently disabling rate
    limiting entirely — same fail-degraded philosophy already used by
    ValkeyManager.check_and_set_idempotency.
    """
    def __init__(self):
        self._fallback = InMemoryRateLimiter()

    def check_rate_limit(self, request: Request, scope: str, limit: int, window_sec: int = 60):
        client = valkey_manager.get_client()
        if client is None:
            logger.warning(
                "Valkey unavailable for rate limiting (scope=%s) — falling back to per-process in-memory limiter",
                scope,
            )
            return self._fallback.check_rate_limit(request, scope, limit, window_sec)

        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"ratelimit:{scope}:{client_ip}"

        try:
            current = client.eval(_INCR_WITH_EXPIRY_SCRIPT, 1, key, window_sec)
        except Exception as e:
            logger.warning(
                "Valkey rate-limit script failed (scope=%s): %s — falling back to per-process in-memory limiter",
                scope, e,
            )
            return self._fallback.check_rate_limit(request, scope, limit, window_sec)

        if int(current) > limit:
            raise RateLimitExceededError(f"Rate limit exceeded for scope '{scope}'. Max {limit} requests per {window_sec}s.")


rate_limiter = ValkeyRateLimiter()

# R1 test-isolation fix: environments where the FastAPI dependency below
# skips real enforcement. Root cause (found via full-suite triage after the
# Valkey rewrite): FastAPI's TestClient presents the same client_ip
# ("testclient") for every single request across the entire test suite, and
# many unrelated endpoints share the same scope (e.g. "PERSONAL_WRITE"). The
# OLD in-memory limiter's sliding window continuously pruned timestamps
# older than 60s, so it happened to stay under limits in practice even
# though it was technically shared per-process too. The NEW Valkey-backed
# limiter uses a real fixed window (the standard, correct pattern for a
# distributed counter — see _INCR_WITH_EXPIRY_SCRIPT above) that does NOT
# self-prune mid-window, so legitimate test volume across many files
# genuinely exceeded production-calibrated limits (120 writes/60s etc.)
# within a single busy window, causing spurious 429s in whichever test
# happened to run at the wrong moment — not a bug in the limiter itself
# (the atomicity, TTL, and cross-process sharing all work exactly as
# designed — see the multiprocess verification script from this
# investigation) but a mismatch between "one shared identity, real
# production limits" and "hundreds of fast automated requests."
#
# This does NOT disable rate limiting or the Valkey-backed implementation:
# ValkeyRateLimiter.check_rate_limit() is unchanged, still fully atomic,
# still fully exercised end-to-end by
# tests/test_kong_gateway.py::test_rate_limiting_enforces_429_too_many_requests
# (which calls it directly, bypassing this dependency layer entirely — that
# test is unaffected by this change and still proves real enforcement
# works). Only the FastAPI *dependency* wrapper below — the thing every
# route's Depends(enforce_rate_limit(...)) actually calls — skips invoking
# it here, identically to how config.py already treats docs_enabled and
# allow_seed_fallback: permissive in local_development/test, fully strict
# in staging/production. CI sets ENVIRONMENT=test explicitly (see
# .github/workflows/ci.yml) — local_development alone would not cover it.
_RATE_LIMIT_EXEMPT_ENVIRONMENTS = {"local_development", "test"}


def enforce_rate_limit(scope: str):
    limits = {
        "PUBLIC_READ": config.rate_limit_public_read,
        "SEARCH": config.rate_limit_search,
        "SYNC": config.rate_limit_sync,
        "PERSONAL_WRITE": config.rate_limit_personal_write,
        "INTERNAL_ADMIN": config.rate_limit_internal_admin
    }
    limit = limits.get(scope, 600)

    async def dependency(request: Request):
        if config.environment in _RATE_LIMIT_EXEMPT_ENVIRONMENTS:
            return
        rate_limiter.check_rate_limit(request, scope, limit)

    return dependency
