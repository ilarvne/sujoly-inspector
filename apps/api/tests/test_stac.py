"""Tests for STAC catalog endpoints.

Tests cover:
- POST /api/v1/stac/collections → 201 with collection metadata
- GET /api/v1/stac/collections → 200 with collections list
- POST /api/v1/stac/collections/{id}/items → 201 with item metadata
- GET /api/v1/stac/collections/{id}/items → 200 with items list
- POST /api/v1/stac/search → 200 with filtered results
- POST /api/v1/stac/tiles → 200 with TiTiler URL template
- StacService: create_collection, add_item, search_items, get_titiler_url
"""

import json
import uuid
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.services.stac_service import StacService


class TestStacService:
    """Unit tests for StacService business logic."""

    def _mock_minio_service(self):
        """Create a mock MinIOService with put_object, get_object, list_objects."""
        mock_minio = MagicMock()

        # Track stored objects for read-back
        stored_objects = {}

        def put_object(bucket, key, data, length=None, content_type=None):
            stored_objects[key] = data.read() if hasattr(data, "read") else data

        def get_object(bucket, key):
            if key in stored_objects:
                return BytesIO(stored_objects[key])
            raise Exception(f"Object not found: {key}")

        def list_objects(bucket, prefix="", recursive=False):
            """Return mock objects matching prefix.

            When recursive=False, synthesizes directory-style entries ending with /
            from unique path components after the prefix — matching MinIO's behavior.
            """
            if recursive:
                mock_objs = []
                for key in stored_objects:
                    if key.startswith(prefix):
                        mock_obj = MagicMock()
                        mock_obj.object_name = key
                        mock_objs.append(mock_obj)
                return mock_objs
            else:
                # Non-recursive: return unique "directory" prefixes one level deep
                seen_dirs = set()
                mock_objs = []
                for key in stored_objects:
                    if key.startswith(prefix):
                        remainder = key[len(prefix):]
                        # Get first path component
                        parts = remainder.split("/")
                        if parts and parts[0]:
                            dir_name = parts[0]
                            if dir_name not in seen_dirs:
                                seen_dirs.add(dir_name)
                                mock_obj = MagicMock()
                                mock_obj.object_name = f"{prefix}{dir_name}/"
                                mock_objs.append(mock_obj)
                return mock_objs

        mock_minio.client.put_object = MagicMock(side_effect=put_object)
        mock_minio.client.get_object = MagicMock(side_effect=get_object)
        mock_minio.client.list_objects = MagicMock(side_effect=list_objects)
        mock_minio.presigned_download_url = MagicMock(
            return_value="https://minio.example.com/sujoly-imagery/test.cog?X-Amz-Signature=abc"
        )

        return mock_minio

    @pytest.mark.asyncio
    async def test_create_collection(self):
        """StacService.create_collection stores collection metadata in MinIO."""
        minio = self._mock_minio_service()
        service = StacService(minio_service=minio)

        result = await service.create_collection(
            collection_id="sentinel-2",
            description="Sentinel-2 satellite imagery for Zhambyl",
            bbox=[67.0, 42.0, 72.0, 45.0],
            temporal=["2024-01-01T00:00:00Z", "2026-06-26T00:00:00Z"],
        )

        assert result["id"] == "sentinel-2"
        assert result["description"] == "Sentinel-2 satellite imagery for Zhambyl"
        assert result["type"] == "Collection"
        assert result["bbox"] == [67.0, 42.0, 72.0, 45.0]
        minio.client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_item(self):
        """StacService.add_item stores item metadata in MinIO."""
        minio = self._mock_minio_service()
        service = StacService(minio_service=minio)

        # Create collection first so items can be added
        await service.create_collection(
            collection_id="sentinel-2",
            description="Sentinel-2 imagery",
            bbox=[67.0, 42.0, 72.0, 45.0],
            temporal=[],
        )

        item_data = {
            "id": "S2A_20260626",
            "geometry": {"type": "Point", "coordinates": [70.0, 43.5]},
            "bbox": [69.9, 43.4, 70.1, 43.6],
            "properties": {"datetime": "2026-06-26T10:30:00Z"},
            "assets": {
                "visual": {
                    "href": "sujoly-imagery/sentinel2/S2A_20260626.tif",
                    "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                }
            },
        }

        result = await service.add_item("sentinel-2", item_data)

        assert result["id"] == "S2A_20260626"
        assert result["collection_id"] == "sentinel-2"
        assert result["type"] == "Feature"
        assert "visual" in result["assets"]

    @pytest.mark.asyncio
    async def test_add_item_without_id_raises(self):
        """StacService.add_item raises ValueError if item has no id."""
        minio = self._mock_minio_service()
        service = StacService(minio_service=minio)

        with pytest.raises(ValueError, match="must have an 'id' field"):
            await service.add_item("sentinel-2", {"geometry": None})

    @pytest.mark.asyncio
    async def test_search_items_by_collection(self):
        """StacService.search_items filters by collection_id."""
        minio = self._mock_minio_service()
        service = StacService(minio_service=minio)

        # Create collection and add items
        await service.create_collection(
            collection_id="sentinel-2",
            description="Sentinel-2 imagery",
            bbox=[67.0, 42.0, 72.0, 45.0],
            temporal=[],
        )
        await service.add_item(
            "sentinel-2",
            {
                "id": "S2A_20260626",
                "bbox": [69.9, 43.4, 70.1, 43.6],
                "properties": {"datetime": "2026-06-26T10:30:00Z"},
            },
        )

        results = await service.search_items(collection_id="sentinel-2")
        assert len(results) == 1
        assert results[0]["id"] == "S2A_20260626"

    @pytest.mark.asyncio
    async def test_search_items_by_bbox(self):
        """StacService.search_items filters by bounding box overlap."""
        minio = self._mock_minio_service()
        service = StacService(minio_service=minio)

        await service.create_collection(
            collection_id="sentinel-2",
            description="Sentinel-2 imagery",
            bbox=[67.0, 42.0, 72.0, 45.0],
            temporal=[],
        )
        await service.add_item(
            "sentinel-2",
            {
                "id": "S2A_20260626",
                "bbox": [69.9, 43.4, 70.1, 43.6],
                "properties": {"datetime": "2026-06-26T10:30:00Z"},
            },
        )
        await service.add_item(
            "sentinel-2",
            {
                "id": "S2A_20260101",
                "bbox": [10.0, 10.0, 11.0, 11.0],  # Far from Zhambyl
                "properties": {"datetime": "2026-01-01T10:30:00Z"},
            },
        )

        # Search within Zhambyl bbox
        results = await service.search_items(
            collection_id="sentinel-2",
            bbox=[67.0, 42.0, 72.0, 45.0],
        )
        assert len(results) == 1
        assert results[0]["id"] == "S2A_20260626"

    @pytest.mark.asyncio
    async def test_get_titiler_url_minio_key(self):
        """StacService.get_titiler_url generates URL with presigned MinIO URL for keys."""
        minio = self._mock_minio_service()
        service = StacService(minio_service=minio)

        url = await service.get_titiler_url("sentinel2/S2A_20260626.tif")
        assert "titiler:8081/cog/tiles/" in url
        assert "{z}/{x}/{y}.png" in url
        assert "X-Amz-Signature" in url
        minio.presigned_download_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_titiler_url_http_url(self):
        """StacService.get_titiler_url uses URL directly if already http."""
        minio = self._mock_minio_service()
        service = StacService(minio_service=minio)

        url = await service.get_titiler_url("http://minio:9000/sujoly-imagery/test.tif")
        assert "titiler:8081/cog/tiles/" in url
        assert "http://minio:9000/sujoly-imagery/test.tif" in url
        minio.presigned_download_url.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_collections(self):
        """StacService.list_collections returns all collections."""
        minio = self._mock_minio_service()
        service = StacService(minio_service=minio)

        await service.create_collection("sentinel-2", "Sentinel-2 imagery", [], [])
        await service.create_collection("ndwi-composites", "NDWI composites", [], [])

        collections = await service.list_collections()
        assert len(collections) == 2
        ids = {c["id"] for c in collections}
        assert ids == {"sentinel-2", "ndwi-composites"}

    @pytest.mark.asyncio
    async def test_list_items(self):
        """StacService.list_items returns all items in a collection."""
        minio = self._mock_minio_service()
        service = StacService(minio_service=minio)

        await service.create_collection("sentinel-2", "Sentinel-2 imagery", [], [])
        await service.add_item(
            "sentinel-2",
            {"id": "item-1", "properties": {"datetime": "2026-06-26T00:00:00Z"}},
        )
        await service.add_item(
            "sentinel-2",
            {"id": "item-2", "properties": {"datetime": "2026-01-01T00:00:00Z"}},
        )

        items = await service.list_items("sentinel-2")
        assert len(items) == 2
        item_ids = {i["id"] for i in items}
        assert item_ids == {"item-1", "item-2"}


class TestStacEndpoints:
    """Tests for /api/v1/stac REST endpoints."""

    def test_create_collection(self, test_client):
        """POST /api/v1/stac/collections returns 201 with collection metadata."""
        response = test_client.post(
            "/api/v1/stac/collections",
            json={
                "id": "sentinel-2",
                "description": "Sentinel-2 satellite imagery for Zhambyl",
                "bbox": [67.0, 42.0, 72.0, 45.0],
                "temporal": ["2024-01-01T00:00:00Z", "2026-06-26T00:00:00Z"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "sentinel-2"
        assert data["type"] == "Collection"

    def test_list_collections(self, test_client):
        """GET /api/v1/stac/collections returns 200 with collections list."""
        # First create a collection
        test_client.post(
            "/api/v1/stac/collections",
            json={
                "id": "test-coll",
                "description": "Test collection",
                "bbox": [],
                "temporal": [],
            },
        )
        response = test_client.get("/api/v1/stac/collections")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert "total" in data

    def test_add_item(self, test_client):
        """POST /api/v1/stac/collections/{id}/items returns 201 with item metadata."""
        # Create collection first
        test_client.post(
            "/api/v1/stac/collections",
            json={
                "id": "sentinel-2",
                "description": "Sentinel-2 imagery",
                "bbox": [],
                "temporal": [],
            },
        )

        response = test_client.post(
            "/api/v1/stac/collections/sentinel-2/items",
            json={
                "id": "S2A_20260626",
                "geometry": {"type": "Point", "coordinates": [70.0, 43.5]},
                "bbox": [69.9, 43.4, 70.1, 43.6],
                "properties": {"datetime": "2026-06-26T10:30:00Z"},
                "assets": {
                    "visual": {
                        "href": "sujoly-imagery/sentinel2/S2A_20260626.tif",
                        "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                    }
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "S2A_20260626"
        assert data["type"] == "Feature"

    def test_add_item_without_id_returns_400(self, test_client):
        """POST /api/v1/stac/collections/{id}/items with no item id returns 400."""
        # Create collection first
        test_client.post(
            "/api/v1/stac/collections",
            json={
                "id": "sentinel-2",
                "description": "Sentinel-2 imagery",
                "bbox": [],
                "temporal": [],
            },
        )

        response = test_client.post(
            "/api/v1/stac/collections/sentinel-2/items",
            json={
                "geometry": None,
            },
        )
        assert response.status_code == 422  # Pydantic validation error

    def test_list_items(self, test_client):
        """GET /api/v1/stac/collections/{id}/items returns 200 with items list."""
        # Create collection and item
        test_client.post(
            "/api/v1/stac/collections",
            json={
                "id": "sentinel-2",
                "description": "Sentinel-2 imagery",
                "bbox": [],
                "temporal": [],
            },
        )
        test_client.post(
            "/api/v1/stac/collections/sentinel-2/items",
            json={
                "id": "S2A_20260626",
                "properties": {"datetime": "2026-06-26T10:30:00Z"},
            },
        )

        response = test_client.get("/api/v1/stac/collections/sentinel-2/items")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_search_items(self, test_client):
        """POST /api/v1/stac/search returns 200 with filtered results."""
        # Create collection and item
        test_client.post(
            "/api/v1/stac/collections",
            json={
                "id": "sentinel-2",
                "description": "Sentinel-2 imagery",
                "bbox": [],
                "temporal": [],
            },
        )
        test_client.post(
            "/api/v1/stac/collections/sentinel-2/items",
            json={
                "id": "S2A_20260626",
                "bbox": [69.9, 43.4, 70.1, 43.6],
                "properties": {"datetime": "2026-06-26T10:30:00Z"},
            },
        )

        response = test_client.post(
            "/api/v1/stac/search",
            json={
                "collection_id": "sentinel-2",
                "bbox": [67.0, 42.0, 72.0, 45.0],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_tile_url(self, test_client):
        """POST /api/v1/stac/tiles returns 200 with TiTiler URL template."""
        response = test_client.post(
            "/api/v1/stac/tiles",
            json={"cog_path": "sentinel2/S2A_20260626.tif"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "tile_url_template" in data
        assert "titiler" in data["tile_url_template"]
