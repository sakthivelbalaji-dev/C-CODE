FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install gcc for C judge

RUN apt-get update 
&& apt-get install -y --no-install-recommends gcc build-essential 
&& rm -rf /var/lib/apt/lists/*


# Install Python dependencies

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend (includes dist folder)

COPY backend /app/backend

WORKDIR /app/backend

ENV SKIP_FRONTEND_BUILD=1

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
