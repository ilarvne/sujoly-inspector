"""Export REST endpoints — CSV/GeoJSON/PDF with trilingual support (D-19).

Provides:
- GET /api/v1/export/structures: CSV or GeoJSON export with filters + lang
- GET /api/v1/export/inspection-report/{id}: PDF inspection report with lang

All endpoints require viewer+ role per D-12 RBAC.
Filter params (type, district, condition, bbox) scope the export.
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from api.dependencies.auth import require_role
from api.models.user import UserModel
from api.services import export_service

router = APIRouter(prefix="/api/v1/export", tags=["exports"])


@router.get("/structures")
async def export_structures_endpoint(
    format: Literal["csv", "geojson"] = "csv",
    lang: Literal["ru", "kk", "en"] = "ru",
    type: str | None = None,
    district: str | None = None,
    condition: str | None = None,
    bbox: str | None = Query(None, description="minx,miny,maxx,maxy (EPSG:4326)"),
    current_user: UserModel = Depends(require_role("viewer")),
):
    """Export structure list as CSV or GeoJSON with filters and lang (D-19).

    CSV export (D-20): StreamingResponse with UTF-8 BOM, trilingual headers,
    risk assessment fields. Formula injection mitigation (T-03-18).

    GeoJSON export (D-21): FeatureCollection with risk fields in properties.
    Reuses existing GeoJSON pattern from structures endpoint.

    Filters: type, district, condition, bbox scope the export.
    Bbox validation reused from structure_service._apply_bbox_filter (T-03-19).
    """
    filters = {
        "type": type,
        "district": district,
        "technical_condition": condition,
        "bbox": bbox,
    }

    # Remove None values from filters
    filters = {k: v for k, v in filters.items() if v is not None}

    try:
        if format == "csv":
            return await export_service.export_structures_csv(
                lang=lang, filters=filters
            )
        else:  # geojson
            data = await export_service.export_structures_geojson(
                lang=lang, filters=filters
            )
            return JSONResponse(content=data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/inspection-report/{inspection_id}")
async def export_inspection_report_endpoint(
    inspection_id: uuid.UUID,
    lang: Literal["ru", "kk", "en"] = "ru",
    request: Request = None,
    current_user: UserModel = Depends(require_role("viewer")),
):
    """Generate PDF inspection report via WeasyPrint + Jinja2 (D-22).

    Returns application/pdf with trilingual template based on lang parameter.
    Includes structure identity, inspection details, findings, photos as base64,
    and risk assessment summary.

    404 if inspection_id not found.
    """
    minio_service = getattr(request.app.state, "minio", None) if request else None

    try:
        return await export_service.export_inspection_report_pdf(
            inspection_id=inspection_id,
            lang=lang,
            minio_service=minio_service,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
