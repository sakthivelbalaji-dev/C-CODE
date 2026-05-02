# ----------- FRONTEND BUILD STAGE -----------

FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Install frontend dependencies
COPY frontend/package.json /app/frontend/package.json
RUN npm --prefix frontend install

# Copy frontend source
COPY frontend /app/frontend

# Build frontend → outputs to backend/dist
RUN mkdir -p /app/backend/dist
RUN npm --prefix frontend run build

# ----------- BACKEND STAGE -----------

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (C toolchain for judge)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Backend code
COPY backend /app/backend

# Built UI from previous stage
COPY --from=frontend-builder /app/backend/dist /app/backend/dist

WORKDIR /app/backend

ENV SKIP_FRONTEND_BUILD=1

EXPOSE 8080

# Railway sets PORT; default 8080 for local runs
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
