"""Tests for OCR pipeline endpoints and service.

Tests cover:
- OcrService.extract_text: text files → HIGH confidence, images → LOW
- OcrService.extract_entities: Russian/Kazakh pattern matching
- POST /api/v1/ocr/upload → 201 with document_id + ocr_result
- POST /api/v1/ocr/process/{document_id} → 200 with ocr_result
- GET /api/v1/ocr/results/{document_id} → 200 with cached results
- GET /api/v1/ocr/results/{document_id} → 404 when no results cached
"""

import uuid
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.services.ocr_service import OcrService, _extract_value_after_prefix, _extract_year_from_text


# ---------------------------------------------------------------------------
# Unit tests for OcrService business logic
# ---------------------------------------------------------------------------


class TestEntityExtraction:
    """Tests for Russian/Kazakh entity extraction patterns."""

    def test_extract_structure_name_russian(self):
        """Pattern-match structure name after 'Наименование:'."""
        text = "Наименование: Канал Бигаз\nРайон: Жуалы"
        value = _extract_value_after_prefix(text, ["Наименование:", "Атауы:"])
        assert value == "Канал Бигаз"

    def test_extract_structure_name_kazakh(self):
        """Pattern-match structure name after 'Атауы:'."""
        text = "Атауы: Бигаз каналы\nРайон: Жуалы"
        value = _extract_value_after_prefix(text, ["Наименование:", "Атауы:"])
        assert value == "Бигаз каналы"

    def test_extract_district_russian(self):
        """Pattern-match district after 'Район:'."""
        text = "Район: Жуалы ауданы"
        value = _extract_value_after_prefix(text, ["Район:", "Аудан:"])
        assert value == "Жуалы ауданы"

    def test_extract_district_kazakh(self):
        """Pattern-match district after 'Аудан:'."""
        text = "Аудан: Жуалы"
        value = _extract_value_after_prefix(text, ["Район:", "Аудан:"])
        assert value == "Жуалы"

    def test_extract_condition_russian(self):
        """Pattern-match condition after 'Состояние:'."""
        text = "Состояние: удовлетворительное"
        value = _extract_value_after_prefix(text, ["Состояние:", "Жағдай:"])
        assert value == "удовлетворительное"

    def test_extract_condition_kazakh(self):
        """Pattern-match condition after 'Жағдай:'."""
        text = "Жағдай: қанағаттанарлық"
        value = _extract_value_after_prefix(text, ["Состояние:", "Жағдай:"])
        assert value == "қанағаттанарлық"

    def test_extract_year_russian(self):
        """Extract year after 'год' keyword."""
        text = "год ввода в эксплуатацию 1973"
        year = _extract_year_from_text(text)
        assert year == "1973"

    def test_extract_year_kazakh(self):
        """Extract year after 'жыл' keyword."""
        text = "жыл 1985"
        year = _extract_year_from_text(text)
        assert year == "1985"

    def test_extract_year_invalid(self):
        """Year outside 1800-2100 range is rejected."""
        text = "год 300"
        year = _extract_year_from_text(text)
        assert year is None

    def test_extract_water_source(self):
        """Pattern-match water source."""
        text = "Источник водоснабжения: р. Талас"
        value = _extract_value_after_prefix(text, ["Источник водоснабжения:", "Су көзі:"])
        assert value == "р. Талас"

    def test_extract_capacity(self):
        """Pattern-match capacity."""
        text = "Пропускная способность: 2.5 м³/с"
        value = _extract_value_after_prefix(text, ["Пропускная способность:", "Өткізу қабілеттілігі:"])
        assert value == "2.5 м³/с"

    def test_no_match_returns_none(self):
        """No matching prefix returns None."""
        text = "Some random text without patterns"
        value = _extract_value_after_prefix(text, ["Наименование:", "Атауы:"])
        assert value is None


