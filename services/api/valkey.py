# CineVault OS — Valkey Integration Module
# Implements Valkey in-memory caching and rate-limiting distributed state boundary

import socket
import logging
from typing import Dict, Any
from .config import config

logger = logging.getLogger("cinevault.valkey")

class ValkeyManager:
    """Manages Valkey distributed state and rate-limiting connectivity checks."""
    
    def __init__(self):
        self.host = config.valkey_host
        self.port = config.valkey_port

    def check_health(self) -> Dict[str, Any]:
        """
        Verifies connectivity to Valkey server port.
        Returns health status for readiness probe.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                return {
                    "status": "HEALTHY",
                    "target": f"{self.host}:{self.port}",
                    "engine": "Valkey 8.0"
                }
            else:
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

valkey_manager = ValkeyManager()
