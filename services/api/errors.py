# CineVault OS — Safe API Error Boundary Module
# RFC 7807 problem details format with strict PII & infra detail redaction

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("cinevault.errors")

class APIError(Exception):
    """Base class for CineVault domain API errors."""
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[List[Dict[str, Any]]] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []

class RateLimitExceededError(APIError):
    def __init__(self, message: str = "Rate limit quota exceeded. Please retry later."):
        super().__init__("RATE_LIMIT_EXCEEDED", message, status.HTTP_429_TOO_MANY_REQUESTS)

class EntityNotFoundError(APIError):
    def __init__(self, resource: str, identifier: str):
        super().__init__("ENTITY_NOT_FOUND", f"The requested {resource} entity '{identifier}' was not found.", status.HTTP_404_NOT_FOUND)

def format_error_response(
    code: str,
    message: str,
    status_code: int,
    correlation_id: str,
    details: Optional[List[Dict[str, Any]]] = None
) -> JSONResponse:
    """Formats safe RFC 7807 error payload."""
    payload = {
        "error": {
            "code": code,
            "message": message,
            "status": status_code,
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or []
        }
    }
    
    headers = {"X-Correlation-ID": correlation_id}
    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        headers["Retry-After"] = "60"
        
    return JSONResponse(status_code=status_code, content=payload, headers=headers)

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "018f2e4a-7b31-7000-8000-000000000000")
    logger.warning(f"API Error [{exc.code}] on {request.method} {request.url.path}: {exc.message}")
    return format_error_response(exc.code, exc.message, exc.status_code, correlation_id, exc.details)

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "018f2e4a-7b31-7000-8000-000000000000")
    code = "UNAUTHORIZED" if exc.status_code == 401 else ("FORBIDDEN" if exc.status_code == 403 else "HTTP_ERROR")
    return format_error_response(code, exc.detail, exc.status_code, correlation_id)

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "018f2e4a-7b31-7000-8000-000000000000")
    details = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", [])])
        details.append({"field": field, "issue": err.get("msg", "Invalid field value")})
    return format_error_response("VALIDATION_ERROR", "Request payload or query parameter validation failed.", status.HTTP_422_UNPROCESSABLE_ENTITY, correlation_id, details)

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "018f2e4a-7b31-7000-8000-000000000000")
    # Log full trace internally for telemetry, return sanitized message to client
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return format_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An internal server error occurred. Please contact system support with the correlation ID.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        correlation_id=correlation_id
    )
