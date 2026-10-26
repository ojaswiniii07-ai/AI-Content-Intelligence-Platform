from fastapi import APIRouter

from app.api.v1.endpoints import (
    analysis,
    audit,
    auth,
    batches,
    dashboard,
    health,
    shortlisting,
)

api_router = APIRouter()

# Core health probes (health, ready)
api_router.include_router(health.router)

# Authentication & Current-User
api_router.include_router(auth.router)

# Platform Feature Routers
api_router.include_router(dashboard.router)
api_router.include_router(analysis.router)
api_router.include_router(shortlisting.router)
api_router.include_router(audit.router)
api_router.include_router(batches.router)
