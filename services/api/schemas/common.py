# CineVault OS — Common Response & Pagination Schemas
# Standardized cursor pagination & RFC 7807 error models

from typing import List, Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")

class CursorPagination(BaseModel):
    next_cursor: Optional[str] = Field(None, description="Opaque cursor token for next page iteration")
    has_more: bool = Field(False, description="Flag indicating if more records are available")
    limit: int = Field(25, description="Page limit requested")

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: CursorPagination

class APIErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str

class APIErrorBody(BaseModel):
    code: str
    message: str
    status: int
    correlation_id: str
    timestamp: str
    details: Optional[List[APIErrorDetail]] = []

class APIErrorResponse(BaseModel):
    error: APIErrorBody
