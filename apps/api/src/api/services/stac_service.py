"""STAC catalog service — lightweight in-MinIO catalog for EO evidence.

Provides:
- create_collection: create a STAC collection in MinIO
- add_item: add a STAC item to a collection in MinIO
- search_items: search items by collection, bbox, datetime
- get_titiler_url: generate TiTiler URL for a COG asset

For hackathon MVP: STAC items stored as JSON in MinIO.
No separate STAC server needed — TiTiler reads COGs directly.
Can be upgraded to a full STAC server (e.g., stac-fastapi) for production.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import structlog
from pydantic import BaseModel, Field

from api.services.minio_client import MinIOService

logger = structlog.get_logger(__name__)

IMAGERY_BUCKET = "sujoly-imagery"


class StacCollection(BaseModel):
    """Lightweight STAC Collection representation."""

    id: str
    description: str
    bbox: list[float] = Field(default_factory=list)
    temporal: list[str] = Field(default_factory=list)
    type: str = "Collection"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StacItem(BaseModel):
    """Lightweight STAC Item representation."""

    id: str
    collection_id: str
    geometry: dict | None = None
    bbox: list[float] = Field(default_factory=list)
    properties: dict = Field(default_factory=dict)
    assets: dict = Field(default_factory=dict)
    type: str = "Feature"


class StacService:
    """STAC catalog service — stores collections and items as JSON in MinIO.

    MinIO object layout:
    - stac/collections/{collection_id}/collection.json
    - stac/collections/{collection_id}/items/{item_id}.json
    """

    def __init__(self, minio_service: MinIOService):
        self.minio = minio_service

    async def create_collection(
        self,
        collection_id: str,
        description: str,
        bbox: list[float],
        temporal: list[str],
    ) -> dict:
        """Create a STAC collection in MinIO.

        Stored as JSON at stac/collections/{collection_id}/collection.json
        in the sujoly-imagery bucket.
        """
        collection = StacCollection(
            id=collection_id,
            description=description,
            bbox=bbox,
            temporal=temporal,
        )
        object_key = f"stac/collections/{collection_id}/collection.json"
        data = json.dumps(collection.model_dump(), ensure_ascii=False).encode("utf-8")

        from io import BytesIO

        self.minio.client.put_object(
            IMAGERY_BUCKET,
            object_key,
            BytesIO(data),
            length=len(data),
            content_type="application/json",
        )

        logger.info(
            "stac_collection_created",
            collection_id=collection_id,
            object_key=object_key,
        )
        return collection.model_dump()

    async def add_item(self, collection_id: str, item: dict) -> dict:
        """Add a STAC item to a collection.

        Item must follow STAC Item spec minimally:
        - id, geometry, bbox, properties.datetime
        - assets with COG hrefs pointing to MinIO

        Stored at stac/collections/{collection_id}/items/{item_id}.json
        """
        item_id = item.get("id")
        if not item_id:
            raise ValueError("STAC item must have an 'id' field")

        stac_item = StacItem(
            id=item_id,
            collection_id=collection_id,
            geometry=item.get("geometry"),
            bbox=item.get("bbox", []),
            properties=item.get("properties", {}),
            assets=item.get("assets", {}),
        )

        object_key = f"stac/collections/{collection_id}/items/{item_id}.json"
        data = json.dumps(stac_item.model_dump(), ensure_ascii=False).encode("utf-8")

        from io import BytesIO

        self.minio.client.put_object(
            IMAGERY_BUCKET,
            object_key,
            BytesIO(data),
            length=len(data),
            content_type="application/json",
        )

        logger.info(
            "stac_item_added",
            collection_id=collection_id,
            item_id=item_id,
            object_key=object_key,
        )
        return stac_item.model_dump()

    async def search_items(
        self,
        collection_id: str | None = None,
        bbox: list[float] | None = None,
        datetime_range: str | None = None,
    ) -> list[dict]:
        """Search STAC items by collection, bbox, datetime.

        For MVP: list items from MinIO and filter in-memory.
        Production upgrade: use PostGIS spatial queries.
        """
        items = []

        # Determine which collections to search
        collections_to_search = []
        if collection_id:
            collections_to_search = [collection_id]
        else:
            # List all collection directories
            prefix = "stac/collections/"
            objects = self.minio.client.list_objects(
                IMAGERY_BUCKET, prefix=prefix, recursive=False
            )
            for obj in objects:
                # Extract collection_id from path: stac/collections/{id}/
                parts = obj.object_name.replace(prefix, "").split("/")
                if parts and parts[0]:
                    collections_to_search.append(parts[0])

        # Collect items from each collection
        for coll_id in collections_to_search:
            item_prefix = f"stac/collections/{coll_id}/items/"
            objects = self.minio.client.list_objects(
                IMAGERY_BUCKET, prefix=item_prefix, recursive=True
            )
            for obj in objects:
                if not obj.object_name.endswith(".json"):
                    continue
                response = self.minio.client.get_object(IMAGERY_BUCKET, obj.object_name)
                try:
                    item_data = json.loads(response.read().decode("utf-8"))
                finally:
                    response.close()
                    if hasattr(response, "release_conn"):
                        response.release_conn()

                # Apply bbox filter if specified
                if bbox and item_data.get("bbox"):
                    item_bbox = item_data["bbox"]
                    # Simple overlap check: [min_lon, min_lat, max_lon, max_lat]
                    if len(item_bbox) == 4 and len(bbox) == 4:
                        if not (
                            item_bbox[0] <= bbox[2]
                            and item_bbox[2] >= bbox[0]
                            and item_bbox[1] <= bbox[3]
                            and item_bbox[3] >= bbox[1]
                        ):
                            continue

                # Apply datetime filter if specified (MVP: simple string match)
                if datetime_range and item_data.get("properties", {}).get("datetime"):
                    # For MVP: just include items with datetime property
                    # Production: parse ISO 8601 intervals
                    pass

                items.append(item_data)

        logger.info(
            "stac_search_completed",
            collection_id=collection_id,
            result_count=len(items),
        )
        return items

    async def get_titiler_url(self, cog_path: str) -> str:
        """Generate TiTiler URL for a COG asset.

        Returns URL like:
        http://titiler:8081/cog/tiles/{z}/{x}/{y}.png?url={cog_path}

        Args:
            cog_path: MinIO object key or URL for the COG file.
                      If it's a MinIO key, we generate a presigned URL.
        """
        # If cog_path looks like a MinIO key (not a URL), generate presigned URL
        if not cog_path.startswith("http"):
            presigned = self.minio.presigned_download_url(IMAGERY_BUCKET, cog_path)
            encoded_path = presigned
        else:
            encoded_path = cog_path

        titiler_base = "http://titiler:8081"
        return f"{titiler_base}/cog/tiles/{{z}}/{{x}}/{{y}}.png?url={encoded_path}"

    async def list_collections(self) -> list[dict]:
        """List all STAC collections from MinIO."""
        collections = []
        prefix = "stac/collections/"
        objects = self.minio.client.list_objects(
            IMAGERY_BUCKET, prefix=prefix, recursive=False
        )
        for obj in objects:
            # Each collection dir should have a collection.json
            coll_prefix = obj.object_name
            if not coll_prefix.endswith("/"):
                continue
            coll_id = coll_prefix.replace(prefix, "").rstrip("/")
            collection_key = f"{coll_prefix}collection.json"
            try:
                response = self.minio.client.get_object(IMAGERY_BUCKET, collection_key)
                try:
                    coll_data = json.loads(response.read().decode("utf-8"))
                finally:
                    response.close()
                    if hasattr(response, "release_conn"):
                        response.release_conn()
                collections.append(coll_data)
            except Exception:
                # Collection metadata file might not exist yet
                logger.warning("stac_collection_missing_metadata", collection_id=coll_id)

        return collections

    async def list_items(self, collection_id: str) -> list[dict]:
        """List all items in a collection."""
        items = []
        item_prefix = f"stac/collections/{collection_id}/items/"
        objects = self.minio.client.list_objects(
            IMAGERY_BUCKET, prefix=item_prefix, recursive=True
        )
        for obj in objects:
            if not obj.object_name.endswith(".json"):
                continue
            response = self.minio.client.get_object(IMAGERY_BUCKET, obj.object_name)
            try:
                item_data = json.loads(response.read().decode("utf-8"))
            finally:
                response.close()
                if hasattr(response, "release_conn"):
                    response.release_conn()
            items.append(item_data)

        return items
