"""Inspection CRUD + photo linking + risk recomputation trigger service.

Provides:
- create_inspection: create inspection with photos and provenance, trigger recomputation
- get_inspection: fetch inspection by ID with photos
- list_inspections: list inspections for a structure with pagination

Creating an inspection triggers risk recomputation via Celery task
(D-05 trigger #1). This connects inspection history to the risk engine.
"""

import uuid
from datetime import date, datetime

import structlog
from sqlalchemy import desc, func, select

from api.infrastructure.database import async_session
from api.models.inspection import InspectionModel, InspectionPhotoModel
from api.models.provenance import ProvenanceModel
from api.models.structure import StructureModel
from api.schemas.inspections import InspectionCreate

logger = structlog.get_logger(__name__)


async def create_inspection(
    structure_id: uuid.UUID,
    data: InspectionCreate,
    user: object,
) -> InspectionModel | None:
    """Create an inspection record with photo attachments and provenance.

    Creates ProvenanceModel with source_type='inspection', then creates
    the InspectionModel and any InspectionPhotoModel rows. After session
    commit, dispatches recompute_structure_risk Celery task (D-05 trigger #1).

    Args:
        structure_id: UUID of the structure being inspected
        data: InspectionCreate with inspection fields and photo metadata
        user: The authenticated user creating the inspection

    Returns:
        InspectionModel if structure found, None if structure_id not found.
    """
    async with async_session() as session:
        async with session.begin():
            # 1. Verify structure exists
            result = await session.execute(
                select(StructureModel).where(StructureModel.id == structure_id)
            )
            structure = result.scalar_one_or_none()
            if structure is None:
                return None

            # 2. Create provenance with source_type='inspection' (DATA-07)
            username = getattr(user, "username", "unknown")
            provenance = ProvenanceModel(
                source_type="inspection",
                source_reference=f"api:inspection:{structure_id}",
                confidence_level="HIGH",
                contributor=username,
            )
            session.add(provenance)
            await session.flush()

            # 3. Create inspection model
            inspection = InspectionModel(
                structure_id=structure_id,
                inspection_date=data.inspection_date,
                inspector_name=data.inspector_name,
                inspector_role=data.inspector_role,
                findings=data.findings,
                condition_at_inspection=data.condition_at_inspection,
                condition_score_at_inspection=data.condition_score_at_inspection,
                red_flags_observed=data.red_flags_observed,
                provenance_id=provenance.id,
            )
            session.add(inspection)
            await session.flush()

            # 4. Create photo attachments
            for photo_meta in data.photos:
                photo = InspectionPhotoModel(
                    inspection_id=inspection.id,
                    minio_bucket=photo_meta.minio_bucket,
                    minio_object_key=photo_meta.minio_object_key,
                    caption=photo_meta.caption,
                    photo_type=photo_meta.photo_type,
                    provenance_id=provenance.id,
                )
                session.add(photo)

            await session.flush()
            await session.refresh(inspection)

            # 5. Load photos onto inspection model for response
            photos_result = await session.execute(
                select(InspectionPhotoModel).where(
                    InspectionPhotoModel.inspection_id == inspection.id
                )
            )
            inspection.photos = list(photos_result.scalars().all())

    # 6. After session commit, dispatch risk recomputation (D-05 trigger #1)
    try:
        from api.tasks.celery_tasks import recompute_structure_risk

        recompute_structure_risk.delay(str(structure_id))
        logger.info(
            "risk_recompute_dispatched",
            structure_id=str(structure_id),
            trigger="inspection_created",
        )
    except Exception:
        logger.warning(
            "risk_recompute_dispatch_failed",
            structure_id=str(structure_id),
        )

    # AI-03: dispatch embedding generation after inspection creation
    try:
        from api.tasks.celery_tasks import generate_structure_embedding
        generate_structure_embedding.delay("inspection", str(inspection.id))
        logger.info(
            "embedding_dispatched",
            inspection_id=str(inspection.id),
            trigger="inspection_created",
        )
    except Exception:
        logger.warning(
            "embedding_dispatch_failed",
            inspection_id=str(inspection.id),
        )

    return inspection


async def get_inspection(
    inspection_id: uuid.UUID,
) -> InspectionModel | None:
    """Retrieve an inspection record by ID with photos.

    Args:
        inspection_id: UUID of the inspection

    Returns:
        InspectionModel with photos loaded if found, None if not found.
    """
    async with async_session() as session:
        result = await session.execute(
            select(InspectionModel).where(InspectionModel.id == inspection_id)
        )
        inspection = result.scalar_one_or_none()
        if inspection is None:
            return None

        # Eagerly load photos
        photos_result = await session.execute(
            select(InspectionPhotoModel).where(
                InspectionPhotoModel.inspection_id == inspection_id
            )
        )
        inspection.photos = list(photos_result.scalars().all())

        return inspection


async def list_inspections(
    structure_id: uuid.UUID,
    offset: int = 0,
    limit: int = 100,
) -> tuple[list, int]:
    """List inspections for a structure with pagination.

    Results are ordered by inspection_date DESC (newest first).
    Each inspection has its photos loaded for presigned URL generation.

    Args:
        structure_id: UUID of the structure
        offset: pagination offset
        limit: max number of results

    Returns:
        Tuple of (list of InspectionModel with photos, total count).
    """
    async with async_session() as session:
        # Count total
        count_stmt = select(func.count()).select_from(InspectionModel).where(
            InspectionModel.structure_id == structure_id
        )
        total = (await session.execute(count_stmt)).scalar() or 0

        # Fetch inspections
        stmt = (
            select(InspectionModel)
            .where(InspectionModel.structure_id == structure_id)
            .order_by(desc(InspectionModel.inspection_date))
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        inspections = list(result.scalars().all())

        # Load photos for each inspection
        for inspection in inspections:
            photos_result = await session.execute(
                select(InspectionPhotoModel).where(
                    InspectionPhotoModel.inspection_id == inspection.id
                )
            )
            inspection.photos = list(photos_result.scalars().all())

        return inspections, total