class TestOcrService:
    """Unit tests for OcrService text extraction."""

    @pytest.mark.asyncio
    async def test_extract_text_txt_file(self):
        """OcrService.extract_text reads text files directly → HIGH confidence."""
        service = OcrService(minio_service=None)
        russian_text = "Наименование: Канал 1\nРайон: Жуалы\nГод: 1973"
        result = await service.extract_text(
            russian_text.encode("utf-8"),
            "passport.txt",
        )
        assert result["confidence"] == "HIGH"
        assert result["language"] == "ru"
        assert "Канал 1" in result["text"]
        # Should also have extracted entities
        assert len(result["entities"]) >= 1

    @pytest.mark.asyncio
    async def test_extract_text_image_file(self):
        """OcrService.extract_text returns LOW confidence for images."""
        service = OcrService(minio_service=None)
        result = await service.extract_text(
            b"\x89PNG\r\n\x1a\n",  # PNG header bytes
            "passport_scan.png",
        )
        assert result["confidence"] == "LOW"
        assert "placeholder" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_extract_text_pdf_file(self):
        """OcrService.extract_text returns LOW confidence for PDFs."""
        service = OcrService(minio_service=None)
        result = await service.extract_text(
            b"%PDF-1.4",  # PDF header
            "document.pdf",
        )
        assert result["confidence"] == "LOW"

    @pytest.mark.asyncio
    async def test_extract_entities_russian_passport(self):
        """OcrService.extract_entities extracts multiple entities from Russian text."""
        service = OcrService(minio_service=None)
        text = (
            "Наименование: Канал Бигаз\n"
            "Район: Жуалы\n"
            "год ввода 1973\n"
            "Состояние: удовлетворительное\n"
            "Источник водоснабжения: р. Талас\n"
            "Пропускная способность: 2.5 м³/с\n"
        )
        entities = await service.extract_entities(text)

        entity_types = {e["type"] for e in entities}
        assert "structure_name" in entity_types
        assert "district" in entity_types
        assert "commissioning_year" in entity_types
        assert "condition" in entity_types
        assert "water_source" in entity_types
        assert "capacity" in entity_types

        # Check specific values
        name_entity = next(e for e in entities if e["type"] == "structure_name")
        assert name_entity["value"] == "Канал Бигаз"

    @pytest.mark.asyncio
    async def test_extract_entities_kazakh_passport(self):
        """OcrService.extract_entities extracts entities from Kazakh text."""
        service = OcrService(minio_service=None)
        text = (
            "Атауы: Бигаз каналы\n"
            "Аудан: Жуалы\n"
            "жыл 1985\n"
            "Жағдай: қанағаттанарлық\n"
        )
        entities = await service.extract_entities(text)

        entity_types = {e["type"] for e in entities}
        assert "structure_name" in entity_types
        assert "district" in entity_types
        assert "commissioning_year" in entity_types
        assert "condition" in entity_types

    @pytest.mark.asyncio
    async def test_extract_entities_empty_text(self):
        """OcrService.extract_entities returns empty list for empty text."""
        service = OcrService(minio_service=None)
        entities = await service.extract_entities("")
        assert entities == []

    @pytest.mark.asyncio
    async def test_extract_text_kazakh_detected(self):
        """OcrService.extract_text detects Kazakh language from Kazakh-specific characters."""
        service = OcrService(minio_service=None)
        # Use Kazakh-specific characters: ә, ғ, қ, ң, ө, ұ, ү, һ, і
        kazakh_text = "Атауы: Өзен каналы\nАудан: Жуалы"
        result = await service.extract_text(
            kazakh_text.encode("utf-8"),
            "passport_kk.txt",
        )
        assert result["language"] == "kk"


class TestOcrEndpoints:
    """Tests for /api/v1/ocr REST endpoints."""

    def test_upload_and_ocr_txt(self, test_client):
        """POST /api/v1/ocr/upload with a text file returns 201 with OCR results."""
        russian_text = "Наименование: Канал 1\nРайон: Жуалы\nгод ввода 1973"
        response = test_client.post(
            "/api/v1/ocr/upload",
            files={"file": ("passport.txt", russian_text.encode("utf-8"), "text/plain")},
        )
        assert response.status_code == 201
        data = response.json()
        assert "document_id" in data
        assert "minio_object_key" in data
        assert "ocr_result" in data
        ocr = data["ocr_result"]
        assert ocr["confidence"] == "HIGH"
        assert ocr["language"] == "ru"
        assert len(ocr["entities"]) >= 1

    def test_upload_and_ocr_image(self, test_client):
        """POST /api/v1/ocr/upload with an image file returns 201 with LOW confidence."""
        response = test_client.post(
            "/api/v1/ocr/upload",
            files={"file": ("scan.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["ocr_result"]["confidence"] == "LOW"

    def test_upload_empty_file(self, test_client):
        """POST /api/v1/ocr/upload with empty file returns 400."""
        response = test_client.post(
            "/api/v1/ocr/upload",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 400

    def test_get_ocr_results(self, test_client):
        """GET /api/v1/ocr/results/{id} returns cached OCR results."""
        # First upload
        russian_text = "Наименование: Канал 1"
        upload_response = test_client.post(
            "/api/v1/ocr/upload",
            files={"file": ("passport.txt", russian_text.encode("utf-8"), "text/plain")},
        )
        doc_id = upload_response.json()["document_id"]

        # Then get results
        response = test_client.get(f"/api/v1/ocr/results/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
        assert data["confidence"] == "HIGH"

    def test_get_ocr_results_not_found(self, test_client):
        """GET /api/v1/ocr/results/{id} returns 404 when no results cached."""
        nonexistent_id = uuid.uuid4()
        response = test_client.get(f"/api/v1/ocr/results/{nonexistent_id}")
        assert response.status_code == 404

    def test_process_document_not_found(self, test_client):
        """POST /api/v1/ocr/process/{id} returns 404 for non-existent document."""
        nonexistent_id = uuid.uuid4()
        with patch(
            "api.services.ocr_service.OcrService.process_document",
            AsyncMock(side_effect=ValueError(f"Document '{nonexistent_id}' not found")),
        ):
            response = test_client.post(f"/api/v1/ocr/process/{nonexistent_id}")
        assert response.status_code == 404
