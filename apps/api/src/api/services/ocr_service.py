"""OCR pipeline service — text extraction + entity recognition for scanned documents.

Provides:
- extract_text: extract text from uploaded document (stub for images, real for text)
- extract_entities: pattern-match Russian/Kazakh hydraulic structure passport fields
- process_document: load document from DB + MinIO → OCR → create candidate

For hackathon MVP: simple pattern-matching approach for Russian/Kazakh passports.
Can be upgraded to Tesseract/EasyOCR/PaddleOCR for production.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

import structlog
from sqlalchemy import select

from api.infrastructure.database import async_session
from api.models.document import DocumentModel
from api.services.minio_client import MinIOService

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Entity extraction patterns for Russian/Kazakh hydraulic structure passports
# ---------------------------------------------------------------------------

_ENTITY_PATTERNS: list[dict[str, Any]] = [
    # Structure names
    {
        "type": "structure_name",
        "prefixes": ["Наименование:", "Атауы:", "Наименование сооружения:"],
        "confidence": "HIGH",
    },
    # Commissioning years
    {
        "type": "commissioning_year",
        "prefixes": ["год ввода", "год ввода в эксплуатацию", "жыл", "Год:"],
        "confidence": "MEDIUM",
    },
    # District names
    {
        "type": "district",
        "prefixes": ["Район:", "Аудан:", "Район расположения:"],
        "confidence": "HIGH",
    },
    # Condition ratings
    {
        "type": "condition",
        "prefixes": ["Состояние:", "Жағдай:", "Техническое состояние:", "Техникалық жағдай:"],
        "confidence": "MEDIUM",
    },
    # Water source
    {
        "type": "water_source",
        "prefixes": ["Источник водоснабжения:", "Су көзі:", "Водный источник:"],
        "confidence": "HIGH",
    },
    # Capacity
    {
        "type": "capacity",
        "prefixes": ["Пропускная способность:", "Өткізу қабілеттілігі:", "Расход:"],
        "confidence": "HIGH",
    },
]


def _extract_value_after_prefix(text: str, prefixes: list[str]) -> str | None:
    """Extract the value following one of the given prefixes in the text.

    Searches for each prefix in the text and returns the text after it
    (up to the next newline or semicolon).
    """
    for prefix in prefixes:
        pattern = re.escape(prefix) + r"\s*(.+?)(?:\n|;|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_year_from_text(text: str) -> str | None:
    """Extract a 4-digit year from text following year-related keywords."""
    year_keywords = ["год", "жыл", "введен", "построен"]
    for keyword in year_keywords:
        pattern = keyword + r"[^\d]*(\d{4})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            year = match.group(1)
            # Sanity check: year should be reasonable (1800-2100)
            if 1800 <= int(year) <= 2100:
                return year
    return None


class OcrService:
    """OCR pipeline service for scanned hydraulic structure passports.

    For hackathon MVP:
    - Text files: read directly
    - Images/PDFs: return placeholder with confidence=LOW
    - Entity extraction: regex pattern matching for Russian/Kazakh fields
    """

    def __init__(self, minio_service: MinIOService | None = None):
        self.minio = minio_service

    async def extract_text(self, file_bytes: bytes, filename: str) -> dict:
        """Extract text from uploaded document.

        For MVP:
        - Text-based formats (.txt, .csv): read directly → HIGH confidence
        - Images/PDFs: return placeholder → LOW confidence

        Returns:
            {
                "text": extracted text,
                "confidence": "HIGH"|"MEDIUM"|"LOW",
                "language": "ru"|"kk"|"unknown",
                "entities": list of extracted entities
            }
        """
        text_content = ""
        confidence = "LOW"
        language = "unknown"

        lower_name = filename.lower()

        if lower_name.endswith((".txt", ".csv", ".tsv")):
            # Text-based: read directly
            try:
                text_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text_content = file_bytes.decode("windows-1251")  # Common Russian encoding
                except UnicodeDecodeError:
                    text_content = file_bytes.decode("latin-1")

            confidence = "HIGH"

            # Simple language detection based on Cyrillic patterns
            if re.search(r"[а-яА-ЯёЁ]", text_content):
                if re.search(r"[әғқңөұүһіӘҒҚҢӨҰҮҺІ]", text_content):
                    language = "kk"  # Kazakh-specific characters
                else:
                    language = "ru"  # Russian

        elif lower_name.endswith((".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp")):
            # Images/PDFs: stub — would need Tesseract/EasyOCR in production
            text_content = f"[OCR placeholder: {filename}] — full OCR requires Tesseract/EasyOCR integration"
            confidence = "LOW"

            # Attempt to detect language from filename patterns
            if any(kw in lower_name for kw in ["kk", "kaz", "kazakh"]):
                language = "kk"
            elif any(kw in lower_name for kw in ["ru", "rus", "russian"]):
                language = "ru"

        else:
            text_content = f"[Unsupported format: {filename}]"
            confidence = "LOW"

        # Extract entities from whatever text we have
        entities = await self.extract_entities(text_content)

        return {
            "text": text_content,
            "confidence": confidence,
            "language": language,
            "entities": entities,
        }

    async def extract_entities(self, text: str) -> list[dict]:
        """Extract named entities from Russian/Kazakh text.

        Pattern-match for:
        - Structure names (after "Наименование:", "Атауы:")
        - Years (4-digit numbers after "год", "жыл")
        - District names (after "Район:", "Аудан:")
        - Condition ratings (after "Состояние:", "Жағдай:")
        - Water source (after "Источник водоснабжения:", "Су көзі:")
        - Capacity (after "Пропускная способность:", "Өткізу қабілеттілігі:")

        Returns list of {"type": str, "value": str, "confidence": str}
        """
        entities = []

        for pattern_def in _ENTITY_PATTERNS:
            entity_type = pattern_def["type"]
            prefixes = pattern_def["prefixes"]
            confidence = pattern_def["confidence"]

            if entity_type == "commissioning_year":
                # Year extraction uses different logic
                year = _extract_year_from_text(text)
                if year:
                    entities.append({
                        "type": entity_type,
                        "value": year,
                        "confidence": confidence,
                    })
            else:
                value = _extract_value_after_prefix(text, prefixes)
                if value:
                    entities.append({
                        "type": entity_type,
                        "value": value,
                        "confidence": confidence,
                    })

        return entities

    async def process_document(self, document_id: uuid.UUID) -> dict:
        """Process an existing document through OCR pipeline.

        1. Load document from DB
        2. Fetch file from MinIO
        3. Run extract_text
        4. Store results in document metadata
        5. If entities found, create candidate from OCR data

        Returns the OCR result dict with text, confidence, language, entities.
        """
        # 1. Load document from DB
        async with async_session() as session:
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
            document = result.scalar_one_or_none()

        if document is None:
            raise ValueError(f"Document '{document_id}' not found")

        # 2. Fetch file from MinIO
        if self.minio is None:
            raise ValueError("MinIO service not configured for OcrService")

        response = self.minio.client.get_object(
            document.minio_bucket, document.minio_object_key
        )
        try:
            file_bytes = response.read()
        finally:
            response.close()
            if hasattr(response, "release_conn"):
                response.release_conn()

        # 3. Run extract_text
        filename = document.minio_object_key.split("/")[-1] if "/" in document.minio_object_key else document.minio_object_key
        ocr_result = await self.extract_text(file_bytes, filename)

        # 4. Store results (for MVP: just return them; production would update DB)
        logger.info(
            "ocr_document_processed",
            document_id=str(document_id),
            confidence=ocr_result["confidence"],
            language=ocr_result["language"],
            entity_count=len(ocr_result["entities"]),
        )

        return ocr_result
