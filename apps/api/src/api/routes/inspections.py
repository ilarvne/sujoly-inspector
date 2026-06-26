"""Inspection history REST endpoints — CRUD + photo attachments + MinIO integration.

Provides:
- POST /api/v1/structures/{id}/inspections: create inspection with photos (inspector+) per D-16
- GET /api/v1/structures/{id}/inspections: list inspections with photo URLs (all roles) per D-16
- GET /api/v1/structures/{id}/inspections/{inspection_id}: inspection detail with photos (all roles) per D-16

RBAC enforcement per D-12 permissions matrix:
- POST requires inspector+ role (T-03-15 mitigation)
- GET endpoints require viewer+ role (any authenticated user)
- Photo presigned URLs are generated on-demand with 2hr expiry (T-03-14 mitigation)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.dependencies.auth import require_role
from api.models.user import UserModel
from api.schemas.inspections import (
    InspectionCreate,
    InspectionListResponse,
    InspectionResponse,
    PhotoResponse,
)
from api.services import inspection_service

router = APIRouter(prefix="/api/v1", tags=["inspections"])


@router.post(
    "/structures/{structure_id}/inspections",
    response_model=InspectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_inspection_endpoint(
    structure_id: uuid.UUID,
    body: InspectionCreate,
    current_user: UserModel = Depends(require_role("inspector")),
) -> InspectionResponse:
    """Create an inspection record with optional photo attachments (D-16).

    Requires inspector+ role per D-12 RBAC retrofit.
    Creates ProvenanceModel with source_type='inspection' (DATA-07).
    Dispatches recompute_structure_risk Celery task after creation (D-05 trigger #1).
    Returns 404 if the structure does not exist.
    """
    model = await inspection_service.create_inspection(
        structure_id=structure_id,
        data=body,
        user=current_user,
    )
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure '{structure_id}' not found",
        )
    return InspectionResponse.model_validate(model)


@router.get(
    "/structures/{structure_id}/inspections",
    response_model=InspectionListResponse,
)
async def list_inspections_endpoint(
    structure_id: uuid.UUID,
    request: Request,
    offset: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_role("viewer")),
) -> InspectionListResponse:
    """List inspections for a structure with photo presigned URLs (D-16).

    Requires viewer+ role per D-12 RBAC retrofit.
    Photo presigned download URLs are generated on-demand (2hr expiry).
    Results ordered by inspection_date DESC (newest first).
    """
    items, total = await inspection_service.list_inspections(
        structure_id=structure_id,
        offset=offset,
        limit=limit,
    )

    # Generate presigned download URLs for each photo (T-03-14 mitigation)
    minio_service = request.app.state.minio
    response_items = []
    for inspection in items:
        resp = InspectionResponse.model_validate(inspection)
        for i, photo in enumerate(resp.photos):
            try:
                photo.presigned_download_url = minio_service.presigned_download_url(
                    photo.minio_bucket,
                    photo.minio_object_key,
                )
            except Exception:
                photo.presigned_download_url = None
        response_items.append(resp)

    return InspectionListResponse(
        items=response_items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/structures/{structure_id}/inspections/{inspection_id}",
    response_model=InspectionResponse,
)
async def get_inspection_endpoint(
    structure_id: uuid.UUID,
    inspection_id: uuid.UUID,
    request: Request,
    current_user: UserModel = Depends(require_role("viewer")),
) -> InspectionResponse:
    """Get inspection detail with photos and presigned download URLs (D-16).

    Requires viewer+ role per D-12 RBAC retrofit.
    Photo presigned download URLs are generated on-demand (2hr expiry).
    Returns 404 if the inspection does not exist.
    """
    model = await inspection_service.get_inspection(inspection_id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection '{inspection_id}' not found",
        )

    # Verify inspection belongs to the requested structure (T-03-09a mitigation)
    if model.structure_id != structure_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection '{inspection_id}' not found for structure '{structure_id}'",
        )

    resp = InspectionResponse.model_validate(model)

    # Generate presigned download URLs for photos (T-03-14 mitigation)
    minio_service = request.app.state.minio
    for photo in resp.photos:
        try:
            photo.presigned_download_url = minio_service.presigned_download_url(
                photo.minio_bucket,
                photo.minio_object_key,
            )
        except Exception:
            photo.presigned_download_url = None

    return resp
