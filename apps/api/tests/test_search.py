"""Tests for hybrid search endpoint with RRF fusion (AI-03).

Tests cover:
- POST /api/v1/search → 200 with ranked results
- POST /api/v1/search with source_types filter → filtered results
- POST /api/v1/search with empty query → 400
- POST /api/v1/search without auth → 401
- SearchService.hybrid_search RRF fusion logic
- SearchService._fulltext_search with ts_rank
- SearchService._trigram_search with similarity threshold
- SearchService._vector_search returns empty for MVP
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.services.search_service import SearchService


class TestSearchEndpoint:
    """Tests for POST /api/v1/search endpoint."""

    def test_search_returns_results(self, test_client):
        """POST /api/v1/search returns 200 with results list and query echoed."""
        mock_results = [
            {
                "source_type": "structure",
                "source_id": str(uuid.uuid4()),
                "score": 0.0167,
                "snippet": "Канал 1",
                "data": None,
            },
        ]
        with patch(
            "api.services.search_service.search_service.hybrid_search",
            AsyncMock(return_value=mock_results),
        ):
            response = test_client.post(
                "/api/v1/search",
                json={"query": "Канал", "limit": 20, "lang": "ru"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "query" in data
        assert data["query"] == "Канал"
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["source_type"] == "structure"
        assert data["results"][0]["score"] > 0

    def test_search_with_source_types_filter(self, test_client):
        """POST /api/v1/search with source_types filter returns filtered results."""
        struct_id = str(uuid.uuid4())
        mock_results = [
            {
                "source_type": "structure",
                "source_id": struct_id,
                "score": 0.0333,
                "snippet": "Test structure",
                "data": None,
            },
        ]
        with patch(
            "api.services.search_service.search_service.hybrid_search",
            AsyncMock(return_value=mock_results),
        ):
            response = test_client.post(
                "/api/v1/search",
                json={
                    "query": "test",
                    "source_types": ["structure"],
                    "lang": "en",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert all(r["source_type"] == "structure" for r in data["results"])

    def test_search_empty_query_returns_400(self, test_client):
        """POST /api/v1/search with empty query returns 400."""
        response = test_client.post(
            "/api/v1/search",
            json={"query": "   ", "limit": 20},
        )
        assert response.status_code == 400

    def test_search_without_auth_returns_401(self, mock_healthy_minio):
        """POST /api/v1/search without authentication returns 401."""
        mock_db_session = MagicMock()
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_cm = MagicMock()
        mock_db_cm.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_cm.__aexit__ = AsyncMock(return_value=None)
        mock_async_session = MagicMock(return_value=mock_db_cm)

        with patch("api.services.minio_client.Minio", mock_healthy_minio), \
             patch("api.infrastructure.database.async_session", mock_async_session):
            from api.main import app
            from fastapi.testclient import TestClient

            # No dependency override — auth will fail
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/search",
                    json={"query": "test"},
                )
            assert response.status_code == 401

    def test_search_returns_multiple_results_ranked(self, test_client):
        """POST /api/v1/search returns multiple results sorted by RRF score descending."""
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())
        mock_results = [
            {
                "source_type": "structure",
                "source_id": id1,
                "score": 0.0333,
                "snippet": "High score result",
                "data": None,
            },
            {
                "source_type": "structure",
                "source_id": id2,
                "score": 0.0167,
                "snippet": "Lower score result",
                "data": None,
            },
        ]
        with patch(
            "api.services.search_service.search_service.hybrid_search",
            AsyncMock(return_value=mock_results),
        ):
            response = test_client.post(
                "/api/v1/search",
                json={"query": "канал"},
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["score"] >= data["results"][1]["score"]


class TestSearchServiceUnit:
    """Unit tests for SearchService methods with mocked DB."""

    @pytest.fixture
    def service(self):
        """Create a SearchService instance for unit tests."""
        return SearchService()

    @pytest.mark.asyncio
    async def test_vector_search_returns_empty_for_mvp(self, service):
        """SearchService._vector_search returns empty list for MVP (no embedding pipeline)."""
        results = await service._vector_search("test query", 10)
        assert results == []
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_fulltext_search_returns_structured_results(self, service):
        """SearchService._fulltext_search returns list of dicts with source_type, source_id, score."""
        mock_id = uuid.uuid4()
        mock_row = (mock_id, 0.5)
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "api.services.search_service.async_session",
            return_value=mock_cm,
        ):
            results = await service._fulltext_search("Канал", 20, "ru")

        assert len(results) == 1
        assert results[0]["source_type"] == "structure"
        assert results[0]["source_id"] == str(mock_id)
        assert results[0]["score"] == 0.5

    @pytest.mark.asyncio
    async def test_trigram_search_with_similarity_threshold(self, service):
        """SearchService._trigram_search uses similarity > 0.1 threshold."""
        mock_id = uuid.uuid4()
        mock_row = (mock_id, "Канал 1", 0.45)
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "api.services.search_service.async_session",
            return_value=mock_cm,
        ):
            results = await service._trigram_search("Канал", 20)

        assert len(results) == 1
        assert results[0]["source_type"] == "structure"
        assert results[0]["snippet"] == "Канал 1"

    @pytest.mark.asyncio
    async def test_hybrid_search_rrf_fusion(self, service):
        """SearchService.hybrid_search combines results from all methods with RRF fusion."""
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())

        fulltext_results = [
            {"source_type": "structure", "source_id": id1, "score": 0.5, "snippet": ""},
        ]
        trigram_results = [
            {"source_type": "structure", "source_id": id1, "score": 0.8, "snippet": "Канал 1"},
            {"source_type": "structure", "source_id": id2, "score": 0.3, "snippet": "Канал 2"},
        ]

        with patch.object(service, "_fulltext_search", AsyncMock(return_value=fulltext_results)), \
             patch.object(service, "_trigram_search", AsyncMock(return_value=trigram_results)), \
             patch.object(service, "_vector_search", AsyncMock(return_value=[])):
            results = await service.hybrid_search("Канал", limit=10)

        # id1 should rank higher (appears in both fulltext and trigram)
        assert len(results) == 2
        assert results[0]["source_id"] == id1
        assert results[0]["score"] > results[1]["score"]

    @pytest.mark.asyncio
    async def test_hybrid_search_with_source_types_filter(self, service):
        """SearchService.hybrid_search filters by source_types when provided."""
        struct_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())

        fulltext_results = [
            {"source_type": "structure", "source_id": struct_id, "score": 0.5, "snippet": ""},
            {"source_type": "document", "source_id": doc_id, "score": 0.3, "snippet": ""},
        ]

        with patch.object(service, "_fulltext_search", AsyncMock(return_value=fulltext_results)), \
             patch.object(service, "_trigram_search", AsyncMock(return_value=[])), \
             patch.object(service, "_vector_search", AsyncMock(return_value=[])):
            results = await service.hybrid_search(
                "test", limit=10, source_types=["structure"]
            )

        # Only structure results should be returned
        assert len(results) == 1
        assert results[0]["source_type"] == "structure"

    @pytest.mark.asyncio
    async def test_hybrid_search_respects_limit(self, service):
        """SearchService.hybrid_search respects the limit parameter."""
        results_template = [
            {"source_type": "structure", "source_id": str(uuid.uuid4()), "score": 0.5, "snippet": f"Result {i}"}
            for i in range(50)
        ]

        with patch.object(service, "_fulltext_search", AsyncMock(return_value=results_template)), \
             patch.object(service, "_trigram_search", AsyncMock(return_value=[])), \
             patch.object(service, "_vector_search", AsyncMock(return_value=[])):
            results = await service.hybrid_search("test", limit=5)

        assert len(results) <= 5
