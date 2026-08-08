# CineVault OS — Rate Limiting Policy Enforcement Module
# Implements sliding window rate limiting for public, search, sync, and admin endpoints

import time
from typing import Dict, Tuple
from fastapi import Request
from .config import config
from .errors import RateLimitExceededError

class InMemoryRateLimiter:
    """Sliding window rate limiter for local development and unit testing."""
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

rate_limiter = InMemoryRateLimiter()

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
        rate_limiter.check_rate_limit(request, scope, limit)
        
    return dependency
