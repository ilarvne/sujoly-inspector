# Simple deploy: just Next.js frontend with mock data
# AlemPlus: port 80, logs to /applogs/app.logs

FROM node:22-alpine AS builder
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm install --legacy-peer-deps
COPY apps/web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS runtime
RUN apk add --no-cache bash
RUN mkdir -p /applogs
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

ENV NODE_ENV=production
ENV PORT=80
ENV HOSTNAME=0.0.0.0

# Start script: run Next.js, tail logs to /applogs/app.logs
RUN printf '#!/bin/bash\nnode server.js > /applogs/web.log 2>&1 &\nsleep 2\ntail -f /applogs/web.log > /applogs/app.logs 2>&1\n' > /start.sh && chmod +x /start.sh

EXPOSE 80
CMD ["/start.sh"]
