"""Structure CRUD + multilingual search service — async database operations.

Provides:
- create_structure: create a new structure with provenance
- get_structure: retrieve a structure by ID
- list_structures: list with attribute filters, bbox, pagination, GeoJSON option
- search_structures: combined FTS + pg_trgm fuzzy search with blended score (D-12)
- update_structure: full provenance-per-fact update (D-13)
- delete_structure: soft delete via status field (D-13)

All queries use SQLAlchemy 2.0 parameterized ORM constructs — never string
interpolation for user input (T-02-01 mitigation).
"""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import and_, desc, func, literal_column, or_, select

from api.infrastructure.database import async_session
from api.models.provenance import ProvenanceModel
from api.models.structure import StructureFactModel, StructureModel
from api.schemas.structures import StructureCreate, StructureUpdate

logger = structlog.get_logger(__name__)

# Language → PostgreSQL FTS config mapping (D-10)
_TS_CONFIGS = {"ru": "russian", "kk": "simple", "en": "english"}

# Language → generated tsvector column name (D-10)
_TS_COLUMNS = {"ru": "search_ts_ru", "kk": "search_ts_kk", "en": "search_ts_en"}


def _apply_bbox_filter(stmt, bbox: str | None):
    """Apply bbox spatial filter to a select statement using plain lat/lon (T-02-03 mitigation).

    Parses the bbox string to floats, validates exactly 4 values, and filters
    structures whose latitude/longitude fall within the bounding box.
    Raises ValueError for invalid bbox input — the route layer catches this
    and returns HTTP 400.
    """
    if not bbox:
        return stmt
    parts = bbox.split(",")
    if len(parts) != 4:
        raise ValueError("bbox must contain exactly 4 values: minx,miny,maxx,maxy")
    try:
        minx, miny, maxx, maxy = (float(p) for p in parts)
    except ValueError:
        raise ValueError("bbox values must be numeric") from None
    # Plain lat/lon bounding box filter (no PostGIS required)
    return stmt.where(
        and_(
            StructureModel.latitude.isnot(None),
            StructureModel.longitude.isnot(None),
            StructureModel.latitude.between(miny, maxy),
            StructureModel.longitude.between(minx, maxx),
        )
    )


def _apply_attribute_filters(stmt, filters: dict):
    """Apply attribute filters (type, district, technical_condition, water_source) to a select statement."""
    if filters.get("type"):
        stmt = stmt.where(StructureModel.type == filters["type"])
    if filters.get("district"):
        stmt = stmt.where(StructureModel.district == filters["district"])
    if filters.get("technical_condition"):
        stmt = stmt.where(
            StructureModel.technical_condition == filters["technical_condition"]
        )
    if filters.get("water_source"):
        stmt = stmt.where(StructureModel.water_source == filters["water_source"])
    return stmt


async def create_structure(
    data: StructureCreate, provenance_id: uuid.UUID
) -> StructureModel:
    """Create a new structure record and return it.

    After creation, dispatches embedding generation Celery task (AI-03).

    Args:
        data: StructureCreate with structure fields
        provenance_id: UUID of the provenance record for this structure

    Returns:
        The created StructureModel with generated id and timestamps.
    """
    async with async_session() as session:
        async with session.begin():
            model = StructureModel(
                name_ru=data.name_ru,
                name_kk=data.name_kk,
                name_en=data.name_en,
                type=data.type,
                latitude=data.latitude,
                longitude=data.longitude,
                district=data.district,
                water_source=data.water_source,
                technical_condition=data.technical_condition,
                wear_percentage=data.wear_percentage,
                commissioning_year=data.commissioning_year,
                cadastral_number=data.cadastral_number,
                structure_count=data.structure_count,
                provenance_id=provenance_id,
            )
            session.add(model)
            await session.flush()
            await session.refresh(model)
            structure_id = model.id

    # AI-03: dispatch embedding generation after structure creation
    try:
        from api.tasks.celery_tasks import generate_structure_embedding
        generate_structure_embedding.delay("structure", str(structure_id))
        logger.info("embedding_dispatched", structure_id=str(structure_id), trigger="structure_created")
    except Exception:
        logger.warning("embedding_dispatch_failed", structure_id=str(structure_id))

    return model


