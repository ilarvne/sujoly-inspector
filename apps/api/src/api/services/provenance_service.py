"""Provenance CRUD service — async database operations.

Provides:
- create_provenance: create a new provenance record
- get_provenance: retrieve a provenance record by ID
- query_provenance: query provenance records with optional filters

This is the core DATA-07 implementation: every fact has a source,
confidence, and timestamp, stored as an immutable provenance record.
"""

import uuid

import structlog
from sqlalchemy import select

from api.infrastructure.database import async_session
from api.models.provenance import ProvenanceModel

logger = structlog.get_logger(__name__)


async def create_provenance(
    source_type: str,
    confidence_level: str,
    source_reference: str | None = None,
    contributor: str | None = None,
) -> ProvenanceModel:
    """Create a new provenance record and return it.

    Args:
        source_type: kazvodhoz_spreadsheet, osm, satellite, ocr, manual, ai_inferred, inspection
        confidence_level: HIGH, MEDIUM, LOW
        source_reference: URL, file path, OSM element ID, satellite scene ID, etc.
        contributor: Person, system, or process that contributed this fact

    Returns:
        The created ProvenanceModel with generated id and recorded_at.
    """
    async with async_session() as session:
        async with session.begin():
            model = ProvenanceModel(
                source_type=source_type,
                confidence_level=confidence_level,
                source_reference=source_reference,
                contributor=contributor,
            )
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return model


async def get_provenance(provenance_id: uuid.UUID) -> ProvenanceModel | None:
    """Retrieve a provenance record by ID.

    Args:
        provenance_id: UUID of the provenance record

    Returns:
        ProvenanceModel if found, None if not found.
    """
    async with async_session() as session:
        result = await session.execute(
            select(ProvenanceModel).where(
                ProvenanceModel.id == provenance_id
            )
        )
        return result.scalar_one_or_none()


async def query_provenance(
    source_type: str | None = None,
    confidence_level: str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[ProvenanceModel]:
    """Query provenance records with optional filters.

    Args:
        source_type: Filter by source_type (e.g., 'kazvodhoz_spreadsheet')
        confidence_level: Filter by confidence_level (HIGH, MEDIUM, LOW)
        offset: Pagination offset
        limit: Maximum number of records to return

    Returns:
        List of ProvenanceModel matching the filters.
    """
    async with async_session() as session:
        stmt = select(ProvenanceModel)
        if source_type is not None:
            stmt = stmt.where(ProvenanceModel.source_type == source_type)
        if confidence_level is not None:
            stmt = stmt.where(
                ProvenanceModel.confidence_level == confidence_level
            )
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
