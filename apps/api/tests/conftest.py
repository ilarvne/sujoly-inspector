"""Test configuration for the SuJoly Inspector API."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to python path so `api.*` imports resolve
sys.path.append(str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Mock fixtures for health endpoint dependencies
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_healthy_db():
    """Mock async_session factory that succeeds on execute."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=MagicMock())

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    return MagicMock(return_value=mock_cm)


@pytest.fixture
def mock_failing_db():
    """Mock async_session factory where execute raises."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(side_effect=Exception("DB connection refused"))

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    return MagicMock(return_value=mock_cm)


@pytest.fixture
def mock_healthy_redis():
    """Mock Redis class with from_url returning a healthy client."""
    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()

    mock_class = MagicMock()
    mock_class.from_url.return_value = mock_redis
    return mock_class


@pytest.fixture
def mock_failing_redis():
    """Mock Redis class where ping raises."""
    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(side_effect=Exception("Redis connection refused"))
    mock_redis.aclose = AsyncMock()

    mock_class = MagicMock()
    mock_class.from_url.return_value = mock_redis
    return mock_class


@pytest.fixture
def mock_healthy_minio():
    """Mock Minio class with bucket_exists returning True."""
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = True
    mock_client.make_bucket = MagicMock()

    mock_class = MagicMock(return_value=mock_client)
    return mock_class


@pytest.fixture
def mock_failing_minio():
    """Mock Minio class where bucket_exists raises."""
    mock_client = MagicMock()
    mock_client.bucket_exists.side_effect = Exception("MinIO connection refused")

    mock_class = MagicMock(return_value=mock_client)
    return mock_class


# ---------------------------------------------------------------------------
# TestClient fixture — patches MinIO in main.py for lifespan startup
# Health endpoint deps (async_session, Redis, Minio) are patched per-test
# ---------------------------------------------------------------------------


@pytest.fixture
def test_client(mock_healthy_minio):
    """FastAPI TestClient with MinIO mocked for lifespan."""
    with patch("api.main.Minio", mock_healthy_minio):
        from api.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            yield client
