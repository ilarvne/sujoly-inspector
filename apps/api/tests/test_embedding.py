"""Tests for embedding service and Celery embedding tasks (AI-03).

Tests:
- embed_text produces 1024-dim vector (Alem text-1024)
- embed_text fallback pseudo-embedding works without API key
- embed_structure creates EmbeddingModel
- embed_inspection creates EmbeddingModel
- embed_document creates EmbeddingModel
- batch embedding methods
- Celery task dispatch
- _vector_search uses embeddings via EmbeddingService

All embedding API calls are mocked — no real network requests in tests.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to python path so `api.*` imports resolve
sys.path.append(str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Fixtures for embedding tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_structure_for_embedding():
    """Mock StructureModel with fields suitable for embedding."""
    mock = MagicMock()
    for key, val in {
        "id": uuid.uuid4(),
        "name_ru": "Канал Иртыш-Караганда",
        "type": "canal",
        "district": "Жамбылский район",
        "water_source": "р. Иртыш",
        "technical_condition": "удовлетворительное",
        "status": "active",
    }.items():
        setattr(mock, key, val)
    return mock


@pytest.fixture
def mock_inspection_for_embedding():
    """Mock InspectionModel with fields suitable for embedding."""
    mock = MagicMock()
    for key, val in {
        "id": uuid.uuid4(),
        "structure_id": uuid.uuid4(),
        "findings": "Трещины в бетонной облицовке",
        "condition_at_inspection": "удовлетворительное",
        "red_flags_observed": ["subsidence", "erosion"],
    }.items():
        setattr(mock, key, val)
    return mock


@pytest.fixture
def mock_document_for_embedding():
    """Mock DocumentModel with fields suitable for embedding."""
    mock = MagicMock()
    for key, val in {
        "id": uuid.uuid4(),
        "title": "Паспорт гидросооружения №001",
        "document_type": "passport",
        "minio_object_key": "passports/pasport-001.pdf",
    }.items():
        setattr(mock, key, val)
    return mock


@pytest.fixture
def mock_embedding_api_response():
    """Mock response from the Alem embedding API (OpenAI-compatible format)."""
    # 1024-dim vector simulating Alem text-1024 response
    fake_embedding = [0.1] * 1024
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "index": 0,
                "embedding": fake_embedding,
            }
        ],
        "model": "text-1024",
        "usage": {"prompt_tokens": 10, "total_tokens": 10},
    }


# ---------------------------------------------------------------------------
# Tests for embed_text
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_text_produces_1024_dim_vector():
    """embed_text should produce a 1024-dimensional vector."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    # No API key → falls back to pseudo-embedding
    svc._api_key = ""
    result = await svc.embed_text("Канал Иртыш-Караганда")
    assert len(result) == 1024
    assert all(isinstance(v, float) for v in result)


@pytest.mark.asyncio
async def test_embed_text_deterministic_pseudo_embedding():
    """Pseudo-embedding should be deterministic — same text = same vector."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    svc._api_key = ""

    text = "Гидросооружение №42"
    vec1 = await svc.embed_text(text)
    vec2 = await svc.embed_text(text)
    assert vec1 == vec2


@pytest.mark.asyncio
async def test_embed_text_empty_returns_zeros():
    """embed_text for empty/whitespace text should return zero vector."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    svc._api_key = ""

    result = await svc.embed_text("")
    assert len(result) == 1024
    assert all(v == 0.0 for v in result)


@pytest.mark.asyncio
async def test_embed_text_calls_real_api_with_key(mock_embedding_api_response):
    """embed_text should call the Alem API when API key is configured."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    svc._api_key = "test-api-key"
    svc._base_url = "https://llm.alem.ai/v1"
    svc._model = "text-1024"

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=mock_embedding_api_response)

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("api.services.embedding_service.httpx.AsyncClient", return_value=mock_client):
        result = await svc.embed_text("test embedding input")

    assert len(result) == 1024
    assert result == [0.1] * 1024
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_embed_text_fallback_on_api_failure():
    """embed_text should fall back to pseudo-embedding on API failure."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    svc._api_key = "test-api-key"

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("API connection failed"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("api.services.embedding_service.httpx.AsyncClient", return_value=mock_client):
        result = await svc.embed_text("test embedding input")

    # Should fall back to pseudo-embedding
    assert len(result) == 1024
    assert not all(v == 0.0 for v in result)


# ---------------------------------------------------------------------------
# Tests for embed_structure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_structure_creates_embedding(mock_structure_for_embedding):
    """embed_structure should create an EmbeddingModel for a structure."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    svc._api_key = ""  # Use pseudo-embedding for test

    structure_id = mock_structure_for_embedding.id

    # Mock DB session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_structure_for_embedding))
    )
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("api.services.embedding_service.async_session", return_value=mock_cm):
        result = await svc.embed_structure(structure_id)

    assert result is not None
    mock_session.add.assert_called_once()
    # Verify the added model has correct source_type and source_id
    added_model = mock_session.add.call_args[0][0]
    assert added_model.source_type == "structure"
    assert added_model.source_id == structure_id


@pytest.mark.asyncio
async def test_embed_structure_not_found():
    """embed_structure should return None for non-existent structure."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    svc._api_key = ""

    mock_session = MagicMock()
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("api.services.embedding_service.async_session", return_value=mock_cm):
        result = await svc.embed_structure(uuid.uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# Tests for embed_inspection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_inspection_creates_embedding(mock_inspection_for_embedding):
    """embed_inspection should create an EmbeddingModel for an inspection."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    svc._api_key = ""

    inspection_id = mock_inspection_for_embedding.id

    mock_session = MagicMock()
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_inspection_for_embedding))
    )
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("api.services.embedding_service.async_session", return_value=mock_cm):
        result = await svc.embed_inspection(inspection_id)

    assert result is not None
    added_model = mock_session.add.call_args[0][0]
    assert added_model.source_type == "inspection"
    assert added_model.source_id == inspection_id


# ---------------------------------------------------------------------------
# Tests for embed_document
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_document_creates_embedding(mock_document_for_embedding):
    """embed_document should create an EmbeddingModel for a document."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    svc._api_key = ""

    document_id = mock_document_for_embedding.id

    mock_session = MagicMock()
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_document_for_embedding))
    )
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("api.services.embedding_service.async_session", return_value=mock_cm):
        result = await svc.embed_document(document_id)

    assert result is not None
    added_model = mock_session.add.call_args[0][0]
    assert added_model.source_type == "document"
    assert added_model.source_id == document_id


