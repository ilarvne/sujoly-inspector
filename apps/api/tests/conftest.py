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
# TestClient fixture — patches MinIO in minio_client.py for lifespan startup
# main.py uses MinIOService which imports Minio internally.
# Health endpoint deps (async_session, Redis, Minio) are patched per-test
# ---------------------------------------------------------------------------


@pytest.fixture
def test_client(mock_healthy_minio):
    """FastAPI TestClient with MinIO mocked for lifespan.

    Patches Minio at the MinIOService import path so that lifespan startup
    (which creates a MinIOService) uses the mock client.
    """
    with patch("api.services.minio_client.Minio", mock_healthy_minio):
        from api.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            yield client


# ---------------------------------------------------------------------------
# Fixtures for ingestion tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_xlrd_sheet():
    """Mock xlrd Sheet simulating the 'Корректировка' sheet structure.

    Returns a MagicMock with cell_value(row, col), nrows, ncols attributes.
    Simulates 2 data rows (row_num 1 and 2) with headers in rows 0-6.

    Col layout (Корректировка sheet, 13 cols):
    0: № (float), 1: name, 2: commissioning_year, 3: water_source,
    4: capacity_m3s, 5: total_length_before_km, 6: earthwork_length_km,
    7: lined_length_km, 9: total_length_after_km, 12: notes
    """
    sheet = MagicMock()
    # 9 rows: 7 header rows + 2 data rows
    sheet.nrows = 9
    sheet.ncols = 13

    # Data rows at index 7 and 8
    _data = {
        7: [1.0, "Канал 1", 1973.0, "р. Иртыш", 2.5, 10.0, 5.0, 3.0, "", 8.0, "", "", "", "примечание"],
        8: [2.0, "Канал 2", 1985.0, "р. Нура", 1.8, 15.0, 8.0, 5.0, "", 12.0, "", "", "", ""],
    }

    def cell_value(row_idx, col_idx):
        if row_idx in _data:
            cols = _data[row_idx]
            if col_idx < len(cols):
                return cols[col_idx]
        return ""

    sheet.cell_value = cell_value
    return sheet
