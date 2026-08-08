# CineVault OS — Valkey Integration Module
# Implements Valkey in-memory caching and rate-limiting distributed state boundary

import socket
import logging
from typing import Dict, Any, Optional
from .config import config

logger = logging.getLogger("cinevault.valkey")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis-py package not found. ValkeyManager running in fallback mode.")

class ValkeyManager:
    """Manages Valkey distributed state, rate-limiting counters, and idempotency checks."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or config.valkey_host
        self.port = port or config.valkey_port
        self._client: Optional[Any] = None

    def get_client(self):
        """Lazy initialization of Valkey/Redis client with instant socket check."""
        if not REDIS_AVAILABLE:
            return None
        # Instant socket check to avoid client-side connection retries when Valkey is offline
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            res = sock.connect_ex((self.host, self.port))
            sock.close()
            if res != 0:
                return None
        except Exception:
            return None

        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    socket_connect_timeout=0.2,
                    socket_timeout=0.2,
                    decode_responses=True
                )
            except Exception as e:
                logger.error(f"Failed to create Valkey client: {e}")
                return None
        return self._client

    def check_health(self) -> Dict[str, Any]:
        """
        Verifies connectivity to Valkey server.
        Returns health status for readiness probe.
        """
        # Fast socket check first
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result != 0:
                return {
                    "status": "UNHEALTHY",
                    "target": f"{self.host}:{self.port}",
                    "error": f"Valkey port unreachable (code {result})"
                }
        except Exception as e:
            return {
                "status": "UNHEALTHY",
                "target": f"{self.host}:{self.port}",
                "error": str(e)
            }

        client = self.get_client()
        if client:
            try:
                if client.ping():
                    return {
                        "status": "HEALTHY",
                        "target": f"{self.host}:{self.port}",
                        "engine": "Valkey 8.0 (Linux Foundation RESP)"
                    }
            except Exception as e:
                logger.warning(f"Valkey ping failed: {e}")
                return {
                    "status": "UNHEALTHY",
                    "target": f"{self.host}:{self.port}",
                    "error": str(e)
                }

        return {
            "status": "HEALTHY",
            "target": f"{self.host}:{self.port}",
            "engine": "Valkey 8.0 (Linux Foundation RESP)"
        }

    def get(self, key: str) -> Optional[str]:
        """Reads a cached value from Valkey."""
        client = self.get_client()
        if not client:
            return None
        try:
            return client.get(key)
        except Exception as e:
            logger.error(f"Valkey GET error key={key}: {e}")
            return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Sets a cached value in Valkey with optional TTL (seconds)."""
        client = self.get_client()
        if not client:
            return False
        try:
            if ttl:
                return bool(client.setex(key, ttl, value))
            return bool(client.set(key, value))
        except Exception as e:
            logger.error(f"Valkey SET error key={key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Deletes a key from Valkey."""
        client = self.get_client()
        if not client:
            return False
        try:
            return bool(client.delete(key))
        except Exception as e:
            logger.error(f"Valkey DELETE error key={key}: {e}")
            return False

    def incr_rate_limit(self, key: str, ttl: int = 60) -> int:
        """Atomic rate-limit counter increment with TTL expiry window."""
        client = self.get_client()
        if not client:
            return 1
        try:
            pipeline = client.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, ttl)
            res = pipeline.execute()
            return int(res[0])
        except Exception as e:
            logger.error(f"Valkey INCR rate limit error key={key}: {e}")
            return 1

    def check_and_set_idempotency(self, idempotency_key: str, ttl: int = 86400) -> bool:
        """
        Atomic idempotency check-and-set using SETNX logic.
        Returns True if the idempotency key is NEW (successfully acquired).
        Returns False if the key already exists (DUPLICATE request detected).
        """
        client = self.get_client()
        if not client:
            # If cache unavailable, fail safe (allow processing)
            return True
        try:
            full_key = f"idempotency:{idempotency_key}"
            is_new = client.set(full_key, "1", nx=True, ex=ttl)
            return bool(is_new)
        except Exception as e:
            logger.error(f"Valkey idempotency check error key={idempotency_key}: {e}")
            return True

valkey_manager = ValkeyManager()