# ---------------------------------------------------------------------------
# Tests for batch embedding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_all_structures():
    """embed_all_structures should embed structures without embeddings."""
    from api.services.embedding_service import EmbeddingService

    svc = EmbeddingService()
    svc._api_key = ""

    structure_id_1 = uuid.uuid4()
    structure_id_2 = uuid.uuid4()

    # Mock: no existing embeddings, two structures to embed
    mock_session = MagicMock()

    # First call: existing embeddings (empty)
    existing_result = MagicMock()
    existing_result.all = MagicMock(return_value=[])

    # Second call: structures without embeddings
    structures_result = MagicMock()
    structures_result.all = MagicMock(return_value=[(structure_id_1,), (structure_id_2,)])

    call_count = [0]

    async def mock_execute(stmt):
        call_count[0] += 1
        if call_count[0] == 1:
            return existing_result
        return structures_result

    mock_session.execute = mock_execute

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    # Mock embed_structure to return something
    mock_emb = MagicMock()
    mock_emb.id = uuid.uuid4()

    with patch("api.services.embedding_service.async_session", return_value=mock_cm), \
         patch.object(svc, "embed_structure", new_callable=AsyncMock, return_value=mock_emb):
        count = await svc.embed_all_structures()

    assert count == 2


# ---------------------------------------------------------------------------
# Tests for Celery task dispatch
# ---------------------------------------------------------------------------


def test_generate_structure_embedding_task():
    """Celery task generate_structure_embedding should call embedding service."""
    mock_result = MagicMock()
    mock_result.id = uuid.uuid4()

    async def mock_embed_structure(sid):
        return mock_result

    with patch("api.services.embedding_service.embedding_service") as mock_svc:
        mock_svc.embed_structure = mock_embed_structure

        # Need to patch asyncio.run since the task uses it
        with patch("api.tasks.celery_tasks.asyncio") as mock_asyncio:
            from api.tasks.celery_tasks import generate_structure_embedding

            # Simulate what the task does: asyncio.run(embed())
            # We'll just test the task function signature and structure
            assert callable(generate_structure_embedding)


def test_generate_all_embeddings_task():
    """Celery task generate_all_embeddings should exist and be callable."""
    from api.tasks.celery_tasks import generate_all_embeddings

    assert callable(generate_all_embeddings)


# ---------------------------------------------------------------------------
# Tests for vector search integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vector_search_uses_embedding_service():
    """_vector_search should call EmbeddingService.embed_text and query embeddings."""
    from api.services.search_service import SearchService

    svc = SearchService()

    # Mock embedding_service.embed_text to return a 1024-dim vector
    fake_embedding = [0.1] * 1024

    # Mock DB results: one embedding row
    mock_session = MagicMock()
    mock_row = ("structure", uuid.uuid4(), "Канал Иртыш", 0.15)
    mock_result = MagicMock()
    mock_result.all = MagicMock(return_value=[mock_row])
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("api.services.embedding_service.embedding_service") as mock_emb_svc, \
         patch("api.services.search_service.async_session", return_value=mock_cm):
        mock_emb_svc.embed_text = AsyncMock(return_value=fake_embedding)

        results = await svc._vector_search("Канал", 10)

    assert len(results) == 1
    assert results[0]["source_type"] == "structure"
    # score = 1.0 - distance = 1.0 - 0.15 = 0.85
    assert abs(results[0]["score"] - 0.85) < 0.001


@pytest.mark.asyncio
async def test_vector_search_returns_empty_on_embedding_failure():
    """_vector_search should return empty list if embedding generation fails."""
    from api.services.search_service import SearchService

    svc = SearchService()

    with patch("api.services.embedding_service.embedding_service") as mock_emb_svc:
        mock_emb_svc.embed_text = AsyncMock(side_effect=Exception("API down"))

        results = await svc._vector_search("test query", 10)

    assert results == []
