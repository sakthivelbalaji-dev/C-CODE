# C Code Lab — production image for Railway (and any Docker host).
# Multi-stage: build React SPA → bake into backend/dist, then FastAPI + gcc judge.

# --- Build SPA (paths must match frontend/vite.config.js outDir: ../backend/dist) ---
FROM node:22-bookworm-slim AS frontend
WORKDIR /repo/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
COPY backend/ /repo/backend/
ENV CI=true
RUN npm run build

# --- Runtime: API, static files, C compiler for /api/judge/c ---
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Use Railway/database env only (no local .env loading in containers)
ENV ENV=production
# dist/ is baked from the frontend stage; skip npm at startup
ENV SKIP_FRONTEND_BUILD=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY --from=frontend /repo/backend/dist /app/backend/dist

WORKDIR /app/backend

# Railway injects PORT; default for local `docker run -p 8080:8080`
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
