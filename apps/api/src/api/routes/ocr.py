"""OCR pipeline REST endpoints — document upload + text extraction.

Provides:
- POST /api/v1/ocr/upload: upload document + run OCR
- POST /api/v1/ocr/process/{document_id}: process existing document through OCR
- GET /api/v1/ocr/results/{document_id}: get OCR results for a document

All endpoints require inspector+ role. Upload creates a document record
and returns OCR results immediately. Process runs OCR on an existing document.
Results returns the cached OCR output.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from api.dependencies.auth import require_role
from api.models.user import UserModel
from api.services.ocr_service import OcrService

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class OcrResultResponse(BaseModel):
    """Response model for OCR processing results."""

    document_id: uuid.UUID
    text: str
    confidence: str = Field(description="HIGH|MEDIUM|LOW")
    language: str = Field(description="Detected language: ru|kk|unknown")
    entities: list[dict] = Field(
        default_factory=list,
        description="Extracted entities (structure_name, year, district, etc.)",
    )
    processed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class OcrUploadResponse(BaseModel):
    """Response model for document upload + OCR."""

    document_id: uuid.UUID
    minio_object_key: str
    ocr_result: OcrResultResponse


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_ocr_service(request: Request) -> OcrService:
    """Get OcrService from app state (initialized during lifespan)."""
    return OcrService(minio_service=request.app.state.minio)


# ---------------------------------------------------------------------------
# In-memory OCR results cache (MVP: production would use DB)
# ---------------------------------------------------------------------------

_ocr_results_cache: dict[uuid.UUID, dict] = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    response_model=OcrUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_and_ocr(
    file: UploadFile,
    request: Request,
    current_user: UserModel = Depends(require_role("inspector")),
) -> OcrUploadResponse:
    """Upload a document and run OCR on it (inspector+ role).

    1. Upload file to MinIO (sujoly-documents bucket)
    2. Run OCR extraction
    3. Cache results
    4. Return document ID + OCR results

    For MVP: does not create a DocumentModel in DB — that should be done
    via the /documents endpoint separately. This endpoint focuses on OCR.
    """
    service = _get_ocr_service(request)

    # Read file content
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded",
        )

    # Upload to MinIO
    doc_id = uuid.uuid4()
    object_key = f"ocr-uploads/{doc_id}/{file.filename}"
    service.minio.client.put_object(
        "sujoly-documents",
        object_key,
        data=__import__("io").BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=file.content_type or "application/octet-stream",
    )

    # Run OCR
    ocr_result = await service.extract_text(file_bytes, file.filename or "unknown")

    # Build response
    result = OcrResultResponse(
        document_id=doc_id,
        text=ocr_result["text"],
        confidence=ocr_result["confidence"],
        language=ocr_result["language"],
        entities=ocr_result["entities"],
    )

    # Cache results
    _ocr_results_cache[doc_id] = result.model_dump()

    return OcrUploadResponse(
        document_id=doc_id,
        minio_object_key=object_key,
        ocr_result=result,
    )


@router.post(
    "/process/{document_id}",
    response_model=OcrResultResponse,
)
async def process_document(
    document_id: uuid.UUID,
    request: Request,
    current_user: UserModel = Depends(require_role("inspector")),
) -> OcrResultResponse:
    """Process an existing document through OCR (inspector+ role).

    Loads the document from DB, fetches from MinIO, runs OCR,
    and caches the results.
    """
    service = _get_ocr_service(request)

    try:
        ocr_result = await service.process_document(document_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    result = OcrResultResponse(
        document_id=document_id,
        text=ocr_result["text"],
        confidence=ocr_result["confidence"],
        language=ocr_result["language"],
        entities=ocr_result["entities"],
    )

    # Cache results
    _ocr_results_cache[document_id] = result.model_dump()

    return result


@router.get(
    "/results/{document_id}",
    response_model=OcrResultResponse,
)
async def get_ocr_results(
    document_id: uuid.UUID,
    current_user: UserModel = Depends(require_role("viewer")),
) -> OcrResultResponse:
    """Get cached OCR results for a document (viewer+ role).

    Returns the previously computed OCR results from the in-memory cache.
    If no results are cached, returns 404.
    """
    cached = _ocr_results_cache.get(document_id)
    if cached is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OCR results not found for document '{document_id}'",
        )

    return OcrResultResponse(**cached)
