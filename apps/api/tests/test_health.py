"""Health endpoint tests for the SuJoly Inspector API.

Tests cover:
- /health/live liveness check
- /health/ready readiness check with all services healthy
- /health/ready with DB failure
- /health/ready with Redis failure
- /health/ready with MinIO failure
"""

from unittest.mock import patch


class TestHealthEndpoints:
    """Tests for /health/live and /health/ready endpoints."""

    def test_health_live(self, test_client):
        """GET /health/live returns 200 with {"status": "ok"}."""
        response = test_client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_ready_all_healthy(
        self, test_client, mock_healthy_db, mock_healthy_redis, mock_healthy_minio
    ):
        """GET /health/ready returns 200 when all services are healthy."""
        with (
            patch("api.routes.health.async_session", mock_healthy_db),
            patch("api.routes.health.Redis", mock_healthy_redis),
            patch("api.routes.health.Minio", mock_healthy_minio),
        ):
            response = test_client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            for check in data["checks"].values():
                assert check["status"] == "ok"

    def test_health_ready_db_down(
        self, test_client, mock_failing_db, mock_healthy_redis, mock_healthy_minio
    ):
        """GET /health/ready returns 503 when DB connection fails."""
        with (
            patch("api.routes.health.async_session", mock_failing_db),
            patch("api.routes.health.Redis", mock_healthy_redis),
            patch("api.routes.health.Minio", mock_healthy_minio),
        ):
            response = test_client.get("/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["checks"]["postgres"]["status"] == "error"

    def test_health_ready_redis_down(
        self, test_client, mock_healthy_db, mock_failing_redis, mock_healthy_minio
    ):
        """GET /health/ready returns 503 when Redis ping fails."""
        with (
            patch("api.routes.health.async_session", mock_healthy_db),
            patch("api.routes.health.Redis", mock_failing_redis),
            patch("api.routes.health.Minio", mock_healthy_minio),
        ):
            response = test_client.get("/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["checks"]["redis"]["status"] == "error"

    def test_health_ready_minio_down(
        self, test_client, mock_healthy_db, mock_healthy_redis, mock_failing_minio
    ):
        """GET /health/ready returns 503 when MinIO bucket_exists fails."""
        with (
            patch("api.routes.health.async_session", mock_healthy_db),
            patch("api.routes.health.Redis", mock_healthy_redis),
            patch("api.routes.health.Minio", mock_failing_minio),
        ):
            response = test_client.get("/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["checks"]["minio"]["status"] == "error"