async def get_structure(structure_id: uuid.UUID) -> StructureModel | None:
    """Retrieve a structure record by ID.

    Args:
        structure_id: UUID of the structure

    Returns:
        StructureModel if found, None if not found.
    """
    async with async_session() as session:
        result = await session.execute(
            select(StructureModel).where(StructureModel.id == structure_id)
        )
        return result.scalar_one_or_none()


async def list_structures(
    filters: dict,
    q: str | None,
    lang: str,
    bbox: str | None,
    offset: int,
    limit: int,
    format: str = "json",
) -> tuple[list, int]:
    """List structures with filtering, search, bbox, and pagination (D-16).

    If `q` is provided, delegates to search_structures for FTS + trigram search.
    Otherwise, applies attribute filters and bbox spatial filter.

    Args:
        filters: dict with optional keys: type, district, technical_condition, water_source
        q: optional search query (delegates to search if provided)
        lang: language for FTS (ru, kk, en)
        bbox: optional "minx,miny,maxx,maxy" spatial filter
        offset: pagination offset
        limit: max number of results (T-02-05 DoS mitigation: max 1000)
        format: "json" or "geojson" (route-level concern, passed through)

    Returns:
        Tuple of (list of StructureModel, total count).
    """
    if q:
        return await search_structures(
            q=q, lang=lang, filters=filters, bbox=bbox, limit=limit
        )

    async with async_session() as session:
        stmt = select(StructureModel).where(StructureModel.status != "deleted")

        stmt = _apply_attribute_filters(stmt, filters)
        stmt = _apply_bbox_filter(stmt, bbox)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar() or 0

        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total


async def search_structures(
    q: str,
    lang: str,
    filters: dict,
    bbox: str | None,
    limit: int,
) -> tuple[list, int]:
    """Search structures using combined FTS + trigram fuzzy matching (D-12).

    Selects the appropriate tsvector column based on lang (D-10):
    - ru → search_ts_ru with to_tsvector('russian', ...)
    - kk → search_ts_kk with to_tsvector('simple', ...)
    - en → search_ts_en with to_tsvector('english', ...)

    Computes blended_score = fts_rank * 0.7 + greatest(similarity) * 0.3
    per RESEARCH.md D-12.

    WHERE clause: tsvector @@ plainto_tsquery OR name_ru % q OR name_kk % q
    OR name_en % q (pg_trgm % operator with GIN index).

    All user input is parameterized via SQLAlchemy func constructs (T-02-01).

    Args:
        q: search query string
        lang: language for FTS config selection
        filters: dict with optional keys: type, district, technical_condition
        bbox: optional spatial filter
        limit: max number of results (T-02-05: max 100)

    Returns:
        Tuple of (list of (StructureModel, score) tuples, total count).
    """
    ts_config = _TS_CONFIGS.get(lang, "simple")
    ts_col_name = _TS_COLUMNS.get(lang, "search_ts_ru")

    ts_col = literal_column(ts_col_name)
    tsquery = func.plainto_tsquery(ts_config, q)
    fts_rank = func.ts_rank_cd(ts_col, tsquery)

    trigram_best = func.greatest(
        func.similarity(StructureModel.name_ru, q),
        func.similarity(StructureModel.name_kk, q),
        func.similarity(StructureModel.name_en, q),
    )

    blended_score = (fts_rank * 0.7) + (trigram_best * 0.3)

    fts_match = ts_col.op("@@")(tsquery)
    trigram_match_ru = StructureModel.name_ru.op("%")(q)
    trigram_match_kk = StructureModel.name_kk.op("%")(q)
    trigram_match_en = StructureModel.name_en.op("%")(q)

    async with async_session() as session:
        stmt = (
            select(StructureModel, blended_score.label("match_score"))
            .where(
                and_(
                    StructureModel.status != "deleted",
                    or_(
                        fts_match,
                        trigram_match_ru,
                        trigram_match_kk,
                        trigram_match_en,
                    ),
                )
            )
        )

        stmt = _apply_attribute_filters(stmt, filters)
        stmt = _apply_bbox_filter(stmt, bbox)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(desc(blended_score)).limit(limit)
        result = await session.execute(stmt)
        rows = result.all()

        items = [(row[0], float(row[1])) for row in rows]
        return items, total


