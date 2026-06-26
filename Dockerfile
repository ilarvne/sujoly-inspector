# Multi-stage build: Next.js frontend + FastAPI backend in one container
# AlemPlus deploy: HTTP port 80, logs to /applogs/app.logs

# ── Stage 1: Build Next.js frontend ──
FROM node:22-alpine AS web-builder
WORKDIR /app/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ── Stage 2: Build FastAPI backend ──
FROM python:3.12-slim AS api-builder
WORKDIR /app/api
RUN pip install --no-cache-dir uv
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev
COPY apps/api/ ./

# ── Stage 3: Runtime — both services ──
FROM node:22-alpine AS runtime

# Install Python, supervisord, curl
RUN apk add --no-cache python3 py3-pip supervisor curl bash && \
    python3 -m pip install --no-cache-dir uv

# Create logs directory (AlemPlus sidecar reads /applogs/app.logs)
RUN mkdir -p /applogs

# Copy built Next.js standalone
WORKDIR /app/web
COPY --from=web-builder /app/web/.next/standalone ./
COPY --from=web-builder /app/web/.next/static ./.next/static
COPY --from=web-builder /app/web/public ./public

# Copy FastAPI app
WORKDIR /app/api
COPY --from=api-builder /app/api/ ./
COPY --from=api-builder /app/api/.venv ./.venv

# Install runtime Python deps
RUN python3 -m pip install --no-cache-dir fastapi uvicorn[standard] httpx structlog pydantic pydantic-settings sqlalchemy[asyncio] geoalchemy2 asyncpg alembic pgvector celery redis minio xlrd openpyxl jinja2 python-multipart PyJWT passlib bcrypt

# Supervisord config — both services, logs to /applogs/app.logs
RUN mkdir -p /etc/supervisor.d
COPY <<'EOF' /etc/supervisor.d/app.ini
[supervisord]
nodaemon=true
logfile=/applogs/supervisord.log

[program:api]
command=python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
directory=/app/api
environment=PYTHONPATH="/app/api/src"
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

# Startup script that tails all logs into /applogs/app.logs for AlemPlus sidecar
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'supervisord -c /etc/supervisor.d/app.ini &' >> /start.sh && \
    echo 'sleep 2' >> /start.sh && \
    echo 'tail -f /applogs/web.log /applogs/api.log /applogs/supervisord.log > /applogs/app.logs 2>&1' >> /start.sh && \
    chmod +x /start.sh

WORKDIR /app

# Cloud infra env vars (overridden by deployment)
ENV PYTHONPATH="/app/api/src" \
    API_DATABASE_URL="postgresql+asyncpg://ilarvne:yOv34H9W0E@a1-postgres1.alem.ai:30100/alemhackdb" \
    API_SYNC_DATABASE_URL="postgresql+psycopg://ilarvne:yOv34H9W0E@a1-postgres1.alem.ai:30100/alemhackdb" \
    API_REDIS_URL="redis://:NyH3Kl8Ankr2wJ22hpGE08jIQLCiwOhrkpAR3ZOu@149.137.233.13:31224/alemhackredis" \
    API_MINIO_ENDPOINT="a1-minio1.alem.ai" \
    API_MINIO_ACCESS_KEY="ilarvne" \
    API_MINIO_SECRET_KEY="60yGeN99Nt" \
    API_MINIO_USE_SSL="true" \
    API_JWT_SECRET="dev-secret-change-me" \
    API_JWT_EXPIRY_HOURS="24" \
    API_INITIAL_ADMIN_USERNAME="admin" \
    API_INITIAL_ADMIN_API_KEY="dev-admin-key" \
    API_ALLOWED_ORIGINS="*" \
    API_LLM_BASE_URL="https://llm.alem.ai/v1" \
    API_LLM_MODEL="alemllm" \
    CHAT_ALEM_API_KEY="sk-VOqLlzi2lsbeK8uDtnpCtQ" \
    CHAT_QWEN_API_KEY="sk-2Qp0gTxxnhQ2SitBXLKfeg" \
    LLM_DEFAULT_API_KEY="sk-VOqLlzi2lsbeK8uDtnpCtQ" \
    API_EMBEDDING_BASE_URL="https://llm.alem.ai/v1" \
    API_EMBEDDING_MODEL="text-1024" \
    API_EMBEDDING_API_KEY="sk-gjHJ15q4DvGwp2eZGS_nhA" \
    API_EMBEDDING_DIMENSIONS="1024" \
    EMBEDDINGS_API_KEY="sk-gjHJ15q4DvGwp2eZGS_nhA" \
    NEXT_PUBLIC_API_URL="/api/v1" \
    API_INTERNAL_URL="http://localhost:8000" \
    PORT="80" \
    HOSTNAME="0.0.0.0"

EXPOSE 80

CMD ["/start.sh"]
