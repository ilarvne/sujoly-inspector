"""Risk assessment persistence service — async database operations (D-04).

Provides:
- get_latest_assessment: fetch current risk assessment (valid_to IS NULL)
- create_assessment: persist new assessment, expire previous
- create_override: engineer override with provenance per D-13
- recompute_risk_for_structure: load data → call risk_engine → persist

All queries use SQLAlchemy 2.0 parameterized ORM constructs.
Override creates ProvenanceModel with source_type="manual", confidence_level="HIGH",
and contributor=user.username per T-03-08 (repudiation mitigation).
"""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import and_, select

from api.infrastructure.database import async_session
from api.models.provenance import ProvenanceModel
from api.models.risk_assessment import RiskAssessmentModel
from api.models.structure import StructureFactModel, StructureModel
from api.services import risk_engine

logger = structlog.get_logger(__name__)

# Late import guard for InspectionModel (from Plan 03-05, Wave 3).
# Full risk accuracy requires all waves complete. The try/except guard
# ensures the system is functional at every wave boundary.
_InspectionModel = None


def _get_inspection_model():
    """Lazily import InspectionModel if available (Wave 3 dependency)."""
    global _InspectionModel
    if _InspectionModel is None:
        try:
            from api.models.inspection import InspectionModel
            _InspectionModel = InspectionModel
        except ImportError:
            logger.warning("InspectionModel not available — risk computation proceeds without inspection data")
    return _InspectionModel


