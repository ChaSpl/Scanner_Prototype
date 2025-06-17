# syntax=docker/dockerfile:1

### Stage 1 → build React ###
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

COPY app/frontend/package*.json ./
RUN npm install

COPY app/frontend/ .
RUN npm run build
# now /app/frontend/dist contains your static site

### Stage 2 → build & run FastAPI ###
FROM python:3.11-slim
WORKDIR /app

# OS deps for any native wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy code + DB + static
COPY app/    ./app
COPY db/     ./db
COPY static/ ./static

# copy the built frontend into a top-level `frontend/dist`
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# expose & launch
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
