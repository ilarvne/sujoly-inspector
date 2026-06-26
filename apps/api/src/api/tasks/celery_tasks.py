"""Celery task definitions for the SuJoly Inspector API.

Tasks:
- health_check_task: verify Celery + Redis are working
- ingest_kazvodhoz: bulk ingest Kazvodhoz spreadsheet (D-17)
- recompute_structure_risk: event-driven risk recomputation for one structure (D-05)
- recompute_all_risks: daily bulk recomputation for all structures (D-05 trigger 3)
- run_discovery_pipeline: discover candidates from OSM and auto-match against registry
- generate_structure_embedding: generate embedding for a single structure (AI-03)
- generate_all_embeddings: batch generate embeddings for all unembedded records (AI-03)
"""

import asyncio
import uuid
from datetime import datetime, timezone

import structlog

from api.celery_app import celery_app
from api.services.ingestion_service import bulk_insert_structures

logger = structlog.get_logger(__name__)


@celery_app.task
def health_check_task():
    """Simple task to verify Celery + Redis are working.

    Returns a dict with status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@celery_app.task(bind=True, name="ingest_kazvodhoz")
def ingest_kazvodhoz_task(self, filepath: str = "датасет.xls", force: bool = False):
    """Ingest Kazvodhoz spreadsheet into PostGIS.

    Uses sync psycopg connection for efficient bulk loading (D-17).
    Idempotent: checks source_reference in provenance before inserting (D-19).

    Args:
        self: Celery task instance (bind=True)
        filepath: Path to the .xls spreadsheet file
        force: If True, re-ingest existing records instead of skipping

    Returns:
        dict with "inserted", "skipped", "total" keys
    """
    return bulk_insert_structures(filepath=filepath, force=force)


@celery_app.task(name="recompute_structure_risk")
def recompute_structure_risk(structure_id: str):
    """Recompute risk assessment for a single structure (D-05).

    Celery tasks are synchronous — uses asyncio.run() to call the async
    risk_service.recompute_risk_for_structure. This task is triggered by:
    - D-05 trigger 1: after new inspection (from inspection_service)
    - D-05 trigger 2: after structure update (from structure_service)
    - D-05 trigger 4: manual API call (from /structures/{id}/recompute endpoint)

    Args:
        structure_id: UUID string of the structure to recompute

    Returns:
        dict with structure_id and new assessment id
    """
    from api.services import risk_service as _risk_service

    result = asyncio.run(
        _risk_service.recompute_risk_for_structure(uuid.UUID(structure_id))
    )
    return {"structure_id": structure_id, "assessment_id": str(result.id)}


@celery_app.task(name="recompute_all_risks")
def recompute_all_risks():
    """Daily bulk risk recomputation for all structures (D-05 trigger 3).

    Loads all active structure IDs from the database and dispatches
    a recompute_structure_risk task for each one. Scheduled via
    Celery Beat at 2 AM UTC daily.

    Returns:
        dict with total count of structures dispatched for recomputation
    """
    from api.infrastructure.database import async_session
    from api.models.structure import StructureModel as _StructureModel
    from sqlalchemy import select

    async def _load_structure_ids():
        async with async_session() as session:
            result = await session.execute(
                select(_StructureModel.id).where(
                    _StructureModel.status != "deleted"
                )
            )
            return [str(row[0]) for row in result.all()]

    structure_ids = asyncio.run(_load_structure_ids())
    count = 0
    for sid in structure_ids:
        recompute_structure_risk.delay(sid)
        count += 1

    return {"dispatched": count, "timestamp": datetime.now(timezone.utc).isoformat()}


@celery_app.task(name="discovery.run_pipeline")
def run_discovery_pipeline(bbox: str, source: str = "osm"):
    """Full discovery pipeline: discover → match → score.

    1. Run OSM discovery for bbox
    2. For each new candidate, run matching against the registry
    3. Return summary of results

    Celery tasks are synchronous — uses asyncio.run() for async service calls.

    Args:
        bbox: Bounding box in "minx,miny,maxx,maxy" format (EPSG:4326).
        source: Discovery source (currently only "osm" supported).

    Returns:
        dict with discovery and matching summary statistics.
    """
    from api.services.discovery_service import DiscoveryService
    from api.services.matching_service import MatchingService

    async def _run_pipeline():
        # Step 1: Discover candidates from OSM
        discovery_svc = DiscoveryService()
        candidates = await discovery_svc.discover_candidates(bbox=bbox, source=source)

        # Step 2: Match each new candidate against the registry
        matching_svc = MatchingService()
        match_results = []
        for candidate in candidates:
            match_result = await matching_svc.match_candidate(candidate)
            match_results.append(match_result)

            # Update candidate with match result
            from sqlalchemy import update
            from api.infrastructure.database import async_session
            from api.models.candidate import CandidateModel

            async with async_session() as session:
                async with session.begin():
                    await session.execute(
                        update(CandidateModel)
                        .where(CandidateModel.id == candidate.id)
                        .values(
                            match_status=match_result.match_status,
                            confidence=match_result.confidence,
                            confidence_score=match_result.confidence_score,
                            matched_structure_id=match_result.matched_structure_id,
                            evidence=match_result.evidence,
                        )
                    )

        # Step 3: Summarize results
        status_counts = {}
        for mr in match_results:
            status_counts[mr.match_status] = status_counts.get(mr.match_status, 0) + 1

        return {
            "discovered": len(candidates),
            "matched_summary": status_counts,
            "results": [
                {
                    "candidate_id": str(mr.candidate_id),
                    "match_status": mr.match_status,
                    "confidence": mr.confidence,
                    "confidence_score": mr.confidence_score,
                    "matched_structure_id": str(mr.matched_structure_id) if mr.matched_structure_id else None,
                }
                for mr in match_results
            ],
        }

    result = asyncio.run(_run_pipeline())
    logger.info(
        "discovery_pipeline_complete",
        discovered=result["discovered"],
        matched_summary=result["matched_summary"],
    )
    return result


@celery_app.task(name="embeddings.generate_structure")
def generate_structure_embedding(source_type: str, source_id: str):
    """Generate embedding for a single record (structure, inspection, or document).

    Triggered automatically after structure/inspection/document creation.

    Args:
        source_type: One of "structure", "inspection", "document".
        source_id: UUID string of the source record.

    Returns:
        dict with source_type, source_id, and embedding_id or error.
    """
    from api.services.embedding_service import embedding_service

    async def _embed():
        if source_type == "structure":
            result = await embedding_service.embed_structure(uuid.UUID(source_id))
        elif source_type == "inspection":
            result = await embedding_service.embed_inspection(uuid.UUID(source_id))
        elif source_type == "document":
            result = await embedding_service.embed_document(uuid.UUID(source_id))
        else:
            logger.error("unknown_embedding_source_type", source_type=source_type)
            return {"source_type": source_type, "source_id": source_id, "error": "unknown_source_type"}

        if result is not None:
            return {
                "source_type": source_type,
                "source_id": source_id,
                "embedding_id": str(result.id),
            }
        return {"source_type": source_type, "source_id": source_id, "error": "not_found_or_empty"}

    result = asyncio.run(_embed())
    logger.info(
        "embedding_generated",
        source_type=source_type,
        source_id=source_id,
        result=result,
    )
    return result


@celery_app.task(name="embeddings.generate_all")
def generate_all_embeddings():
    """Batch generate embeddings for all unembedded records.

    Runs embed_all_structures and embed_all_inspections sequentially.

    Returns:
        dict with counts of newly embedded structures and inspections.
    """
    from api.services.embedding_service import embedding_service

    async def _embed_all():
        structures_count = await embedding_service.embed_all_structures()
        inspections_count = await embedding_service.embed_all_inspections()
        return {
            "structures_embedded": structures_count,
            "inspections_embedded": inspections_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    result = asyncio.run(_embed_all())
    logger.info(
        "all_embeddings_generated",
        structures=result["structures_embedded"],
        inspections=result["inspections_embedded"],
    )
    return result
