"""Tests for MinIO presigned URL endpoints.

Tests cover:
- POST /api/v1/minio/presign → 200 with presigned upload URL
- GET /api/v1/minio/presign/{object_name} → 200 with presigned download URL
- presigned_roundtrip → upload and download URLs are different strings (SC-3)
"""

from unittest.mock import MagicMock, patch


class TestMinIOEndpoints:
    """Tests for /api/v1/minio/presign endpoints."""

    def _mock_minio_service(self):
        """Create a mock MinIOService on app.state."""
        mock_service = MagicMock()
        mock_service.presigned_upload_url.return_value = (
            "http://minio:9000/sujoly-documents/test/file.pdf?X-Amz-Upload=true"
        )
        mock_service.presigned_download_url.return_value = (
            "http://minio:9000/sujoly-documents/test/file.pdf?X-Amz-Download=true"
        )
        mock_service.ensure_bucket = MagicMock()
        return mock_service

    def test_presign_upload(self, test_client):
        """POST /api/v1/minio/presign returns 200 with non-empty presigned_url."""
        mock_service = self._mock_minio_service()
        test_client.app.state.minio = mock_service

        response = test_client.post(
            "/api/v1/minio/presign",
            json={
                "bucket": "sujoly-documents",
                "object_name": "test/file.pdf",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "presigned_url" in data
        assert len(data["presigned_url"]) > 0
        assert "expires_in_seconds" in data
        mock_service.presigned_upload_url.assert_called_once_with(
            "sujoly-documents", "test/file.pdf"
        )

    def test_presign_download(self, test_client):
        """GET /api/v1/minio/presign/{object_name} returns 200 with non-empty presigned_url."""
        mock_service = self._mock_minio_service()
        test_client.app.state.minio = mock_service

        response = test_client.get(
            "/api/v1/minio/presign/test/file.pdf",
            params={"bucket": "sujoly-documents"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "presigned_url" in data
        assert len(data["presigned_url"]) > 0
        assert "expires_in_seconds" in data
        mock_service.presigned_download_url.assert_called_once_with(
            "sujoly-documents", "test/file.pdf"
        )

    def test_presigned_roundtrip(self, test_client):
        """Upload URL and download URL are different strings (SC-3)."""
        mock_service = self._mock_minio_service()
        test_client.app.state.minio = mock_service

        # Get upload URL
        upload_resp = test_client.post(
            "/api/v1/minio/presign",
            json={"bucket": "sujoly-documents", "object_name": "test/roundtrip.pdf"},
        )
        assert upload_resp.status_code == 200
        upload_url = upload_resp.json()["presigned_url"]

        # Get download URL
        download_resp = test_client.get(
            "/api/v1/minio/presign/test/roundtrip.pdf",
            params={"bucket": "sujoly-documents"},
        )
        assert download_resp.status_code == 200
        download_url = download_resp.json()["presigned_url"]

        # URLs should be different (one is PUT, other is GET)
        assert upload_url != download_url
