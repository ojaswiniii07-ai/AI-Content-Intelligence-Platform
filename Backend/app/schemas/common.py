from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized API response envelope."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthResponse(BaseModel):
    status: str = "healthy"
    environment: str
    version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DatabaseReadiness(BaseModel):
    status: str  # "operational" or "unavailable"
    connected: bool
    latency_ms: float
    details: str


class ReadyResponse(BaseModel):
    status: str  # "ready" or "degraded"
    environment: str
    database: DatabaseReadiness
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
