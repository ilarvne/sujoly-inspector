"""Celery task definitions for the SuJoly Inspector API."""

from datetime import datetime, timezone

from api.celery_app import celery_app


@celery_app.task
def health_check_task():
    """Simple task to verify Celery + Redis are working.

    Returns a dict with status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
