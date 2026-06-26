"""Celery application instance with Redis broker, result backend, and Beat schedule.

Beat schedule runs daily risk recomputation at 2 AM UTC (D-05 trigger 3).
"""

from celery import Celery
from celery.schedules import crontab

from api.config.settings import settings

celery_app = Celery(
    "sujoly_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["api.tasks.celery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# D-05 trigger 3: daily recomputation of all structure risk assessments
celery_app.conf.beat_schedule = {
    "daily-risk-recomputation": {
        "task": "recompute_all_risks",
        "schedule": crontab(hour=2, minute=0),
    },
}
