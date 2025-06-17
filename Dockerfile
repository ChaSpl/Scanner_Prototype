# syntax=docker/dockerfile:1

### Stage 1: build frontend ###
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY app/frontend/package*.json ./
RUN npm install
COPY app/frontend/ .
RUN npm run build     # output in /app/frontend/dist

### Stage 2: build backend ###
FROM python:3.11-slim
WORKDIR /app

# install any OS-level deps your app needs
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

# copy & install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy your code
COPY app/    ./app
COPY db/     ./db
COPY static/ ./static

# include the built frontend
COPY --from=frontend-build /app/frontend/dist ./app/frontend/dist

# expose port and start
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
