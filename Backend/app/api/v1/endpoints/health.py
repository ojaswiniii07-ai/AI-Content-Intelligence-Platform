from datetime import datetime, timezone
from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.db.session import check_db_readiness
from app.schemas.common import DatabaseReadiness, HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health() -> HealthResponse:
    """
    Lightweight health check indicating API process liveness.
    Does not require database connectivity.
    """
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/ready", response_model=ReadyResponse, tags=["Health"])
async def get_ready(response: Response) -> ReadyResponse:
    """
    Readiness probe validating whether the application and its dependencies (PostgreSQL) are operational.
    Dynamically executes a SELECT 1 query against the database.
    Returns HTTP 200 if connected; returns HTTP 503 if the database is unreachable.
    NEVER reports connected without a verified connection query.
    """
    is_ready, details, latency_ms = await check_db_readiness()

    db_readiness = DatabaseReadiness(
        status="operational" if is_ready else "unavailable",
        connected=is_ready,
        latency_ms=latency_ms,
        details=details,
    )

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "degraded"
    else:
        response.status_code = status.HTTP_200_OK
        overall_status = "ready"

    return ReadyResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        database=db_readiness,
        timestamp=datetime.now(timezone.utc),
    )
