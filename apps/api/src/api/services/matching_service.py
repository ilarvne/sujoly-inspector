"""Hierarchical matching engine — spatial + name + attribute matching.

Provides:
- match_candidate: match a single candidate against the registry
  using hierarchical spatial → name similarity → attribute comparison
- match_all_unmatched: batch processing for all unmatched candidates
- compute_confidence: weighted confidence scoring formula

Match state assignment (DISC-03):
- matched: spatial < 100m AND name_sim > 0.7 → HIGH confidence
- likely_match: spatial < 500m AND name_sim > 0.3 → MEDIUM confidence
- new_candidate: no structures within 500m → LOW confidence
- conflict: spatial < 100m but name/type mismatch → LOW confidence

Confidence formula (DISC-06):
score = 0.4 * name_sim + 0.3 * (1 - spatial_dist/500) + 0.3 * (attr_matches/3)
HIGH >= 0.7, MEDIUM >= 0.4, LOW < 0.4
"""

import uuid

import structlog
from geoalchemy2 import functions as geofunc
from sqlalchemy import and_, func, select, update

from api.infrastructure.database import async_session
from api.models.candidate import CandidateModel
from api.models.structure import StructureModel
from api.schemas.candidates import CandidateMatchResult

logger = structlog.get_logger(__name__)


