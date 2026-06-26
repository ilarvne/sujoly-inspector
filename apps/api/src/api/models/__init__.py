"""Barrel export for ORM models.

Importing this package registers all models on Base.metadata so Alembic
can discover them for migration generation.
"""

from api.models.provenance import ProvenanceModel
from api.models.structure import StructureFactModel, StructureModel
from api.models.user import UserModel

__all__ = ["ProvenanceModel", "StructureModel", "StructureFactModel", "UserModel"]
