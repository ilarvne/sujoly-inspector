"""Celery application instance with Redis broker and result backend."""

from celery import Celery

from api.config.settings import settings

celery_app = Celery(
    "sujoly_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
