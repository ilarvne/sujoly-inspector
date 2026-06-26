"""Celery task definitions for the SuJoly Inspector API.

Tasks:
- health_check_task: verify Celery + Redis are working
- ingest_kazvodhoz: bulk ingest Kazvodhoz spreadsheet (D-17)
- recompute_structure_risk: event-driven risk recomputation for one structure (D-05)
- recompute_all_risks: daily bulk recomputation for all structures (D-05 trigger 3)
"""

import asyncio
import uuid
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


@celery_app.task(name="recompute_structure_risk")
def recompute_structure_risk(structure_id: str):
    """Recompute risk assessment for a single structure (D-05).

    Celery tasks are synchronous — uses asyncio.run() to call the async
    risk_service.recompute_risk_for_structure. This task is triggered by:
    - D-05 trigger 1: after new inspection (from inspection_service)
    - D-05 trigger 2: after structure update (from structure_service)
    - D-05 trigger 4: manual API call (from /structures/{id}/recompute endpoint)

    Args:
        structure_id: UUID string of the structure to recompute

    Returns:
        dict with structure_id and new assessment id
    """
    from api.services import risk_service as _risk_service

    result = asyncio.run(
        _risk_service.recompute_risk_for_structure(uuid.UUID(structure_id))
    )
    return {"structure_id": structure_id, "assessment_id": str(result.id)}


@celery_app.task(name="recompute_all_risks")
def recompute_all_risks():
    """Daily bulk risk recomputation for all structures (D-05 trigger 3).

    Loads all active structure IDs from the database and dispatches
    a recompute_structure_risk task for each one. Scheduled via
    Celery Beat at 2 AM UTC daily.

    Returns:
        dict with total count of structures dispatched for recomputation
    """
    from api.infrastructure.database import async_session
    from api.models.structure import StructureModel as _StructureModel
    from sqlalchemy import select

    async def _load_structure_ids():
        async with async_session() as session:
            result = await session.execute(
                select(_StructureModel.id).where(
                    _StructureModel.status != "deleted"
                )
            )
            return [str(row[0]) for row in result.all()]

    structure_ids = asyncio.run(_load_structure_ids())
    count = 0
    for sid in structure_ids:
        recompute_structure_risk.delay(sid)
        count += 1

    return {"dispatched": count, "timestamp": datetime.now(timezone.utc).isoformat()}
