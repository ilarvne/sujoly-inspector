"""Barrel export for ORM models.

Importing this package registers all models on Base.metadata so Alembic
can discover them for migration generation.
"""

from api.models.candidate import CandidateModel
from api.models.document import DocumentModel
from api.models.inspection import InspectionModel, InspectionPhotoModel
from api.models.provenance import ProvenanceModel
from api.models.risk_assessment import RiskAssessmentModel
from api.models.structure import StructureFactModel, StructureModel
from api.models.user import UserModel

__all__ = [
    "CandidateModel",
    "DocumentModel",
    "InspectionModel",
    "InspectionPhotoModel",
    "ProvenanceModel",
    "RiskAssessmentModel",
    "StructureFactModel",
    "StructureModel",
    "UserModel",
]
