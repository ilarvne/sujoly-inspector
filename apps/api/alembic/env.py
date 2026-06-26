"""Alembic migration environment for SuJoly Inspector API.

Uses plain SQLAlchemy configuration (no GeoAlchemy2 helpers needed —
we removed PostGIS dependency in favor of plain Float lat/lon columns).
Sync database URL comes from settings (not hardcoded in alembic.ini).
Models are registered on Base.metadata by importing api.models.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import settings to get sync_database_url (overridden from alembic.ini)
from api.config.settings import settings

# Import Base and all models so they register on Base.metadata
from api.infrastructure.database import Base
import api.models  # noqa: F401 — registers all ORM models on Base.metadata

# This is the Alembic Config object.
config = context.config

# Override sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Custom include_object that excludes extension tables from autogenerate.

    No PostGIS extension tables to exclude anymore, but keeping the hook
    for future extension tables (e.g. pg_trgm catalog tables).
    """
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to the database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
