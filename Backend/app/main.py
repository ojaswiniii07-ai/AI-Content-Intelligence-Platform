import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]",
        extra={"origins": settings.CORS_ORIGINS},
    )
    # Ensure database tables exist
    try:
        from app.db.base import Base
        from app.db.session import engine
        import app.models  # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as exc:
        logger.warning(f"Database schema auto-init warning: {exc}")

    # Warm up ML text detector model in the background
    try:
        from ai.ml.detector import get_detector
        asyncio.create_task(asyncio.to_thread(get_detector))
        logger.info("ML text detector warmup initiated.")
    except Exception as exc:
        logger.warning(f"ML detector warmup skipped: {exc}")

    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


def create_application() -> FastAPI:
    """Factory function for initializing the FastAPI application."""
    setup_logging(settings.LOG_LEVEL)

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend API Foundation for ContentIQ AI Content Intelligence Platform",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS for configured frontend origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing & structured access logger middleware
    @app.middleware("http")
    async def request_timing_middleware(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
            extra={
                "endpoint": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        return response

    # Centralized error handlers
    register_error_handlers(app)

    # Mount API v1 endpoints
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # ── Mount Frontend Static Files & SPA Routing ───────────────
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi import HTTPException

    frontend_dist = Path(__file__).resolve().parents[2] / "dist"
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            # Pass through API and doc routes
            if (
                full_path.startswith("api/")
                or full_path.startswith("docs")
                or full_path.startswith("redoc")
                or full_path == "openapi.json"
            ):
                raise HTTPException(status_code=404, detail="Not Found")

            target_file = frontend_dist / full_path
            if target_file.is_file():
                return FileResponse(str(target_file))
            return FileResponse(str(frontend_dist / "index.html"))
    else:
        @app.get("/", tags=["Root"])
        async def root_info():
            return {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "docs": "/docs",
                "api_prefix": settings.API_V1_PREFIX,
                "status": "online",
            }

    return app


app = create_application()
