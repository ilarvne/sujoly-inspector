"""create users table

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-26

Creates the users table for JWT-based RBAC (D-10):
- id (UUID PK)
- username (unique, indexed)
- role (enum: admin/engineer/inspector/viewer)
- full_name (nullable)
- api_key (nullable, indexed)
- created_at

Role constrained via CheckConstraint to the four RBAC roles.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Uuid

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users table with role check constraint and indexes."""
    op.create_table(
        "users",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("api_key", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('admin', 'engineer', 'inspector', 'viewer')",
            name="ck_users_role",
        ),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_api_key", "users", ["api_key"])


def downgrade() -> None:
    """Drop users table and indexes."""
    op.drop_index("ix_users_api_key", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
