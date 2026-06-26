"""Ingestion REST endpoints.

Provides:
- POST /api/v1/ingestion/kazvodhoz: trigger Celery ingestion task (202 + job_id)
- GET /api/v1/ingestion/kazvodhoz/{job_id}: poll Celery task status

D-15: Ingestion endpoint triggers Celery task, returns job ID immediately.
T-02-04: Validates file upload extension is .xls only (rejects .xlsx, .csv, etc.).
"""

import os
import tempfile

from celery.result import AsyncResult
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from api.celery_app import celery_app
from api.tasks.celery_tasks import ingest_kazvodhoz_task

router = APIRouter(prefix="/api/v1", tags=["ingestion"])

# T-02-04: Maximum file size for uploads (10MB)
_MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post(
    "/ingestion/kazvodhoz",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_ingestion(
    file: UploadFile | None = File(None, description="Optional .xls file upload"),
    force: bool = Query(False, description="Re-ingest even if records exist"),
) -> dict:
    """Trigger Kazvodhoz spreadsheet ingestion via Celery task.

    If no file is uploaded, uses the bundled 'датасет.xls' file.

    Args:
        file: Optional .xls file upload (T-02-04: validates extension)
        force: If True, re-ingest existing records

    Returns:
        202 Accepted with {"job_id": str, "status": "queued"}
    """
    filepath = "датасет.xls"  # default bundled file

    if file is not None:
        # T-02-04: Validate file extension is .xls only
        filename = file.filename or ""
        if not filename.lower().endswith(".xls"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be .xls format (xlsx, csv, and other formats are not accepted)",
            )

        # Save uploaded file to temp location
        content = await file.read()
        # T-02-04: Check file size < 10MB
        if len(content) > _MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 10MB limit",
            )

        # Write to temp file with .xls extension (xlrd requires it)
        fd, filepath = tempfile.mkstemp(suffix=".xls")
        try:
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(content)
        except Exception:
            os.unlink(filepath)
            raise

    task = ingest_kazvodhoz_task.delay(filepath=filepath, force=force)
    return {"job_id": task.id, "status": "queued"}


@router.get("/ingestion/kazvodhoz/{job_id}")
async def get_ingestion_status(job_id: str) -> dict:
    """Poll the status of a Kazvodhoz ingestion Celery task.

    Args:
        job_id: Celery task ID from POST /ingestion/kazvodhoz response

    Returns:
        {"job_id": str, "status": "SUCCESS|PENDING|FAILURE|...", "result": dict|None}
    """
    result = AsyncResult(job_id, app=celery_app)
    return {
        "job_id": job_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
