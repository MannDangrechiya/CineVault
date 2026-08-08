# CineVault OS — RabbitMQ AMQP Message Broker Integration Module
# Implements AMQP 0-9-1 broker topology, Quorum Queues, Dead-Letter Exchange (DLX), Retry & Rejection Topology, and Health Probes

import json
import logging
import socket
from typing import Dict, Any, Optional
from .config import config

logger = logging.getLogger("cinevault.rabbitmq")

try:
    import pika
    PIKA_AVAILABLE = True
except ImportError:
    PIKA_AVAILABLE = False
    logger.warning("pika package not found. RabbitMQManager running in fallback mode.")

# Maximum allowed message size: 512 KB
MAX_MESSAGE_SIZE_BYTES = 512 * 1024

class PayloadValidationError(Exception):
    """Raised when a message payload violates safety or schema rules."""
    pass

class RabbitMQManager:
    """Manages RabbitMQ broker connections, Quorum Queue topologies, DLX, and message safety."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 user: Optional[str] = None, password: Optional[str] = None,
                 vhost: Optional[str] = None):
        self.host = host or config.rabbitmq_host
        self.port = port or config.rabbitmq_port
        self.user = user or config.rabbitmq_user
        self.password = password or config.rabbitmq_password
        self.vhost = vhost or config.rabbitmq_vhost

    def _get_connection_params(self, timeout: float = 1.0, attempts: int = 1):
        if not PIKA_AVAILABLE:
            return None
        credentials = pika.PlainCredentials(self.user, self.password)
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials,
            socket_timeout=timeout,
            connection_attempts=attempts,
            retry_delay=0.1
        )

    def check_health(self) -> Dict[str, Any]:
        """
        Verifies AMQP connectivity to RabbitMQ broker.
        Returns health status without exposing sensitive credentials or topology contents.
        Uses instant socket probe before attempting AMQP handshake.
        """
        # 1. Fast socket check first
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()

            if result != 0:
                return {
                    "status": "UNHEALTHY",
                    "target": f"{self.host}:{self.port}",
                    "error": f"RabbitMQ port unreachable (code {result})"
                }
        except Exception as e:
            return {
                "status": "UNHEALTHY",
                "target": f"{self.host}:{self.port}",
                "error": str(e)
            }

        # 2. AMQP Handshake via Pika if socket is listening
        if PIKA_AVAILABLE:
            try:
                params = self._get_connection_params(timeout=1.0, attempts=1)
                connection = pika.BlockingConnection(params)
                if connection.is_open:
                    connection.close()
                    return {
                        "status": "HEALTHY",
                        "target": f"{self.host}:{self.port}",
                        "engine": "RabbitMQ 4.0 (AMQP 0-9-1)"
                    }
            except Exception as e:
                logger.warning(f"RabbitMQ pika health check failed: {e}")
                return {
                    "status": "UNHEALTHY",
                    "target": f"{self.host}:{self.port}",
                    "error": str(e)
                }

        return {
            "status": "HEALTHY",
            "target": f"{self.host}:{self.port}",
            "engine": "RabbitMQ 4.0 (AMQP 0-9-1)"
        }

    def declare_topology(self) -> bool:
        """
        Declares locked Phase 4 Exchange and Quorum Queue topology.
        - Direct Exchange: cinevault.ingestion.direct
        - Dead-Letter Exchange (DLX): cinevault.dlx
        - Quorum Queues: queue.ingestion, queue.quality, queue.reconciliation, queue.sync, queue.media, queue.dead_letter
        - Retry Queue: queue.ingestion.retry
        """
        if not PIKA_AVAILABLE:
            logger.warning("pika not installed; skipping topology declaration.")
            return False

        try:
            params = self._get_connection_params()
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            # 1. Main Direct Exchange & Dead-Letter Exchange (DLX)
            channel.exchange_declare(
                exchange="cinevault.ingestion.direct",
                exchange_type="direct",
                durable=True
            )
            channel.exchange_declare(
                exchange="cinevault.dlx",
                exchange_type="direct",
                durable=True
            )

            # Common Quorum Queue Arguments with DLX configuration
            dlx_args = {
                "x-queue-type": "quorum",
                "x-dead-letter-exchange": "cinevault.dlx"
            }

            # 2. Main Workload Quorum Queues
            queues = [
                ("queue.ingestion", "ingestion.task", "ingestion.dead_letter"),
                ("queue.quality", "quality.task", "quality.dead_letter"),
                ("queue.reconciliation", "reconciliation.task", "reconciliation.dead_letter"),
                ("queue.sync", "sync.task", "sync.dead_letter"),
                ("queue.media", "media.task", "media.dead_letter"),
            ]

            for queue_name, routing_key, dlx_routing_key in queues:
                q_args = dlx_args.copy()
                q_args["x-dead-letter-routing-key"] = dlx_routing_key
                channel.queue_declare(queue=queue_name, durable=True, arguments=q_args)
                channel.queue_bind(
                    exchange="cinevault.ingestion.direct",
                    queue=queue_name,
                    routing_key=routing_key
                )

            # 3. Dead-Letter / Rejection Quorum Queue
            channel.queue_declare(
                queue="queue.dead_letter",
                durable=True,
                arguments={"x-queue-type": "quorum"}
            )
            for dlx_key in ["ingestion.dead_letter", "quality.dead_letter", "reconciliation.dead_letter", "sync.dead_letter", "media.dead_letter"]:
                channel.queue_bind(
                    exchange="cinevault.dlx",
                    queue="queue.dead_letter",
                    routing_key=dlx_key
                )

            # 4. Retry Queue Topology (TTL 5000ms dead-lettering back to main exchange)
            retry_args = {
                "x-queue-type": "quorum",
                "x-message-ttl": 5000,
                "x-dead-letter-exchange": "cinevault.ingestion.direct",
                "x-dead-letter-routing-key": "ingestion.task"
            }
            channel.queue_declare(queue="queue.ingestion.retry", durable=True, arguments=retry_args)
            channel.queue_bind(
                exchange="cinevault.ingestion.direct",
                queue="queue.ingestion.retry",
                routing_key="ingestion.retry"
            )

            connection.close()
            logger.info("RabbitMQ Quorum Queue topology and DLX declared successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to declare RabbitMQ topology: {e}")
            return False

    def validate_payload_safety(self, payload: Dict[str, Any]) -> str:
        """
        Validates message safety constraints:
        - Non-empty dictionary
        - Safe JSON serialization
        - Size < 512KB
        - No committed secrets or plaintext CAT-2 personal data fields
        """
        if not isinstance(payload, dict):
            raise PayloadValidationError("Payload must be a JSON-serializable dictionary.")

        # Check prohibited sensitive fields
        prohibited_keys = {"password", "secret", "token", "auth_token", "watch_event_notes", "user_address"}
        for k in payload.keys():
            if k.lower() in prohibited_keys:
                raise PayloadValidationError(f"Prohibited sensitive payload field detected: {k}")

        try:
            serialized = json.dumps(payload)
        except Exception as e:
            raise PayloadValidationError(f"Payload JSON serialization error: {e}")

        if len(serialized.encode("utf-8")) > MAX_MESSAGE_SIZE_BYTES:
            raise PayloadValidationError(f"Payload size exceeds limit of {MAX_MESSAGE_SIZE_BYTES} bytes.")

        return serialized

    def publish_message(self, exchange: str, routing_key: str, payload: Dict[str, Any],
                        correlation_id: str, idempotency_key: Optional[str] = None) -> bool:
        """
        Publishes a safe persistent message to RabbitMQ with correlation ID and idempotency headers.
        """
        if not PIKA_AVAILABLE:
            logger.warning("pika not installed; message publishing bypassed.")
            return False

        serialized_payload = self.validate_payload_safety(payload)

        headers = {
            "x-correlation-id": correlation_id
        }
        if idempotency_key:
            headers["x-idempotency-key"] = idempotency_key

        properties = pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,  # Persistent
            correlation_id=correlation_id,
            headers=headers
        )

        try:
            params = self._get_connection_params()
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=serialized_payload,
                properties=properties
            )
            connection.close()
            logger.info(f"Published message to {exchange}/{routing_key} | correlation_id={correlation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False

rabbitmq_manager = RabbitMQManager()
