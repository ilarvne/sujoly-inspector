# Multi-stage build: Next.js + FastAPI + local PostgreSQL with PostGIS
# AlemPlus: port 80, logs to /applogs/app.logs, self-contained with DB + seed

# ── Stage 1: Build Next.js frontend ──
FROM node:22-alpine AS web-builder
WORKDIR /app/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm install --legacy-peer-deps
COPY apps/web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ── Stage 2: Build FastAPI backend ──
FROM python:3.12-slim AS api-builder
WORKDIR /app/api
RUN pip install --no-cache-dir uv
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY apps/api/ ./
RUN uv sync --frozen --no-dev

# ── Stage 3: Runtime — PostgreSQL + FastAPI + Next.js ──
FROM python:3.12-slim AS runtime

# Install PostgreSQL 17 + PostGIS + pgvector, Node.js 22, supervisord
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl supervisor bash gnupg lsb-release ca-certificates \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       postgresql-17 postgresql-17-postgis-3 postgresql-17-postgis-3-scripts \
       postgresql-17-pgvector \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /applogs

# Copy Next.js standalone
WORKDIR /app/web
COPY --from=web-builder /app/web/.next/standalone ./
COPY --from=web-builder /app/web/.next/static ./.next/static
COPY --from=web-builder /app/web/public ./public

# Copy FastAPI app + venv
WORKDIR /app/api
COPY --from=api-builder /app/api/ ./

# Copy seed script and Excel dataset
COPY seed.py /app/seed.py
COPY датасет.xls /app/датасет.xls

# Setup PostgreSQL: create user, db, extensions
RUN pg_createcluster 17 main --start 2>/dev/null || true
RUN su - postgres -c "psql -c \"CREATE USER sujoly WITH PASSWORD 'sujoly_dev' SUPERUSER;\"" 2>/dev/null || true
RUN su - postgres -c "psql -c \"CREATE DATABASE sujoly OWNER sujoly;\"" 2>/dev/null || true
RUN su - postgres -c "psql -d sujoly -c \"CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS postgis_topology; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS vector;\"" 2>/dev/null || true

# Supervisord config
RUN mkdir -p /etc/supervisor/conf.d
COPY <<'EOF' /etc/supervisor/conf.d/app.ini
[supervisord]
nodaemon=true
logfile=/applogs/supervisord.log

[program:postgres]
command=/usr/lib/postgresql/17/bin/postgres -D /var/lib/postgresql/17/main -c config_file=/etc/postgresql/17/main/postgresql.conf
user=postgres
autostart=true
autorestart=true
stdout_logfile=/applogs/pg.log
stderr_logfile=/applogs/pg-err.log

[program:api]
command=/app/api/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
directory=/app/api
environment=PYTHONPATH="/app/api/src",API_DATABASE_URL="postgresql+asyncpg://sujoly:sujoly_dev@localhost:5432/sujoly",API_SYNC_DATABASE_URL="postgresql+psycopg://sujoly:sujoly_dev@localhost:5432/sujoly",API_REDIS_URL="redis://:NyH3Kl8Ankr2wJ22hpGE08jIQLCiwOhrkpAR3ZOu@149.137.233.13:31224/alemhackredis",API_MINIO_ENDPOINT="a1-minio1.alem.ai",API_MINIO_ACCESS_KEY="ilarvne",API_MINIO_SECRET_KEY="60yGeN99Nt",API_MINIO_USE_SSL="true",API_JWT_SECRET="dev-secret-change-me",API_JWT_EXPIRY_HOURS="24",API_INITIAL_ADMIN_USERNAME="admin",API_INITIAL_ADMIN_API_KEY="dev-admin-key",API_ALLOWED_ORIGINS="*",API_LLM_BASE_URL="https://llm.alem.ai/v1",API_LLM_MODEL="alemllm",CHAT_ALEM_API_KEY="sk-VOqLlzi2lsbeK8uDtnpCtQ",CHAT_QWEN_API_KEY="sk-2Qp0gTxxnhQ2SitBXLKfeg",LLM_DEFAULT_API_KEY="sk-VOqLlzi2lsbeK8uDtnpCtQ",API_EMBEDDING_BASE_URL="https://llm.alem.ai/v1",API_EMBEDDING_MODEL="text-1024",API_EMBEDDING_API_KEY="sk-gjHJ15q4DvGwp2eZGS_nhA",API_EMBEDDING_DIMENSIONS="1024",EMBEDDINGS_API_KEY="sk-gjHJ15q4DvGwp2eZGS_nhA"
autostart=true
autorestart=true
stdout_logfile=/applogs/api.log
stderr_logfile=/applogs/api-err.log

[program:web]
command=node server.js
directory=/app/web
environment=NODE_ENV="production",PORT="80",HOSTNAME="0.0.0.0",API_INTERNAL_URL="http://localhost:8000"
autostart=true
autorestart=true
stdout_logfile=/applogs/web.log
stderr_logfile=/applogs/web-err.log
EOF

# Start script: start postgres, pre-seed, start services, post-seed, tail logs
RUN printf '#!/bin/bash\nset -e\necho "Starting PostgreSQL..."\nsu - postgres -c "pg_ctlcluster 17 main start" 2>/dev/null || true\nsleep 3\necho "Pre-seed: migrations + data + coordinates..."\ncd /app/api && PYTHONPATH=/app/api/src API_DATABASE_URL="postgresql+asyncpg://sujoly:sujoly_dev@localhost:5432/sujoly" API_SYNC_DATABASE_URL="postgresql+psycopg://sujoly:sujoly_dev@localhost:5432/sujoly" /app/api/.venv/bin/python /app/seed.py pre 2>&1 | tee /applogs/seed.log\necho "Starting services..."\nsupervisord -c /etc/supervisor/conf.d/app.ini &\nsleep 8\necho "Post-seed: risk assessments..."\ncd /app/api && PYTHONPATH=/app/api/src /app/api/.venv/bin/python /app/seed.py post 2>&1 | tee -a /applogs/seed.log\necho "All started"\ntail -f /applogs/web.log /applogs/api.log /applogs/supervisord.log > /applogs/app.logs 2>&1\n' > /start.sh && chmod +x /start.sh

WORKDIR /app

EXPOSE 80

CMD ["/start.sh"]
