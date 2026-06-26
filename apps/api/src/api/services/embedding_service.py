"""Embedding generation service for vector similarity search (AI-03).

Provides:
- embed_text: generate embedding via Alem text-1024 API (OpenAI-compatible)
- embed_structure: load + concatenate structure text → embed → store
- embed_inspection: load + concatenate inspection text → embed → store
- embed_document: load + use OCR text or title → embed → store
- embed_all_structures: batch embed structures without embeddings
- embed_all_inspections: batch embed inspections without embeddings

Uses real Alem embedding API (text-1024, 1024 dimensions) configured via .env.
Falls back to deterministic pseudo-embedding if API key is not configured.
"""

import hashlib
import os
import uuid
from typing import Any

import httpx
import structlog
from sqlalchemy import and_, select

from api.config.settings import settings
from api.infrastructure.database import async_session
from api.models.document import DocumentModel
from api.models.embedding import EmbeddingModel
from api.models.inspection import InspectionModel
from api.models.structure import StructureModel

logger = structlog.get_logger(__name__)


def _get_embedding_api_key() -> str:
    """Get embedding API key from env (EMBEDDINGS_API_KEY) or settings."""
    return os.environ.get("EMBEDDINGS_API_KEY", settings.embedding_api_key)


class EmbeddingService:
    """Embedding generation service for vector similarity search (AI-03).

    Uses Alem text-1024 embedding API (OpenAI-compatible endpoint) for real
    embeddings. Falls back to deterministic pseudo-embeddings if API is
    unavailable, so the pipeline works end-to-end in any environment.
    """

    def __init__(self):
        self._api_key = _get_embedding_api_key()
        self._base_url = settings.embedding_base_url
        self._model = settings.embedding_model
        self._dimensions = settings.embedding_dimensions

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text via Alem text-1024 API.

        Uses the OpenAI-compatible POST /v1/embeddings endpoint.
        Falls back to deterministic pseudo-embedding if API key is missing
        or API call fails.

        Args:
            text: Text to embed.

        Returns:
            1024-dimensional embedding vector.
        """
        if not text or not text.strip():
            return [0.0] * self._dimensions

        # Try real Alem API first
        if self._api_key:
            try:
                return await self._call_embedding_api(text)
            except Exception as exc:
                logger.warning(
                    "embedding_api_failed_fallback",
                    error=str(exc),
                    text_preview=text[:100],
                )

        # Fallback: deterministic pseudo-embedding (hash-based)
        return self._pseudo_embed(text)

    async def _call_embedding_api(self, text: str) -> list[float]:
        """Call the Alem embedding API (OpenAI-compatible /v1/embeddings).

        Args:
            text: Text to embed.

        Returns:
            Embedding vector from the API response.
        """
        url = f"{self._base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "input": text,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            # OpenAI-compatible format: data[0]["embedding"]
            embedding_data = data.get("data", [])
            if embedding_data and "embedding" in embedding_data[0]:
                return embedding_data[0]["embedding"]

            raise ValueError(f"Unexpected embedding API response format: {list(data.keys())}")

    def _pseudo_embed(self, text: str) -> list[float]:
        """Generate deterministic pseudo-embedding for fallback.

        Uses SHA-256 hash of text to seed a deterministic 1024-dim vector.
        Same text always produces the same vector, so search works
        end-to-end even without an embedding API key.

        Args:
            text: Text to embed.

        Returns:
            1024-dimensional pseudo-embedding vector with values in [-1, 1].
        """
        vec = []
        for i in range(self._dimensions):
            # Hash text + index for deterministic but varied values
            h = hashlib.sha256(f"{text}:{i}".encode("utf-8")).hexdigest()
            # Convert first 8 hex chars to a float in [-1, 1]
            val = int(h[:8], 16) / 0xFFFFFFFF * 2.0 - 1.0
            vec.append(val)
        return vec

    async def embed_structure(self, structure_id: uuid.UUID) -> EmbeddingModel | None:
        """Generate and store embedding for a structure.

        Concatenates: name_ru + type + district + water_source + technical_condition

        Args:
            structure_id: UUID of the structure to embed.

        Returns:
            The created EmbeddingModel, or None if structure not found.
        """
        async with async_session() as session:
            result = await session.execute(
                select(StructureModel).where(StructureModel.id == structure_id)
            )
            structure = result.scalar_one_or_none()
            if structure is None:
                logger.warning("embed_structure_not_found", structure_id=str(structure_id))
                return None

            # Build text to embed
            parts = [
                structure.name_ru or "",
                structure.type or "",
                structure.district or "",
                structure.water_source or "",
                structure.technical_condition or "",
            ]
            text = " ".join(p for p in parts if p).strip()

            if not text:
                logger.warning("embed_structure_empty_text", structure_id=str(structure_id))
                return None

            # Generate embedding
            embedding = await self.embed_text(text)

            # Store in embeddings table
            emb_model = EmbeddingModel(
                source_type="structure",
                source_id=structure_id,
                content_text=text,
                embedding=embedding,
            )
            session.add(emb_model)
            await session.commit()
            await session.refresh(emb_model)

            logger.info(
                "structure_embedded",
                structure_id=str(structure_id),
                embedding_id=str(emb_model.id),
            )
            return emb_model

    async def embed_inspection(self, inspection_id: uuid.UUID) -> EmbeddingModel | None:
        """Generate and store embedding for an inspection.

        Concatenates: findings + condition + red_flags

        Args:
            inspection_id: UUID of the inspection to embed.

        Returns:
            The created EmbeddingModel, or None if inspection not found.
        """
        async with async_session() as session:
            result = await session.execute(
                select(InspectionModel).where(InspectionModel.id == inspection_id)
            )
            inspection = result.scalar_one_or_none()
            if inspection is None:
                logger.warning("embed_inspection_not_found", inspection_id=str(inspection_id))
                return None

            # Build text to embed
            parts = [
                inspection.findings or "",
                inspection.condition_at_inspection or "",
            ]
            # Add red flags as text
            if inspection.red_flags_observed:
                parts.extend(str(flag) for flag in inspection.red_flags_observed)

            text = " ".join(p for p in parts if p).strip()

            if not text:
                logger.warning("embed_inspection_empty_text", inspection_id=str(inspection_id))
                return None

            # Generate embedding
            embedding = await self.embed_text(text)

            # Store in embeddings table
            emb_model = EmbeddingModel(
                source_type="inspection",
                source_id=inspection_id,
                content_text=text,
                embedding=embedding,
            )
            session.add(emb_model)
            await session.commit()
            await session.refresh(emb_model)

            logger.info(
                "inspection_embedded",
                inspection_id=str(inspection_id),
                embedding_id=str(emb_model.id),
            )
            return emb_model

    async def embed_document(self, document_id: uuid.UUID) -> EmbeddingModel | None:
        """Generate and store embedding for a document.

        Uses title + document_type as text (OCR text would be integrated
        via the OCR pipeline in production). For MVP, we embed the
        document metadata text since OCR results aren't persisted to
        the document model.

        Args:
            document_id: UUID of the document to embed.

        Returns:
            The created EmbeddingModel, or None if document not found.
        """
        async with async_session() as session:
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
            document = result.scalar_one_or_none()
            if document is None:
                logger.warning("embed_document_not_found", document_id=str(document_id))
                return None

            # Build text to embed — use title + document_type + filename
            parts = [
                document.title or "",
                document.document_type or "",
                document.minio_object_key.split("/")[-1] if document.minio_object_key else "",
            ]
            text = " ".join(p for p in parts if p).strip()

            if not text:
                logger.warning("embed_document_empty_text", document_id=str(document_id))
                return None

            # Generate embedding
            embedding = await self.embed_text(text)

            # Store in embeddings table
            emb_model = EmbeddingModel(
                source_type="document",
                source_id=document_id,
                content_text=text,
                embedding=embedding,
            )
            session.add(emb_model)
            await session.commit()
            await session.refresh(emb_model)

            logger.info(
                "document_embedded",
                document_id=str(document_id),
                embedding_id=str(emb_model.id),
            )
            return emb_model

    async def embed_all_structures(self) -> int:
        """Batch embed all structures that don't have embeddings yet.

        Returns:
            Count of newly embedded structures.
        """
        async with async_session() as session:
            # Find structures without embeddings
            existing_stmt = select(EmbeddingModel.source_id).where(
                EmbeddingModel.source_type == "structure"
            )
            existing_result = await session.execute(existing_stmt)
            existing_ids = {row[0] for row in existing_result.all()}

            # Get all active structures
            stmt = select(StructureModel.id).where(
                and_(
                    StructureModel.status != "deleted",
                    StructureModel.id.notin_(existing_ids),
                )
            )
            result = await session.execute(stmt)
            structure_ids = [row[0] for row in result.all()]

        # Embed each structure
        count = 0
        for sid in structure_ids:
            try:
                result = await self.embed_structure(sid)
                if result is not None:
                    count += 1
            except Exception as exc:
                logger.warning(
                    "batch_embed_structure_failed",
                    structure_id=str(sid),
                    error=str(exc),
                )

        logger.info("batch_embed_structures_complete", count=count, total=len(structure_ids))
        return count

    async def embed_all_inspections(self) -> int:
        """Batch embed all inspections without embeddings.

        Returns:
            Count of newly embedded inspections.
        """
        async with async_session() as session:
            # Find inspections without embeddings
            existing_stmt = select(EmbeddingModel.source_id).where(
                EmbeddingModel.source_type == "inspection"
            )
            existing_result = await session.execute(existing_stmt)
            existing_ids = {row[0] for row in existing_result.all()}

            # Get all inspections not already embedded
            stmt = select(InspectionModel.id).where(
                InspectionModel.id.notin_(existing_ids)
            )
            result = await session.execute(stmt)
            inspection_ids = [row[0] for row in result.all()]

        # Embed each inspection
        count = 0
        for iid in inspection_ids:
            try:
                result = await self.embed_inspection(iid)
                if result is not None:
                    count += 1
            except Exception as exc:
                logger.warning(
                    "batch_embed_inspection_failed",
                    inspection_id=str(iid),
                    error=str(exc),
                )

        logger.info("batch_embed_inspections_complete", count=count, total=len(inspection_ids))
        return count


# Module-level singleton for route handlers and Celery tasks
embedding_service = EmbeddingService()
