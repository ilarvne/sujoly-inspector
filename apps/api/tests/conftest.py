"""Test configuration for the SuJoly Inspector API."""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
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
def test_client(mock_healthy_minio, mock_user):
    """FastAPI TestClient with MinIO and auth mocked for lifespan.

    Patches Minio at the MinIOService import path so that lifespan startup
    (which creates a MinIOService) uses the mock client. Also patches
    async_session for admin seeding. Uses app.dependency_overrides for
    get_current_user to avoid MagicMock signature issues with FastAPI.
    """
    # Mock async_session context manager for admin seeding in lifespan
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

        # Override get_current_user dependency with a function that
        # returns mock_user — FastAPI dependency_overrides handles signature
        # correctly unlike MagicMock-based patching.
        async def _override_get_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = _override_get_current_user

        try:
            with TestClient(app) as client:
                yield client
        finally:
            app.dependency_overrides.clear()


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


# ---------------------------------------------------------------------------
# Fixtures for structure tests
# ---------------------------------------------------------------------------


def _make_mock_structure(**overrides):
    """Create a mock StructureModel instance with all response fields."""
    defaults = {
        "id": uuid.uuid4(),
        "name_ru": "Канал 1",
        "name_kk": None,
        "name_en": None,
        "type": "canal",
        "district": "Район 1",
        "water_source": "р. Иртыш",
        "technical_condition": "удовлетворительное",
        "wear_percentage": 45.0,
        "commissioning_year": 1973,
        "cadastral_number": "01-001",
        "structure_count": 5,
        "geometry": None,
        "provenance_id": uuid.uuid4(),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, val in defaults.items():
        setattr(mock, key, val)
    return mock


@pytest.fixture
def mock_structure():
    """Mock StructureModel with all response fields for structure endpoint tests."""
    return _make_mock_structure()


@pytest.fixture
def mock_structure_list():
    """List of 3 mock structures for pagination and list tests."""
    return [_make_mock_structure(name_ru=f"Канал {i+1}") for i in range(3)]


@pytest.fixture
def mock_search_results():
    """List of (mock_structure, 0.85) tuples for search endpoint tests."""
    return [(_make_mock_structure(), 0.85)]


# ---------------------------------------------------------------------------
# Fixtures for auth and RBAC tests (Phase 3)
# ---------------------------------------------------------------------------


def _make_mock_user(role="admin", **overrides):
    """Create a mock UserModel instance with all response fields."""
    defaults = {
        "id": uuid.uuid4(),
        "username": f"test-{role}",
        "role": role,
        "full_name": f"Test {role.capitalize()}",
        "api_key": f"key-{role}",
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, val in defaults.items():
        setattr(mock, key, val)
    return mock


@pytest.fixture
def mock_user():
    """Mock admin user for auth tests."""
    return _make_mock_user("admin")


@pytest.fixture
def mock_viewer():
    """Mock viewer user for RBAC tests."""
    return _make_mock_user("viewer")


@pytest.fixture
def mock_inspector():
    """Mock inspector user for RBAC tests."""
    return _make_mock_user("inspector")


@pytest.fixture
def mock_engineer():
    """Mock engineer user for RBAC tests."""
    return _make_mock_user("engineer")


@pytest.fixture
def mock_auth_token():
    """Real JWT token for testing auth endpoints."""
    return jwt.encode(
        {
            "user_id": str(uuid.uuid4()),
            "username": "admin",
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        "test-secret",
        algorithm="HS256",
    )


@pytest.fixture
def auth_client(mock_healthy_minio, mock_user):
    """FastAPI TestClient with mocked authentication."""
    # Mock async_session for admin seeding in lifespan
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

        async def _override_get_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = _override_get_current_user

        with TestClient(app) as client:
            yield client

        app.dependency_overrides.clear()


@pytest.fixture
def mock_risk_assessment():
    """Mock RiskAssessment object with all factor fields."""
    mock = MagicMock()
    for key, val in {
        "condition_score": 65.0,
        "consequence_factor": 1.2,
        "seasonal_modifier": 1.0,
        "staleness_modifier": 1.0,
        "composite_score": 78.0,
        "inspection_interval": "180d",
        "repair_status": "inspection_required",
        "red_flags": [],
        "contributing_factors": {},
        "weak_evidence_reasons": [],
    }.items():
        setattr(mock, key, val)
    return mock


@pytest.fixture
def mock_inspection():
    """Mock InspectionModel with all response fields."""
    mock = MagicMock()
    for key, val in {
        "id": uuid.uuid4(),
        "structure_id": uuid.uuid4(),
        "inspection_date": "2026-06-01",
        "inspector_name": "Inspector One",
        "inspector_role": "inspector",
        "findings": "Structure in satisfactory condition",
        "condition_at_inspection": "удовлетворительное",
        "condition_score_at_inspection": 65.0,
        "red_flags_observed": [],
        "provenance_id": uuid.uuid4(),
        "created_at": datetime.now(timezone.utc),
    }.items():
        setattr(mock, key, val)
    return mock


@pytest.fixture
def mock_document():
    """Mock DocumentModel with all response fields."""
    mock = MagicMock()
    for key, val in {
        "id": uuid.uuid4(),
        "structure_id": uuid.uuid4(),
        "document_type": "inspection_report",
        "title": "Inspection Report",
        "language": "ru",
        "minio_bucket": "sujoly-documents",
        "minio_object_key": "reports/inspection-1.pdf",
        "file_size_bytes": 1024,
        "uploaded_by": "inspector",
        "provenance_id": uuid.uuid4(),
        "created_at": datetime.now(timezone.utc),
    }.items():
        setattr(mock, key, val)
    return mock
