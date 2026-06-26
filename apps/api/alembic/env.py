"""Alembic migration environment for SuJoly Inspector API.

Uses GeoAlchemy2 alembic_helpers for correct spatial type rendering.
Sync database URL comes from settings (not hardcoded in alembic.ini).
Models are registered on Base.metadata by importing api.models.
"""

from logging.config import fileConfig

from alembic import context
from geoalchemy2 import alembic_helpers
from sqlalchemy import engine_from_config, pool

# Import settings to get sync_database_url (overridden from alembic.ini)
from api.config.settings import settings

# Import Base and all models so they register on Base.metadata
from api.infrastructure.database import Base
import api.models  # noqa: F401 — registers ProvenanceModel, StructureModel, StructureFactModel

# This is the Alembic Config object.
config = context.config

# Override sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata

# PostGIS extension tables that ship with the postgis Docker image but are
# not part of our application schema. These must be excluded from autogenerate
# comparisons so `alembic check` doesn't flag them as "removed tables".
_POSTGIS_EXTENSION_TABLES = frozenset({
    # postgis_tiger_geocoder
    "addr", "addrfeat", "bg", "county", "county_lookup", "countysub_lookup",
    "cousub", "direction_lookup", "edges", "faces", "featnames", "geocode_settings",
    "geocode_settings_default", "loader_lookuptables", "loader_platform",
    "loader_variables", "pagc_gaz", "pagc_lex", "pagc_rules", "place",
    "place_lookup", "secondary_unit_lookup", "state", "state_lookup",
    "street_type_lookup", "tabblock", "tabblock20", "tract", "zcta5",
    "zip_lookup", "zip_lookup_all", "zip_lookup_base", "zip_state",
    "zip_state_loc",
    # postgis_topology
    "topology", "layer",
})


# Spatial indexes created via raw SQL (op.execute) that GeoAlchemy2's
# include_object doesn't auto-detect because they don't follow the
# idx_<table>_geom_gist naming convention.
_SPATIAL_INDEXES = frozenset({
    "ix_structures_geometry",
})


def include_object(object, name, type_, reflected, compare_to):
    """Custom include_object that wraps GeoAlchemy2's helper and also excludes
    PostGIS extension tables (Tiger geocoder, topology) and raw-SQL spatial
    indexes that ship with the postgis Docker image but are not part of our
    application schema.
    """
    # First, let GeoAlchemy2's helper handle spatial indexes and its own exclusions
    if not alembic_helpers.include_object(object, name, type_, reflected, compare_to):
        return False
    # Exclude PostGIS extension tables
    if type_ == "table" and name in _POSTGIS_EXTENSION_TABLES:
        return False
    # Exclude raw-SQL spatial indexes (GiST indexes created via op.execute)
    if type_ == "index" and name in _SPATIAL_INDEXES:
        return False
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
        process_revision_directives=alembic_helpers.writer,
        render_item=alembic_helpers.render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to the database.

    Uses GeoAlchemy2 alembic_helpers for correct spatial type handling.
    """
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
            process_revision_directives=alembic_helpers.writer,
            render_item=alembic_helpers.render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
