#!/bin/bash
set -e

echo "Starting PostgreSQL..."
su - postgres -c "pg_ctlcluster 17 main start" 2>/dev/null || true
sleep 5

echo "Creating user/db/extensions..."
su - postgres -c "psql -c \"CREATE USER sujoly WITH PASSWORD 'sujoly_dev' SUPERUSER;\"" 2>/dev/null || true
su - postgres -c "psql -c \"CREATE DATABASE sujoly OWNER sujoly;\"" 2>/dev/null || true
su - postgres -c "psql -d sujoly -c \"CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS postgis_topology; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS vector;\"" 2>/dev/null || true

echo "Pre-seed: migrations + data + coordinates..."
cd /app/api
export PYTHONPATH=/app/api/src
export API_DATABASE_URL="postgresql+asyncpg://sujoly:sujoly_dev@localhost:5432/sujoly"
export API_SYNC_DATABASE_URL="postgresql+psycopg://sujoly:sujoly_dev@localhost:5432/sujoly"
/app/api/.venv/bin/python /app/seed.py pre 2>&1 | tee /applogs/seed.log

echo "Starting services..."
supervisord -c /etc/supervisor/conf.d/app.ini &
sleep 10

echo "Post-seed: risk assessments..."
cd /app/api
export PYTHONPATH=/app/api/src
/app/api/.venv/bin/python /app/seed.py post 2>&1 | tee -a /applogs/seed.log

echo "All started"
tail -f /applogs/web.log /applogs/api.log /applogs/supervisord.log > /applogs/app.logs 2>&1
