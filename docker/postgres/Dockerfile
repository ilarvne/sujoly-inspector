# syntax=docker/dockerfile:1
# Custom PostgreSQL image with PostGIS + pgvector extensions.
# postgis/postgis:17-3.5 provides PostGIS; pgvector is installed from PGDG apt.
# The PGDG apt repository is already configured in the base image.

FROM postgis/postgis:17-3.5

# Install pgvector extension from PGDG apt repository
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-17-pgvector && \
    rm -rf /var/lib/apt/lists/*

# Copy init-extensions.sql into entrypoint initdb directory
COPY init-extensions.sql /docker-entrypoint-initdb.d/
