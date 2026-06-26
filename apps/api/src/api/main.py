"""SuJoly Inspector API — FastAPI application.

Lifespan initializes MinIOService and ensures buckets exist on startup.
Shutdown disposes the SQLAlchemy async engine.
"""

import importlib
import pkgutil
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config.settings import settings
from api.infrastructure.database import async_session, engine
from api.services.minio_client import MinIOService
from api.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)

_BUCKETS = ["sujoly-imagery", "sujoly-documents", "sujoly-photos"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: configure logging, init MinIO, ensure buckets, seed admin. Shutdown: dispose engine."""
    configure_logging(level="DEBUG" if settings.debug else "INFO")
    logger.info("api_starting", environment=settings.environment)

    # Initialize MinIO service and ensure buckets exist
    minio_service = MinIOService(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl,
    )
    for bucket in _BUCKETS:
        minio_service.ensure_bucket(bucket)
    app.state.minio = minio_service
    logger.info("minio_buckets_ready", buckets=_BUCKETS)

    # Seed initial admin user if no admin exists
    try:
        from api.models.user import UserModel
        from sqlalchemy import select

        async with async_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.role == "admin").limit(1)
            )
            if result.scalar_one_or_none() is None:
                admin = UserModel(
                    username=settings.initial_admin_username,
                    role="admin",
                    api_key=settings.initial_admin_api_key,
                    full_name="Initial Administrator",
                )
                session.add(admin)
                await session.commit()
                logger.info("initial_admin_seeded", username=admin.username)
    except ImportError:
        logger.warning("admin_seed_skipped", reason="UserModel not available yet")

    yield

    # Shutdown: clean up
    await engine.dispose()
    logger.info("api_stopped")


configure_logging(level="DEBUG" if settings.debug else "INFO")

app = FastAPI(
    title="SuJoly Inspector API",
    version="0.1.0",
    description="Backend API for the Zhambyl Hydraulic Structures Catalog",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler — catches HTTPException separately, logs unhandled errors."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )

    logger.exception(
        "unhandled_exception",
        request_id=getattr(request.state, "request_id", "unknown"),
        path=request.url.path,
        error_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"},
    )


@app.middleware("http")
async def add_headers_middleware(request: Request, call_next):
    """Add request ID, timing, and security headers to all responses."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception:
        raise

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'"

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip() for o in settings.allowed_origins.split(",") if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-User-ID", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# Auto-discover and include all route modules in api.routes
routes_dir = Path(__file__).parent / "routes"
for _, module_name, _ in pkgutil.iter_modules([str(routes_dir)]):
    module = importlib.import_module(f"api.routes.{module_name}")
    if hasattr(module, "router"):
        app.include_router(module.router)
        logger.debug("router_included", module=module_name)


@app.get("/health")
async def health_check():
    """Simple health check for Docker healthcheck and load balancer probes."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint — service info."""
    return {
        "name": "SuJoly Inspector API",
        "status": "operational",
    }


def main():
    """Run the API with uvicorn."""
    import uvicorn

    configure_logging()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