async def update_structure(
    structure_id: uuid.UUID,
    data: StructureUpdate,
    provenance_id: uuid.UUID,
) -> StructureModel | None:
    """Update a structure with full provenance-per-fact tracking (D-13).

    Implements the provenance-per-fact update pattern:
    1. Fetch existing StructureModel, return None if not found.
    2. Create a new ProvenanceModel (source_type="manual", confidence="HIGH").
    3. Set valid_to=now on all existing structure_facts for this structure.
    4. Create new StructureFactModel rows for each non-None field in data.
    5. Update the StructureModel's non-None fields directly.
    6. Return updated model.

    Args:
        structure_id: UUID of the structure to update
        data: StructureUpdate with only the fields to change (None = skip)
        provenance_id: UUID of the new provenance record for this update

    Returns:
        Updated StructureModel if found, None if structure_id not found.
    """
    now = datetime.utcnow()

    async with async_session() as session:
        async with session.begin():
            # 1. Fetch existing structure
            result = await session.execute(
                select(StructureModel).where(StructureModel.id == structure_id)
            )
            structure = result.scalar_one_or_none()
            if structure is None:
                return None

            # 2. Create new provenance for this update
            new_provenance = ProvenanceModel(
                source_type="manual",
                source_reference=f"api:update:{structure_id}",
                confidence_level="HIGH",
                contributor="api:update",
            )
            session.add(new_provenance)
            await session.flush()

            # 3. Expire existing structure_facts (set valid_to=now)
            facts_result = await session.execute(
                select(StructureFactModel).where(
                    and_(
                        StructureFactModel.structure_id == structure_id,
                        StructureFactModel.valid_to.is_(None),
                    )
                )
            )
            for fact in facts_result.scalars().all():
                fact.valid_to = now

            # 4. Create new structure_facts for each non-None field
            update_fields = data.model_dump(exclude_unset=True)
            field_mapping = {
                "name_ru": "name_ru",
                "name_kk": "name_kk",
                "name_en": "name_en",
                "type": "type",
                "latitude": "latitude",
                "longitude": "longitude",
                "district": "district",
                "water_source": "water_source",
                "technical_condition": "technical_condition",
                "wear_percentage": "wear_percentage",
                "commissioning_year": "commissioning_year",
                "cadastral_number": "cadastral_number",
                "structure_count": "structure_count",
            }

            for field_name, attr_name in field_mapping.items():
                if field_name in update_fields and update_fields[field_name] is not None:
                    new_fact = StructureFactModel(
                        structure_id=structure_id,
                        attribute_name=attr_name,
                        attribute_value={"value": update_fields[field_name]},
                        provenance_id=new_provenance.id,
                        valid_from=now,
                    )
                    session.add(new_fact)

            # 5. Update the StructureModel's non-None fields directly
            for field_name, value in update_fields.items():
                if value is not None and field_name in field_mapping:
                    setattr(structure, field_name, value)

            structure.provenance_id = new_provenance.id
            structure.updated_at = now

            await session.flush()
            await session.refresh(structure)

            # D-05 trigger 2: dispatch risk recomputation after structure update
            try:
                from api.tasks.celery_tasks import recompute_structure_risk
                recompute_structure_risk.delay(str(structure_id))
            except Exception:
                logger.warning("risk_recompute_dispatch_failed", structure_id=str(structure_id))

            # AI-03: dispatch embedding generation after structure creation
            try:
                from api.tasks.celery_tasks import generate_structure_embedding
                generate_structure_embedding.delay("structure", str(structure_id))
            except Exception:
                logger.warning("embedding_dispatch_failed", structure_id=str(structure_id))

            return structure


async def delete_structure(structure_id: uuid.UUID) -> bool:
    """Soft delete a structure by setting status='deleted' (D-13).

    Args:
        structure_id: UUID of the structure to delete

    Returns:
        True if the structure was found and soft-deleted, False if not found.
    """
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(StructureModel).where(StructureModel.id == structure_id)
            )
            structure = result.scalar_one_or_none()
            if structure is None:
                return False
            structure.status = "deleted"
            return True
