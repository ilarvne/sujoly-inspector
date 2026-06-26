"""Risk assessment REST endpoints — GET risk, POST override, POST recompute.

Provides:
- GET /api/v1/structures/{id}/risk: retrieve latest risk assessment (D-04)
- POST /api/v1/structures/{id}/override: engineer override with provenance (D-13, RISK-06)
- POST /api/v1/structures/{id}/recompute: manual risk recomputation (D-05 trigger 4)

RBAC:
- GET risk: any authenticated user
- POST override: engineer+ role (require_role("engineer"))
- POST recompute: engineer+ role (require_role("engineer"))
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies.auth import require_role
from api.models.user import UserModel
from api.schemas.risk import (
    OverrideRequest,
    OverrideResponse,
    RiskAssessmentResponse,
)
from api.services import risk_service, structure_service

router = APIRouter(prefix="/api/v1", tags=["risk"])


@router.get("/structures/{structure_id}/risk", response_model=RiskAssessmentResponse)
async def get_risk_assessment(structure_id: uuid.UUID) -> RiskAssessmentResponse:
    """Retrieve the latest risk assessment for a structure (D-04).

    Returns 404 if the structure does not exist or no assessment is available.
    """
    # Verify structure exists
    structure = await structure_service.get_structure(structure_id)
    if structure is None or structure.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure '{structure_id}' not found",
        )

    assessment = await risk_service.get_latest_assessment(structure_id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk assessment found for this structure",
        )
    return RiskAssessmentResponse.model_validate(assessment)


@router.post("/structures/{structure_id}/override", response_model=OverrideResponse)
async def override_risk_assessment(
    structure_id: uuid.UUID,
    body: OverrideRequest,
    current_user: UserModel = Depends(require_role("engineer")),
) -> OverrideResponse:
    """Engineer override of risk assessment with provenance (D-13, RISK-06).

    Requires engineer+ role. Creates ProvenanceModel with source_type="manual",
    confidence_level="HIGH", contributor=current_user.username per T-03-08.
    Both system-computed and override values are stored for audit transparency.
    """
    # Verify structure exists
    structure = await structure_service.get_structure(structure_id)
    if structure is None or structure.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure '{structure_id}' not found",
        )

    result = await risk_service.create_override(
        structure_id=structure_id,
        override_interval=body.inspection_interval,
        override_status=body.repair_status,
        override_reason=body.reason,
        user=current_user,
    )

    # Build OverrideResponse with system values extracted from contributing_factors
    base_data = RiskAssessmentResponse.model_validate(result).model_dump()
    factors = result.contributing_factors if isinstance(result.contributing_factors, dict) else {}
    base_data["system_inspection_interval"] = factors.get("system_inspection_interval")
    base_data["system_repair_status"] = factors.get("system_repair_status")
    return OverrideResponse(**base_data)


@router.post("/structures/{structure_id}/recompute", response_model=RiskAssessmentResponse)
async def recompute_risk_assessment(
    structure_id: uuid.UUID,
    current_user: UserModel = Depends(require_role("engineer")),
) -> RiskAssessmentResponse:
    """Manual risk recomputation per D-05 trigger 4.

    Requires engineer+ role. Calls risk_service.recompute_risk_for_structure
    which loads structure+facts+inspections, calls risk_engine.compute_risk(),
    and persists the result.
    """
    # Verify structure exists
    structure = await structure_service.get_structure(structure_id)
    if structure is None or structure.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure '{structure_id}' not found",
        )

    try:
        result = await risk_service.recompute_risk_for_structure(structure_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return RiskAssessmentResponse.model_validate(result)
