"""User ORM model for RBAC."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class UserModel(Base):
    """Users table for RBAC with four roles."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'engineer', 'inspector', 'viewer')",
            name="ck_users_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
