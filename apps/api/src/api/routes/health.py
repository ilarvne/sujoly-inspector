"""Health check endpoints for the SuJoly Inspector API.

Provides:
- GET /health/live: simple liveness check (service is running)
- GET /health/ready: deep readiness check (probes PostgreSQL, Redis, MinIO)
"""

from typing import Literal

from fastapi import APIRouter, Response
from minio import Minio
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text

from api.config.settings import settings
from api.infrastructure.database import async_session

router = APIRouter(tags=["health"])


class ComponentHealth(BaseModel):
    """Health status for a single component."""

    status: Literal["ok", "error"]
    message: str | None = None


class HealthStatus(BaseModel):
    """Overall health status response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    checks: dict[str, ComponentHealth]


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """Simple liveness check — confirms the service is running."""
    return {"status": "ok"}


@router.get("/health/ready", response_model=HealthStatus)
async def readiness_check(response: Response) -> HealthStatus:
    """Deep readiness check verifying PostgreSQL, Redis, and MinIO connectivity.

    Returns 200 with status=healthy when all services are reachable.
    Returns 503 with status=degraded when any service is unreachable.
    """
    checks: dict[str, ComponentHealth] = {}
    overall: Literal["healthy", "degraded", "unhealthy"] = "healthy"

    # Check PostgreSQL
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = ComponentHealth(status="ok")
    except Exception as e:
        checks["postgres"] = ComponentHealth(status="error", message=str(e))
        overall = "degraded"

    # Check Redis
    try:
        redis = Redis.from_url(settings.redis_url)
        await redis.ping()
        await redis.aclose()
        checks["redis"] = ComponentHealth(status="ok")
    except Exception as e:
        checks["redis"] = ComponentHealth(status="error", message=str(e))
        overall = "degraded"

    # Check MinIO
    try:
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )
        client.bucket_exists(settings.minio_bucket)
        checks["minio"] = ComponentHealth(status="ok")
    except Exception as e:
        checks["minio"] = ComponentHealth(status="error", message=str(e))
        overall = "degraded"

    if overall != "healthy":
        response.status_code = 503

    return HealthStatus(status=overall, checks=checks)
