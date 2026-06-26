"""Embedding ORM model for vector similarity search.

EmbeddingModel: Stores text embeddings for structures, inspections,
documents, and candidates. Uses a JSONB column to store embedding vectors
as JSON arrays (no pgvector dependency required).

Architecture (AI-03): Hybrid search combines full-text + pg_trgm + JSONB-stored
embeddings. Vector similarity search is performed in Python when needed.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class EmbeddingModel(Base):
    """Embedding record for vector similarity search (AI-03).

    Each row stores an embedding vector for a piece of content from
    a source entity (structure, inspection, document, or candidate).
    The embedding is stored as a JSONB array of floats.
    """

    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Source entity type: structure, inspection, document, candidate",
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False,
        comment="UUID of the source record",
    )
    content_text: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="The text that was embedded",
    )
    embedding: Mapped[list | None] = mapped_column(
        JSONB, nullable=True,
        comment="Embedding vector stored as JSON array of floats",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_embeddings_source", "source_type", "source_id"),
    )