async def get_latest_assessment(
    structure_id: uuid.UUID,
) -> RiskAssessmentModel | None:
    """Fetch the current risk assessment for a structure (valid_to IS NULL).

    Args:
        structure_id: UUID of the structure

    Returns:
        RiskAssessmentModel if found, None if no current assessment exists.
    """
    async with async_session() as session:
        result = await session.execute(
            select(RiskAssessmentModel).where(
                and_(
                    RiskAssessmentModel.structure_id == structure_id,
                    RiskAssessmentModel.valid_to.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()


async def create_assessment(
    structure_id: uuid.UUID,
    assessment: risk_engine.RiskAssessment,
    provenance_id: uuid.UUID,
) -> RiskAssessmentModel:
    """Persist a new risk assessment, expiring the previous one.

    Sets valid_to=now on any existing current assessment (valid_to IS NULL),
    then creates a new RiskAssessmentModel from the RiskAssessment dataclass.

    Args:
        structure_id: UUID of the structure
        assessment: RiskAssessment dataclass from risk_engine.compute_risk()
        provenance_id: UUID of the provenance record for this assessment

    Returns:
        The newly created RiskAssessmentModel.
    """
    now = datetime.utcnow()

    async with async_session() as session:
        async with session.begin():
            # Expire existing current assessment
            existing_result = await session.execute(
                select(RiskAssessmentModel).where(
                    and_(
                        RiskAssessmentModel.structure_id == structure_id,
                        RiskAssessmentModel.valid_to.is_(None),
                    )
                )
            )
            for existing in existing_result.scalars().all():
                existing.valid_to = now

            # Create new assessment
            model = RiskAssessmentModel(
                structure_id=structure_id,
                condition_score=assessment.condition_score,
                consequence_factor=assessment.consequence_factor,
                seasonal_modifier=assessment.seasonal_modifier,
                staleness_modifier=assessment.staleness_modifier,
                composite_score=assessment.composite_score,
                inspection_interval=assessment.inspection_interval,
                repair_status=assessment.repair_status,
                red_flags=assessment.red_flags,
                contributing_factors=assessment.contributing_factors,
                provenance_id=provenance_id,
                is_override=False,
                computed_at=now,
            )
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return model


async def create_override(
    structure_id: uuid.UUID,
    override_interval: str,
    override_status: str,
    override_reason: str,
    user,
) -> RiskAssessmentModel:
    """Create an engineer override assessment with provenance (D-13, RISK-06).

    Implements the provenance-per-fact override pattern (RESEARCH.md Pattern 3):
    1. Fetch current assessment to get system-computed values.
    2. Expire current assessment (set valid_to=now).
    3. Create ProvenanceModel(source_type="manual", confidence_level="HIGH",
       contributor=user.username) per T-03-08.
    4. Create new RiskAssessmentModel with is_override=True, override values
       for inspection_interval/repair_status, and system values preserved
       in contributing_factors with override_reason and overridden_by.

    Args:
        structure_id: UUID of the structure
        override_interval: Engineer-chosen inspection interval
        override_status: Engineer-chosen repair status
        override_reason: Engineer justification text
        user: Authenticated UserModel with username attribute

    Returns:
        The newly created override RiskAssessmentModel.
    """
    now = datetime.utcnow()

    async with async_session() as session:
        async with session.begin():
            # 1. Fetch current assessment to get system-computed values
            current_result = await session.execute(
                select(RiskAssessmentModel).where(
                    and_(
                        RiskAssessmentModel.structure_id == structure_id,
                        RiskAssessmentModel.valid_to.is_(None),
                    )
                )
            )
            current = current_result.scalar_one_or_none()

            # Default system values if no assessment exists yet
            system_interval = current.inspection_interval if current else "24mo"
            system_status = current.repair_status if current else "normal"
            system_factors = dict(current.contributing_factors) if current else {}

            # 2. Expire current assessment
            if current is not None:
                current.valid_to = now

            # 3. Create provenance for this override
            provenance = ProvenanceModel(
                source_type="manual",
                source_reference=f"api:override:{structure_id}",
                confidence_level="HIGH",
                contributor=user.username,
            )
            session.add(provenance)
            await session.flush()

            # 4. Build contributing_factors with system values preserved
            override_factors = {
                **system_factors,
                "system_inspection_interval": system_interval,
                "system_repair_status": system_status,
                "override_reason": override_reason,
                "overridden_by": user.username,
            }

            # Use existing factor values from current assessment if available,
            # otherwise use defaults
            condition_score = current.condition_score if current else 50.0
            consequence_factor = current.consequence_factor if current else 1.0
            seasonal_modifier = current.seasonal_modifier if current else 1.0
            staleness_modifier = current.staleness_modifier if current else 1.0
            composite_score = current.composite_score if current else 50.0

            # 5. Create new override assessment
            model = RiskAssessmentModel(
                structure_id=structure_id,
                condition_score=condition_score,
                consequence_factor=consequence_factor,
                seasonal_modifier=seasonal_modifier,
                staleness_modifier=staleness_modifier,
                composite_score=composite_score,
                inspection_interval=override_interval,
                repair_status=override_status,
                red_flags=list(current.red_flags) if current else [],
                contributing_factors=override_factors,
                provenance_id=provenance.id,
                is_override=True,
                computed_at=now,
            )
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return model


async def recompute_risk_for_structure(
    structure_id: uuid.UUID,
) -> RiskAssessmentModel:
    """Load structure data and recompute risk assessment (D-05).

    Loads:
    - StructureModel for type, wear, condition
    - StructureFactModel (valid_to IS NULL) for additional attributes
    - InspectionModel (if available from Wave 3) for staleness

    Calls risk_engine.compute_risk() with the loaded data, creates a
    ProvenanceModel(source_type="system", confidence_level="MEDIUM"),
    and persists via create_assessment.

    Args:
        structure_id: UUID of the structure to recompute

    Returns:
        The newly created RiskAssessmentModel.

    Raises:
        ValueError: If the structure is not found.
    """
    async with async_session() as session:
        # Load structure
        struct_result = await session.execute(
            select(StructureModel).where(StructureModel.id == structure_id)
        )
        structure = struct_result.scalar_one_or_none()
        if structure is None:
            raise ValueError(f"Structure '{structure_id}' not found")

        # Load provenance for confidence level (D-09 weak-evidence floor)
        prov_result = await session.execute(
            select(ProvenanceModel).where(ProvenanceModel.id == structure.provenance_id)
        )
        provenance = prov_result.scalar_one_or_none()

        # Load current facts (valid_to IS NULL)
        facts_result = await session.execute(
            select(StructureFactModel).where(
                and_(
                    StructureFactModel.structure_id == structure_id,
                    StructureFactModel.valid_to.is_(None),
                )
            )
        )
        facts = facts_result.scalars().all()
        facts_dicts = [
            {"attribute_name": f.attribute_name, "attribute_value": f.attribute_value}
            for f in facts
        ]

        # Load inspections if available (Wave 3 dependency — late import)
        inspections_dicts: list[dict] = []
        InspectionModel = _get_inspection_model()
        if InspectionModel is not None:
            insp_result = await session.execute(
                select(InspectionModel)
                .where(InspectionModel.structure_id == structure_id)
                .order_by(InspectionModel.inspection_date.desc())
            )
            inspections = insp_result.scalars().all()
            inspections_dicts = [
                {
                    "inspection_date": i.inspection_date,
                    "findings": i.findings,
                    "condition_score_at_inspection": getattr(
                        i, "condition_score_at_inspection", None
                    ),
                }
                for i in inspections
            ]

        # Convert structure to dict for risk_engine
        structure_dict = {
            "type": structure.type,
            "wear_percentage": structure.wear_percentage,
            "technical_condition": structure.technical_condition,
            "provenance_confidence": provenance.confidence_level if provenance else None,
        }

        # Compute risk using pure Python risk engine
        assessment = risk_engine.compute_risk(
            structure=structure_dict,
            facts=facts_dicts,
            inspections=inspections_dicts,
        )

    # Create provenance and persist assessment
    async with async_session() as session:
        async with session.begin():
            provenance = ProvenanceModel(
                source_type="system",
                source_reference=f"api:recompute:{structure_id}",
                confidence_level="MEDIUM",
                contributor="risk_engine",
            )
            session.add(provenance)
            await session.flush()

    return await create_assessment(
        structure_id=structure_id,
        assessment=assessment,
        provenance_id=provenance.id,
    )