class MatchingService:
    """Hierarchical matching engine for comparing candidates against the registry.

    Implements the three-level matching strategy from DISC-02:
    1. Spatial proximity: ST_DWithin 500m radius
    2. Name similarity: pg_trgm similarity() > 0.3 threshold
    3. Attribute comparison: type, district, water_source match

    Produces four-state match assignment per DISC-03:
    - matched, likely_match, new_candidate, conflict
    """

    async def match_candidate(
        self, candidate: CandidateModel
    ) -> CandidateMatchResult:
        """Match a single candidate against the registry.

        Hierarchical matching:
        1. Find structures within 500m using ST_DWithin
        2. Compute name similarity using pg_trgm similarity()
        3. Compare attributes (type, district, water_source)
        4. Assign match state and confidence

        Args:
            candidate: CandidateModel to match against the registry.

        Returns:
            CandidateMatchResult with assigned match_status and confidence.
        """
        if candidate.geometry is None:
            # No geometry → can't do spatial matching → new_candidate
            return CandidateMatchResult(
                candidate_id=candidate.id,
                match_status="new_candidate",
                confidence="LOW",
                confidence_score=0.0,
                matched_structure_id=None,
                evidence={"reason": "no_geometry", "spatial": None, "name_sim": None, "attr_matches": 0},
            )

        async with async_session() as session:
            # Step 1: Spatial proximity — find structures within 500m
            nearby_stmt = select(
                StructureModel,
                geofunc.ST_Distance(
                    geofunc.ST_Transform(StructureModel.geometry, 3857),
                    geofunc.ST_Transform(candidate.geometry, 3857),
                ).label("distance_m"),
            ).where(
                and_(
                    StructureModel.geometry.isnot(None),
                    StructureModel.status != "deleted",
                    geofunc.ST_DWithin(
                        geofunc.ST_Transform(StructureModel.geometry, 3857),
                        geofunc.ST_Transform(candidate.geometry, 3857),
                        500,  # meters
                    ),
                )
            )

            nearby_result = await session.execute(nearby_stmt)
            nearby_structures = nearby_result.all()

        if not nearby_structures:
            # No structures within 500m → new_candidate
            return CandidateMatchResult(
                candidate_id=candidate.id,
                match_status="new_candidate",
                confidence="LOW",
                confidence_score=0.0,
                matched_structure_id=None,
                evidence={
                    "reason": "no_nearby_structures",
                    "spatial": None,
                    "name_sim": None,
                    "attr_matches": 0,
                },
            )

        # Step 2: For each nearby structure, compute name similarity + attribute comparison
        best_match = None
        best_score = -1.0
        best_evidence = {}

        for structure, distance_m in nearby_structures:
            distance = float(distance_m) if distance_m is not None else 500.0

            # Name similarity: pg_trgm similarity against all name columns
            name_sim = 0.0
            async with async_session() as session:
                for name_col in [StructureModel.name_ru, StructureModel.name_kk, StructureModel.name_en]:
                    sim_result = await session.execute(
                        select(func.similarity(name_col, candidate.name)).where(
                            StructureModel.id == structure.id
                        )
                    )
                    sim_val = sim_result.scalar()
                    if sim_val is not None and sim_val > name_sim:
                        name_sim = float(sim_val)

            # Attribute comparison: type, district, water_source
            attr_matches = 0
            if candidate.type and structure.type and candidate.type == structure.type:
                attr_matches += 1
            if candidate.district and structure.district and candidate.district == structure.district:
                attr_matches += 1
            if candidate.water_source and structure.water_source and candidate.water_source == structure.water_source:
                attr_matches += 1

            # Compute confidence
            confidence_level, score = compute_confidence(
                spatial_dist=distance,
                name_sim=name_sim,
                attr_matches=attr_matches,
            )

            evidence = {
                "spatial_distance_m": round(distance, 1),
                "name_similarity": round(name_sim, 3),
                "attribute_matches": attr_matches,
                "structure_id": str(structure.id),
                "structure_name_ru": structure.name_ru,
            }

            if score > best_score:
                best_score = score
                best_match = structure
                best_evidence = evidence

        # Step 3: Determine match state based on thresholds
        distance = best_evidence.get("spatial_distance_m", 500.0)
        name_sim = best_evidence.get("name_similarity", 0.0)

        if distance < 100 and name_sim > 0.7:
            match_status = "matched"
        elif distance < 500 and name_sim > 0.3:
            match_status = "likely_match"
        elif distance < 100 and (name_sim <= 0.3 or best_evidence.get("attribute_matches", 0) == 0):
            match_status = "conflict"
        else:
            match_status = "likely_match" if name_sim > 0.3 else "new_candidate"

        confidence_level, score = compute_confidence(
            spatial_dist=distance,
            name_sim=name_sim,
            attr_matches=best_evidence.get("attribute_matches", 0),
        )

        # Override confidence level based on match state
        if match_status == "matched":
            confidence_level = "HIGH" if score >= 0.7 else "MEDIUM"
        elif match_status == "conflict":
            confidence_level = "LOW"
        elif match_status == "new_candidate":
            confidence_level = "LOW"

        best_evidence["match_status_assigned"] = match_status

        return CandidateMatchResult(
            candidate_id=candidate.id,
            match_status=match_status,
            confidence=confidence_level,
            confidence_score=round(score, 3),
            matched_structure_id=best_match.id if best_match else None,
            evidence=best_evidence,
        )

    async def match_all_unmatched(self) -> list[CandidateMatchResult]:
        """Run matching for all unmatched candidates.

        1. Load all candidates with match_status="unmatched"
        2. For each, run match_candidate
        3. Update candidate records with results
        4. Return results

        Returns:
            List of CandidateMatchResult for all matched candidates.
        """
        async with async_session() as session:
            result = await session.execute(
                select(CandidateModel).where(
                    CandidateModel.match_status == "unmatched"
                )
            )
            candidates = list(result.scalars().all())

        results = []
        for candidate in candidates:
            match_result = await self.match_candidate(candidate)
            results.append(match_result)

            # Update candidate with match result
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

        logger.info(
            "matching_complete",
            total_candidates=len(candidates),
            results=len(results),
        )
        return results


def compute_confidence(
    spatial_dist: float, name_sim: float, attr_matches: int
) -> tuple[str, float]:
    """Compute confidence level and score from signals (DISC-06).

    Weighted formula:
    score = 0.4 * name_sim + 0.3 * (1 - spatial_dist/500) + 0.3 * (attr_matches/3)

    Level:
    HIGH if score >= 0.7
    MEDIUM if score >= 0.4
    LOW otherwise

    Args:
        spatial_dist: distance in meters to nearest structure (0-500+)
        name_sim: pg_trgm similarity score (0.0-1.0)
        attr_matches: count of matching attributes (0-3: type, district, water_source)

    Returns:
        Tuple of (confidence_level: str, confidence_score: float)
    """
    # Clamp spatial distance to 500 max for scoring
    clamped_dist = min(spatial_dist, 500.0)

    score = (
        0.4 * name_sim
        + 0.3 * (1.0 - clamped_dist / 500.0)
        + 0.3 * (attr_matches / 3.0)
    )

    # Clamp score to [0, 1]
    score = max(0.0, min(1.0, score))

    if score >= 0.7:
        return "HIGH", score
    elif score >= 0.4:
        return "MEDIUM", score
    else:
        return "LOW", score
