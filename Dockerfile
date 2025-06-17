# syntax=docker/dockerfile:1

### Stage 1 → build React ###
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

COPY app/frontend/package*.json ./
RUN npm install

COPY app/frontend/ .
RUN npm run build
# ← after this, /app/frontend/dist contains your production React build

### Stage 2 → build & run FastAPI ###
FROM python:3.11-slim
WORKDIR /app

# Install OS-level deps (for any native Python wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your backend code, database files, and other static assets
COPY app/    ./app
COPY db/     ./db
COPY static/ ./static

# ← **NEW:** pull in the React build into /app/frontend/dist
#     and place it at /app/frontend/dist → but because we're
#     mounting from /app/frontend/dist, we copy it into a top-level
#     "frontend/dist" folder:
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose and launch
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
