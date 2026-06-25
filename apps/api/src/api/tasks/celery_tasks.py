"""Celery task definitions for the SuJoly Inspector API."""

from datetime import datetime, timezone

from api.celery_app import celery_app
from api.services.ingestion_service import bulk_insert_structures


@celery_app.task
def health_check_task():
    """Simple task to verify Celery + Redis are working.

    Returns a dict with status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@celery_app.task(bind=True, name="ingest_kazvodhoz")
def ingest_kazvodhoz_task(self, filepath: str = "датасет.xls", force: bool = False):
    """Ingest Kazvodhoz spreadsheet into PostGIS.

    Uses sync psycopg connection for efficient bulk loading (D-17).
    Idempotent: checks source_reference in provenance before inserting (D-19).

    Args:
        self: Celery task instance (bind=True)
        filepath: Path to the .xls spreadsheet file
        force: If True, re-ingest existing records instead of skipping

    Returns:
        dict with "inserted", "skipped", "total" keys
    """
    return bulk_insert_structures(filepath=filepath, force=force)
