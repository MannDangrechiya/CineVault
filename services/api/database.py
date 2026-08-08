# CineVault OS — Database Integration Module
# Connects API service to PostgreSQL via PgBouncer transaction pooler (ADR-001)

import socket
import logging
from typing import Dict, Any
from .config import config

logger = logging.getLogger("cinevault.database")

class DatabaseManager:
    """Manages PgBouncer connection pool checks and health status."""
    
    def __init__(self):
        self.host = config.pgbouncer_host
        self.port = config.pgbouncer_port
        self.db = config.postgres_db
        self.user = config.postgres_user

    def check_health(self) -> Dict[str, Any]:
        """
        Verifies connectivity to PgBouncer socket.
        Returns health status dictionary for readiness probe.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                return {
                    "status": "HEALTHY",
                    "target": f"{self.host}:{self.port}",
                    "pool_mode": "transaction",
                    "database": self.db
                }
            else:
                return {
                    "status": "UNHEALTHY",
                    "target": f"{self.host}:{self.port}",
                    "error": f"Connection refused or unreachable (code {result})"
                }
        except Exception as e:
            return {
                "status": "UNHEALTHY",
                "target": f"{self.host}:{self.port}",
                "error": str(e)
            }

db_manager = DatabaseManager()
