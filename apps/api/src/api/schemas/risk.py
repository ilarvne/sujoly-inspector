"""Pydantic schemas for risk assessment endpoints.

Provides:
- RiskAssessmentResponse: full factor breakdown response for GET /structures/{id}/risk
- OverrideRequest: engineer override request with Literal enum fields (D-13, RISK-06)
- OverrideResponse: response with system + override values for audit transparency (D-13)
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RiskAssessmentResponse(BaseModel):
    """Response model for a risk assessment with full factor breakdown (D-04).

    Includes all computed factors for explainability, plus the is_override
    flag and valid_to for time-based history queries.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    structure_id: uuid.UUID
    condition_score: float
    consequence_factor: float
    seasonal_modifier: float
    staleness_modifier: float
    composite_score: float
    inspection_interval: str
    repair_status: str
    red_flags: list = Field(default_factory=list)
    contributing_factors: dict = Field(default_factory=dict)
    is_override: bool = False
    computed_at: datetime
    valid_to: datetime | None = None


class OverrideRequest(BaseModel):
    """Engineer override request with Literal enum fields (D-13, RISK-06).

    Mass assignment protection (T-03-07): only the two overridable fields
    plus a mandatory reason are accepted. No arbitrary field injection.
    """

    inspection_interval: Literal[
        "emergency", "30d", "90d", "180d", "12mo", "24mo"
    ] = Field(..., description="Overridden inspection interval")
    repair_status: Literal[
        "normal", "inspection_required", "repair_required", "critical_condition"
    ] = Field(..., description="Overridden repair status")
    reason: str = Field(
        ..., description="Engineer justification for override"
    )


class OverrideResponse(RiskAssessmentResponse):
    """Response for override endpoint with system + override values (D-13).

    Extends RiskAssessmentResponse with the system-computed values that
    were overridden, extracted from contributing_factors. This ensures
    audit transparency — both system and human decisions are visible.
    """

    system_inspection_interval: str | None = Field(
        None, description="System-computed inspection interval before override"
    )
    system_repair_status: str | None = Field(
        None, description="System-computed repair status before override"
    )
