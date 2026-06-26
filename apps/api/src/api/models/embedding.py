"""Embedding ORM model for vector similarity search.

EmbeddingModel: Stores text embeddings for structures, inspections,
documents, and candidates. Uses pgvector Vector(1536) column for
OpenAI ada-002 compatible embeddings.

Architecture (AI-03): Hybrid search combines full-text + pg_trgm + pgvector
cosine similarity with RRF fusion. This model is the vector component.
"""

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class EmbeddingModel(Base):
    """Embedding record for vector similarity search (AI-03).

    Each row stores an embedding vector for a piece of content from
    a source entity (structure, inspection, document, or candidate).
    The HNSW index on the embedding column enables fast cosine
    similarity queries via pgvector.
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
    embedding = mapped_column(
        Vector(1536), nullable=True,
        comment="OpenAI ada-002 compatible 1536-dim embedding vector",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_embeddings_source", "source_type", "source_id"),
    )
