"""Structure REST endpoints — CRUD + multilingual search.

Provides:
- GET /api/v1/structures: list with filters, search, bbox, pagination, GeoJSON (D-16)
- GET /api/v1/structures/search: FTS + trigram ranked search (D-12, D-14)
- GET /api/v1/structures/{id}: detail or 404 (D-13)
- POST /api/v1/structures: create with 201 (D-13)
- PUT /api/v1/structures/{id}: update with provenance-per-fact (D-13)
- DELETE /api/v1/structures/{id}: soft delete via status field (D-13)
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies.auth import require_role
from api.models.user import UserModel
from api.schemas.structures import (
    SearchListResponse,
    SearchResultResponse,
    StructureCreate,
    StructureListResponse,
    StructureResponse,
    StructureUpdate,
)
from api.services.structure_service import (
    create_structure,
    delete_structure,
    get_structure,
    list_structures,
    search_structures,
    update_structure,
)

router = APIRouter(prefix="/api/v1", tags=["structures"])


@router.get("/structures", response_model=None)
async def list_structures_endpoint(
    type: str | None = None,
    district: str | None = None,
    technical_condition: str | None = None,
    water_source: str | None = None,
    q: str | None = Query(None, description="Full-text + fuzzy search query"),
    lang: Literal["ru", "kk", "en"] = "ru",
    bbox: str | None = Query(None, description="minx,miny,maxx,maxy (EPSG:4326)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    format: Literal["json", "geojson"] = "json",
):
    """List structures with filtering, search, bbox, and pagination (D-16).

    Filters: type, district, technical_condition, water_source.
    Search: if `q` is provided, delegates to FTS + trigram search.
    Spatial: bbox=minx,miny,maxx,maxy filters by bounding box (EPSG:4326).
    Pagination: offset/limit with total count.
    Format: json (default) or geojson (GeoJSON FeatureCollection for map clients).
    """
    filters = {
        "type": type,
        "district": district,
        "technical_condition": technical_condition,
        "water_source": water_source,
    }

    try:
        items, total = await list_structures(
            filters=filters,
            q=q,
            lang=lang,
            bbox=bbox,
            offset=offset,
            limit=limit,
            format=format,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if format == "geojson":
        features = []
        for item in items:
            props = StructureResponse.model_validate(item).model_dump()
            geom = props.pop("geometry", None)
            features.append(
                {
                    "type": "Feature",
                    "geometry": geom,
                    "properties": props,
                }
            )
        return {"type": "FeatureCollection", "features": features}

    return StructureListResponse(
        items=[StructureResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/structures/search", response_model=SearchListResponse)
async def search_structures_endpoint(
    q: str = Query(..., description="Search query (FTS + trigram fuzzy matching)"),
    lang: Literal["ru", "kk", "en"] = "ru",
    type: str | None = None,
    district: str | None = None,
    condition: str | None = None,
    bbox: str | None = Query(None, description="minx,miny,maxx,maxy (EPSG:4326)"),
    limit: int = Query(20, ge=1, le=100),
) -> SearchListResponse:
    """Search structures using combined FTS + trigram fuzzy matching (D-12, D-14).

    Combines PostgreSQL full-text search (ts_rank_cd) with pg_trgm similarity
    for typo-tolerant matching. Results are ordered by blended score:
    fts_rank * 0.7 + greatest(similarity) * 0.3.

    The `lang` parameter selects the tsvector column:
    - ru → search_ts_ru (russian config with stemming)
    - kk → search_ts_kk (simple config — no dedicated Kazakh config)
    - en → search_ts_en (english config with stemming)
    """
    filters = {
        "type": type,
        "district": district,
        "technical_condition": condition,
    }

    try:
        items_with_score, total = await search_structures(
            q=q,
            lang=lang,
            filters=filters,
            bbox=bbox,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    results = []
    for model, score in items_with_score:
        resp = SearchResultResponse.model_validate(model)
        resp.match_score = score
        results.append(resp)

    return SearchListResponse(
        items=results,
        total=total,
        offset=0,
        limit=limit,
    )


@router.get("/structures/{structure_id}", response_model=StructureResponse)
async def get_structure_endpoint(structure_id: uuid.UUID) -> StructureResponse:
    """Retrieve a structure record by ID (D-13).

    Returns 404 if the structure does not exist or has been soft-deleted.
    """
    model = await get_structure(structure_id)
    if model is None or model.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure '{structure_id}' not found",
        )
    return StructureResponse.model_validate(model)


@router.post(
    "/structures",
    response_model=StructureResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_structure_endpoint(
    body: StructureCreate,
    provenance_id: uuid.UUID = Query(..., description="Provenance UUID for this structure"),
    current_user: UserModel = Depends(require_role("engineer")),
) -> StructureResponse:
    """Create a new structure record (D-13).

    Requires engineer+ role per D-12 RBAC retrofit.
    Requires a provenance_id query param.
    Returns 201 with the created structure.
    """
    model = await create_structure(data=body, provenance_id=provenance_id)
    return StructureResponse.model_validate(model)


@router.put("/structures/{structure_id}", response_model=StructureResponse)
async def update_structure_endpoint(
    structure_id: uuid.UUID,
    body: StructureUpdate,
    provenance_id: uuid.UUID = Query(..., description="Provenance UUID for this update"),
    current_user: UserModel = Depends(require_role("engineer")),
) -> StructureResponse:
    """Update a structure with provenance-per-fact tracking (D-13).

    Requires engineer+ role per D-12 RBAC retrofit.

    Creates a new provenance record, expires old structure_facts, and creates
    new facts for each non-None field in the request body.
    Returns 404 if the structure does not exist.
    """
    model = await update_structure(
        structure_id=structure_id,
        data=body,
        provenance_id=provenance_id,
    )
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure '{structure_id}' not found",
        )
    return StructureResponse.model_validate(model)


@router.delete("/structures/{structure_id}")
async def delete_structure_endpoint(
    structure_id: uuid.UUID,
    current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    """Soft delete a structure by setting status='deleted' (D-13).

    Requires admin role per D-12 RBAC retrofit.

    Returns 404 if the structure does not exist.
    """
    deleted = await delete_structure(structure_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure '{structure_id}' not found",
        )
    return {"status": "deleted"}
