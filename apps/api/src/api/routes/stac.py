"""STAC catalog REST endpoints — lightweight in-MinIO catalog for EO evidence.

Provides:
- POST /api/v1/stac/collections: create STAC collection
- GET /api/v1/stac/collections: list collections
- POST /api/v1/stac/collections/{id}/items: add item to collection
- GET /api/v1/stac/collections/{id}/items: list items in collection
- POST /api/v1/stac/search: search across collections
- GET /api/v1/stac/tiles/{z}/{x}/{y}: proxy to TiTiler for COG tiles

All endpoints require viewer+ role. Collection/item creation requires inspector+.
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from api.dependencies.auth import require_role
from api.models.user import UserModel
from api.services.stac_service import StacService

router = APIRouter(prefix="/api/v1/stac", tags=["stac"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CollectionCreate(BaseModel):
    """Request body for creating a STAC collection."""

    id: str = Field(..., description="Unique collection identifier")
    description: str = Field(..., description="Collection description")
    bbox: list[float] = Field(
        default_factory=list,
        description="Bounding box [min_lon, min_lat, max_lon, max_lat]",
    )
    temporal: list[str] = Field(
        default_factory=list,
        description="Temporal extent [start, end] as ISO 8601 strings",
    )


class ItemCreate(BaseModel):
    """Request body for adding a STAC item to a collection."""

    id: str = Field(..., description="Unique item identifier")
    geometry: dict | None = Field(None, description="GeoJSON geometry")
    bbox: list[float] = Field(
        default_factory=list,
        description="Bounding box [min_lon, min_lat, max_lon, max_lat]",
    )
    properties: dict = Field(
        default_factory=dict,
        description="STAC item properties (datetime, etc.)",
    )
    assets: dict = Field(
        default_factory=dict,
        description="STAC item assets (COG hrefs, thumbnails, etc.)",
    )


class SearchRequest(BaseModel):
    """Request body for STAC search."""

    collection_id: str | None = Field(None, description="Filter by collection")
    bbox: list[float] | None = Field(
        None, description="Bounding box filter [min_lon, min_lat, max_lon, max_lat]"
    )
    datetime_range: str | None = Field(
        None, description="Datetime range filter (ISO 8601 interval)"
    )


class TileRequest(BaseModel):
    """Request body for generating a TiTiler URL."""

    cog_path: str = Field(..., description="MinIO object key or URL for the COG file")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_stac_service(request: Request) -> StacService:
    """Get StacService from app state (initialized during lifespan)."""
    return StacService(minio_service=request.app.state.minio)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/collections",
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    body: CollectionCreate,
    request: Request,
    current_user: UserModel = Depends(require_role("inspector")),
) -> dict:
    """Create a STAC collection (inspector+ role).

    Stores collection metadata as JSON in MinIO under
    stac/collections/{collection_id}/collection.json.
    """
    service = _get_stac_service(request)
    return await service.create_collection(
        collection_id=body.id,
        description=body.description,
        bbox=body.bbox,
        temporal=body.temporal,
    )


@router.get("/collections")
async def list_collections(
    request: Request,
    current_user: UserModel = Depends(require_role("viewer")),
) -> dict:
    """List all STAC collections (viewer+ role).

    Returns a list of collection metadata objects from MinIO.
    """
    service = _get_stac_service(request)
    collections = await service.list_collections()
    return {"collections": collections, "total": len(collections)}


@router.post(
    "/collections/{collection_id}/items",
    status_code=status.HTTP_201_CREATED,
)
async def add_item(
    collection_id: str,
    body: ItemCreate,
    request: Request,
    current_user: UserModel = Depends(require_role("inspector")),
) -> dict:
    """Add a STAC item to a collection (inspector+ role).

    Stores item metadata as JSON in MinIO under
    stac/collections/{collection_id}/items/{item_id}.json.
    """
    service = _get_stac_service(request)
    item_dict = {
        "id": body.id,
        "geometry": body.geometry,
        "bbox": body.bbox,
        "properties": body.properties,
        "assets": body.assets,
    }
    try:
        return await service.add_item(collection_id, item_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/collections/{collection_id}/items")
async def list_items(
    collection_id: str,
    request: Request,
    current_user: UserModel = Depends(require_role("viewer")),
) -> dict:
    """List all items in a STAC collection (viewer+ role)."""
    service = _get_stac_service(request)
    items = await service.list_items(collection_id)
    return {"items": items, "total": len(items)}


@router.post("/search")
async def search_items(
    body: SearchRequest,
    request: Request,
    current_user: UserModel = Depends(require_role("viewer")),
) -> dict:
    """Search across STAC collections (viewer+ role).

    Supports filtering by collection, bounding box, and datetime range.
    For MVP: in-memory filtering of items from MinIO.
    """
    service = _get_stac_service(request)
    items = await service.search_items(
        collection_id=body.collection_id,
        bbox=body.bbox,
        datetime_range=body.datetime_range,
    )
    return {"items": items, "total": len(items)}


@router.post("/tiles")
async def get_tile_url(
    body: TileRequest,
    request: Request,
    current_user: UserModel = Depends(require_role("viewer")),
) -> dict:
    """Generate TiTiler URL for a COG asset (viewer+ role).

    Returns a URL template like:
    http://titiler:8081/cog/tiles/{z}/{x}/{y}.png?url={presigned_url}

    The client substitutes {z}, {x}, {y} with tile coordinates.
    """
    service = _get_stac_service(request)
    url = await service.get_titiler_url(body.cog_path)
    return {"tile_url_template": url}
