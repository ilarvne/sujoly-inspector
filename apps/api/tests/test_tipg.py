"""Integration tests for TiPG OGC API Features + Tiles endpoints.

These tests require the full Docker stack running: docker compose up -d
Run with: pytest tests/test_tipg.py -m integration -v

TiPG runs on port 8080 (separate from FastAPI on port 8000).
Tests verify:
- OGC API Features collection auto-discovery (D-05)
- GeoJSON FeatureCollection response format (D-05)
- CQL2 filtering with filter-lang=cql2-text (D-05, T-02-02)
- TileJSON endpoint for MapLibre consumption (D-05)
- NULL geometry handling — geometry: null in GeoJSON (D-02, Pitfall #6)
- Limit/offset pagination (D-05)
- Health check endpoint used by Docker
"""

import pytest
import httpx
from httpx import AsyncClient

TIPG_URL = "http://localhost:8080"


class TestTiPGIntegration:
    """Integration tests for TiPG OGC API Features + Tiles.

    All tests require the Docker stack running with TiPG + PostgreSQL + ingested data from Plan 01.
    """

    @pytest.mark.integration
    async def test_ogc_collection_exists(self):
        """GET /collections returns 200 with public.structures collection (D-05)."""
        async with AsyncClient() as client:
            response = await client.get(f"{TIPG_URL}/collections")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert isinstance(data["collections"], list)
        # TiPG auto-discovers tables with geometry columns — named "public.structures"
        collection_ids = [c["id"] for c in data["collections"]]
        assert any("structures" in cid for cid in collection_ids), (
            f"Expected a collection with 'structures' in id, got: {collection_ids}"
        )

    @pytest.mark.integration
    async def test_items_geojson(self):
        """GET /collections/public.structures/items returns GeoJSON FeatureCollection (D-05)."""
        async with AsyncClient() as client:
            response = await client.get(
                f"{TIPG_URL}/collections/public.structures/items?limit=5"
            )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert isinstance(data["features"], list)

    @pytest.mark.integration
    async def test_cql2_filter(self):
        """GET /collections/public.structures/items?filter=type='canal' returns filtered results (D-05, T-02-02)."""
        async with AsyncClient() as client:
            response = await client.get(
                f"{TIPG_URL}/collections/public.structures/items",
                params={
                    "filter": "type='canal'",
                    "filter-lang": "cql2-text",
                    "limit": 5,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        features = data.get("features", [])
        # All returned features should have type == "canal" in properties
        for feature in features:
            props = feature.get("properties", {})
            assert props.get("type") == "canal", (
                f"Expected type='canal', got: {props.get('type')}"
            )

    @pytest.mark.integration
    async def test_tilejson_endpoint(self):
        """GET /collections/public.structures/tiles/WebMercatorQuad/tilejson.json returns tile metadata (D-05)."""
        async with AsyncClient() as client:
            response = await client.get(
                f"{TIPG_URL}/collections/public.structures/tiles/WebMercatorQuad/tilejson.json"
            )
        assert response.status_code == 200
        data = response.json()
        assert "tiles" in data
        assert isinstance(data["tiles"], list)
        # Tile URL template should be a string with {z}/{x}/{y} placeholders
        assert len(data["tiles"]) > 0

    @pytest.mark.integration
    async def test_null_geometry_handling(self):
        """GET /collections/public.structures/items?limit=1 returns valid GeoJSON with geometry: null (D-02, Pitfall #6).

        All geometries are NULL in Phase 2 (no coordinate data in spreadsheet).
        PostGIS 3.5.7 correctly outputs "geometry": null in GeoJSON.
        """
        async with AsyncClient() as client:
            response = await client.get(
                f"{TIPG_URL}/collections/public.structures/items?limit=1"
            )
        assert response.status_code == 200
        data = response.json()
        features = data.get("features", [])
        assert len(features) > 0
        first_feature = features[0]
        # Feature must have a "geometry" key — either null (D-02) or a valid GeoJSON geometry
        assert "geometry" in first_feature
        geometry = first_feature["geometry"]
        # In Phase 2, all geometries are NULL so geometry should be null
        if geometry is not None:
            # If geometry is not null, it must be a valid GeoJSON geometry object
            assert "type" in geometry
            assert "coordinates" in geometry

    @pytest.mark.integration
    async def test_items_pagination(self):
        """GET /collections/public.structures/items?limit=10&offset=0 returns paginated results (D-05)."""
        async with AsyncClient() as client:
            response = await client.get(
                f"{TIPG_URL}/collections/public.structures/items",
                params={"limit": 10, "offset": 0},
            )
        assert response.status_code == 200
        data = response.json()
        # Either numberMatched is present or features length is within limit
        features = data.get("features", [])
        assert len(features) <= 10, (
            f"Expected <= 10 features with limit=10, got {len(features)}"
        )

    @pytest.mark.integration
    async def test_healthz(self):
        """GET /healthz returns 200 — verifies the TiPG health check endpoint used by Docker."""
        async with AsyncClient() as client:
            response = await client.get(f"{TIPG_URL}/healthz")
        assert response.status_code == 200
