"""Candidate REST endpoints — CRUD + discovery + review.

Provides:
- GET /api/v1/candidates: list with filters (match_status, source_type, confidence)
- GET /api/v1/candidates/{id}: detail
- POST /api/v1/candidates/discover: trigger OSM discovery with bbox parameter
- POST /api/v1/candidates/{id}/review: review endpoint (accept/link/reject)
- DELETE /api/v1/candidates/{id}: remove candidate
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies.auth import require_role
from api.models.user import UserModel
from api.schemas.candidates import (
    CandidateListResponse,
    CandidateResponse,
    CandidateReviewRequest,
)
from api.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/api/v1", tags=["candidates"])


def _model_to_response(model) -> CandidateResponse:
    """Convert CandidateModel to CandidateResponse with geometry serialization."""
    from geoalchemy2.shape import to_shape

    data = {
        "id": model.id,
        "name": model.name,
        "source_type": model.source_type,
        "source_id": model.source_id,
        "match_status": model.match_status,
        "matched_structure_id": model.matched_structure_id,
        "confidence": model.confidence,
        "confidence_score": model.confidence_score,
        "evidence": model.evidence,
        "district": model.district,
        "water_source": model.water_source,
        "type": model.type,
        "review_notes": model.review_notes,
        "reviewed_by": model.reviewed_by,
        "reviewed_at": model.reviewed_at,
        "provenance_id": model.provenance_id,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }
    # Convert geometry to GeoJSON dict
    if model.geometry is not None:
        try:
            geom = to_shape(model.geometry)
            data["geometry"] = geom.__geo_interface__
        except Exception:
            data["geometry"] = None
    else:
        data["geometry"] = None

    return CandidateResponse(**data)


async def _list_candidates_from_db(
    match_status: str | None,
    source_type: str | None,
    confidence: str | None,
    offset: int,
    limit: int,
) -> tuple[list, int]:
    """List candidates with optional filters and pagination."""
    from sqlalchemy import func, select

    from api.infrastructure.database import async_session
    from api.models.candidate import CandidateModel

    async with async_session() as session:
        stmt = select(CandidateModel)

        if match_status:
            stmt = stmt.where(CandidateModel.match_status == match_status)
        if source_type:
            stmt = stmt.where(CandidateModel.source_type == source_type)
        if confidence:
            stmt = stmt.where(CandidateModel.confidence == confidence)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(CandidateModel.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total


async def _get_candidate_by_id(candidate_id: uuid.UUID):
    """Get a candidate by ID, return None if not found."""
    from sqlalchemy import select

    from api.infrastructure.database import async_session
    from api.models.candidate import CandidateModel

    async with async_session() as session:
        result = await session.execute(
            select(CandidateModel).where(CandidateModel.id == candidate_id)
        )
        return result.scalar_one_or_none()


async def _delete_candidate_by_id(candidate_id: uuid.UUID) -> bool:
    """Delete a candidate by ID. Returns True if deleted, False if not found."""
    from sqlalchemy import select

    from api.infrastructure.database import async_session
    from api.models.candidate import CandidateModel

    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(CandidateModel).where(CandidateModel.id == candidate_id)
            )
            candidate = result.scalar_one_or_none()
            if candidate is None:
                return False
            await session.delete(candidate)
            return True


async def _review_candidate(
    candidate_id: uuid.UUID,
    review: CandidateReviewRequest,
    reviewer_id: uuid.UUID,
):
    """Update candidate with review decision."""
    from sqlalchemy import select

    from api.infrastructure.database import async_session
    from api.models.candidate import CandidateModel

    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(CandidateModel).where(CandidateModel.id == candidate_id)
            )
            candidate = result.scalar_one_or_none()
            if candidate is None:
                return None

            candidate.match_status = review.match_status
            candidate.matched_structure_id = review.matched_structure_id
            candidate.review_notes = review.review_notes
            candidate.reviewed_by = reviewer_id
            candidate.reviewed_at = datetime.now(timezone.utc)

            await session.flush()
            await session.refresh(candidate)
            return candidate


@router.get("/candidates", response_model=CandidateListResponse)
async def list_candidates_endpoint(
    match_status: str | None = None,
    source_type: str | None = None,
    confidence: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
):
    """List candidates with optional filters and pagination."""
    items, total = await _list_candidates_from_db(
        match_status=match_status,
        source_type=source_type,
        confidence=confidence,
        offset=offset,
        limit=limit,
    )
    return CandidateListResponse(
        items=[_model_to_response(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate_endpoint(candidate_id: uuid.UUID):
    """Retrieve a candidate record by ID."""
    candidate = await _get_candidate_by_id(candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found",
        )
    return _model_to_response(candidate)


@router.post(
    "/candidates/discover",
    response_model=CandidateListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def discover_candidates_endpoint(
    bbox: str = Query(..., description="Bounding box: minx,miny,maxx,maxy (EPSG:4326)"),
    source: str = Query("osm", description="Discovery source (currently only 'osm')"),
    current_user: UserModel = Depends(require_role("engineer")),
):
    """Trigger OSM discovery for hydraulic structures in a bounding box.

    Queries the OSM Overpass API for hydraulic structure candidates within the
    specified bounding box. Deduplicates against existing candidates by source_id.
    Returns the list of newly created candidates.
    """
    service = DiscoveryService()
    try:
        candidates = await service.discover_candidates(bbox=bbox, source=source)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Discovery source error: {str(exc)}",
        )

    return CandidateListResponse(
        items=[_model_to_response(c) for c in candidates],
        total=len(candidates),
        offset=0,
        limit=len(candidates),
    )


@router.post("/candidates/{candidate_id}/review", response_model=CandidateResponse)
async def review_candidate_endpoint(
    candidate_id: uuid.UUID,
    body: CandidateReviewRequest,
    current_user: UserModel = Depends(require_role("engineer")),
):
    """Review a candidate — accept/link/reject the match.

    Updates match_status, matched_structure_id, review_notes, reviewed_at.
    If match_status is 'matched' or 'likely_match' with matched_structure_id,
    optionally update the structure's geometry if candidate has coords and
    structure doesn't.
    """
    candidate = await _review_candidate(
        candidate_id=candidate_id,
        review=body,
        reviewer_id=current_user.id,
    )
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found",
        )
    return _model_to_response(candidate)


@router.delete("/candidates/{candidate_id}")
async def delete_candidate_endpoint(
    candidate_id: uuid.UUID,
    current_user: UserModel = Depends(require_role("admin")),
):
    """Delete a candidate record.

    Requires admin role. Returns 404 if candidate not found.
    """
    deleted = await _delete_candidate_by_id(candidate_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found",
        )
    return {"status": "deleted"}
