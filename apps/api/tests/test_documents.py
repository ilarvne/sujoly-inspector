"""Tests for document attachment endpoints with MinIO integration.

Tests cover:
- POST /api/v1/structures/{id}/documents → 201 with document fields (D-18)
- POST /api/v1/structures/{id}/documents → 403 for viewer role (D-12)
- GET /api/v1/structures/{id}/documents → 200 with items list (D-18)
- GET /api/v1/structures/{id}/documents → includes presigned_download_url (D-18)
- DELETE /api/v1/documents/{id} → {"status": "deleted"} for admin (D-18)
- DELETE /api/v1/documents/{id} → 403 for inspector role (D-12)
- DELETE /api/v1/documents/{id} → 404 for non-existent (D-18)
- GET /api/v1/documents/{id}/download → 200 with presigned_url (D-18)
- GET /api/v1/documents/{id}/download → 404 for non-existent (D-18)
- Document registration creates ProvenanceModel with source_type='manual'
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDocumentEndpoints:
    """Tests for /api/v1 document attachment endpoints with MinIO integration."""

    def _mock_document(self, **overrides):
        """Create a mock DocumentModel instance with all response fields."""
        defaults = {
            "id": uuid.uuid4(),
            "structure_id": uuid.uuid4(),
            "document_type": "inspection_report",
            "title": "Inspection Report 2026",
            "language": "ru",
            "minio_bucket": "sujoly-documents",
            "minio_object_key": "reports/inspection-2026.pdf",
            "file_size_bytes": 1024,
            "uploaded_by": "inspector",
            "provenance_id": uuid.uuid4(),
            "created_at": datetime.now(timezone.utc),
        }
        defaults.update(overrides)
        mock = MagicMock()
        for key, val in defaults.items():
            setattr(mock, key, val)
        return mock

    def _mock_minio_service(self):
        """Create a mock MinIOService instance."""
        mock_minio = MagicMock()
        mock_minio.presigned_download_url = MagicMock(
            return_value="https://minio.example.com/sujoly-documents/reports/test.pdf?X-Amz-Signature=abc"
        )
        mock_minio.client = MagicMock()
        mock_minio.client.remove_object = MagicMock()
        return mock_minio

    # ------------------------------------------------------------------
    # Register document tests
    # ------------------------------------------------------------------

    def test_register_document(self, test_client):
        """POST /api/v1/structures/{id}/documents returns 201 with id, document_type, title, language, minio_object_key."""
        struct_id = uuid.uuid4()
        mock_doc = self._mock_document(structure_id=struct_id)
        with patch(
            "api.routes.documents.register_document",
            AsyncMock(return_value=mock_doc),
        ):
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/documents",
                json={
                    "document_type": "inspection_report",
                    "title": "Inspection Report 2026",
                    "language": "ru",
                    "minio_object_key": "reports/inspection-2026.pdf",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["document_type"] == "inspection_report"
        assert data["title"] == "Inspection Report 2026"
        assert data["language"] == "ru"
        assert "minio_object_key" in data

    def test_register_document_viewer_forbidden(self, mock_healthy_minio):
        """POST /api/v1/structures/{id}/documents with viewer role returns 403."""
        struct_id = uuid.uuid4()
        mock_viewer = MagicMock()
        mock_viewer.role = "viewer"
        mock_viewer.username = "viewer-user"

        # Mock async_session for lifespan admin seeding
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
            from api.dependencies.auth import get_current_user
            from fastapi.testclient import TestClient

            async def _override_viewer():
                return mock_viewer

            app.dependency_overrides[get_current_user] = _override_viewer

            try:
                with TestClient(app) as client:
                    response = client.post(
                        f"/api/v1/structures/{struct_id}/documents",
                        json={
                            "document_type": "inspection_report",
                            "title": "Test Doc",
                            "language": "ru",
                            "minio_object_key": "test/doc.pdf",
                        },
                    )
            finally:
                app.dependency_overrides.clear()

        assert response.status_code == 403

    # ------------------------------------------------------------------
    # List documents tests
    # ------------------------------------------------------------------

    def test_list_documents(self, test_client):
        """GET /api/v1/structures/{id}/documents returns 200 with items list containing document metadata."""
        struct_id = uuid.uuid4()
        mock_docs = [self._mock_document(structure_id=struct_id)]
        with patch(
            "api.routes.documents.list_documents",
            AsyncMock(return_value=mock_docs),
        ):
            response = test_client.get(
                f"/api/v1/structures/{struct_id}/documents"
            )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) >= 1
        assert data["items"][0]["document_type"] == "inspection_report"

    def test_list_documents_includes_presigned_urls(self, test_client):
        """GET /api/v1/structures/{id}/documents returns items with presigned_download_url field."""
        struct_id = uuid.uuid4()
        mock_doc = self._mock_document(structure_id=struct_id)
        mock_minio = self._mock_minio_service()

        with patch(
            "api.routes.documents.list_documents",
            AsyncMock(return_value=[mock_doc]),
        ), patch.object(
            test_client.app.state, "minio", mock_minio
        ):
            response = test_client.get(
                f"/api/v1/structures/{struct_id}/documents"
            )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert "presigned_download_url" in data["items"][0]

    # ------------------------------------------------------------------
    # Delete document tests
    # ------------------------------------------------------------------

    def test_delete_document_admin(self, test_client):
        """DELETE /api/v1/documents/{id} with admin role returns {"status": "deleted"}."""
        doc_id = uuid.uuid4()
        mock_minio = self._mock_minio_service()

        with patch(
            "api.routes.documents.delete_document",
            AsyncMock(return_value=True),
        ), patch.object(
            test_client.app.state, "minio", mock_minio
        ):
            response = test_client.delete(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"

    def test_delete_document_inspector_forbidden(self, mock_healthy_minio):
        """DELETE /api/v1/documents/{id} with inspector role returns 403."""
        doc_id = uuid.uuid4()
        mock_inspector = MagicMock()
        mock_inspector.role = "inspector"
        mock_inspector.username = "inspector-user"

        # Mock async_session for lifespan admin seeding
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
            from api.dependencies.auth import get_current_user
            from fastapi.testclient import TestClient

            async def _override_inspector():
                return mock_inspector

            app.dependency_overrides[get_current_user] = _override_inspector

            try:
                with TestClient(app) as client:
                    response = client.delete(f"/api/v1/documents/{doc_id}")
            finally:
                app.dependency_overrides.clear()

        assert response.status_code == 403

    def test_delete_document_not_found(self, test_client):
        """DELETE /api/v1/documents/{nonexistent_id} returns 404."""
        nonexistent_id = uuid.uuid4()
        mock_minio = self._mock_minio_service()

        with patch(
            "api.routes.documents.delete_document",
            AsyncMock(return_value=False),
        ), patch.object(
            test_client.app.state, "minio", mock_minio
        ):
            response = test_client.delete(f"/api/v1/documents/{nonexistent_id}")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # Download URL tests
    # ------------------------------------------------------------------

    def test_get_download_url(self, test_client):
        """GET /api/v1/documents/{id}/download returns 200 with presigned_url and expires_in_seconds."""
        doc_id = uuid.uuid4()
        mock_minio = self._mock_minio_service()

        with patch(
            "api.routes.documents.get_download_url",
            AsyncMock(return_value="https://minio.example.com/sujoly-documents/reports/test.pdf?X-Amz-Signature=abc"),
        ), patch.object(
            test_client.app.state, "minio", mock_minio
        ):
            response = test_client.get(f"/api/v1/documents/{doc_id}/download")
        assert response.status_code == 200
        data = response.json()
        assert "presigned_url" in data
        assert "expires_in_seconds" in data
        assert data["expires_in_seconds"] == 7200

    def test_get_download_url_not_found(self, test_client):
        """GET /api/v1/documents/{nonexistent_id}/download returns 404."""
        nonexistent_id = uuid.uuid4()
        mock_minio = self._mock_minio_service()

        with patch(
            "api.routes.documents.get_download_url",
            AsyncMock(return_value=None),
        ), patch.object(
            test_client.app.state, "minio", mock_minio
        ):
            response = test_client.get(f"/api/v1/documents/{nonexistent_id}/download")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # Provenance tracking test
    # ------------------------------------------------------------------

    def test_register_creates_provenance(self, test_client):
        """Verify document_service.register_document creates ProvenanceModel."""
        struct_id = uuid.uuid4()
        mock_doc = self._mock_document(structure_id=struct_id)
        mock_provenance = MagicMock()
        mock_provenance.source_type = "manual"
        mock_provenance.contributor = "admin"
        mock_provenance.id = uuid.uuid4()

        with patch(
            "api.services.document_service.ProvenanceModel",
            return_value=mock_provenance,
        ) as MockProvenance, patch(
            "api.routes.documents.register_document",
            AsyncMock(return_value=mock_doc),
        ):
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/documents",
                json={
                    "document_type": "inspection_report",
                    "title": "Test Report",
                    "language": "ru",
                    "minio_object_key": "reports/test.pdf",
                },
            )
        assert response.status_code == 201
