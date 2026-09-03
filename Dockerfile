# ==============================================================================
# JobHelperGuru Production Multi-Stage Dockerfile
# Stage 1: Build React Frontend Assets
# Stage 2: Serve Unified FastAPI Service on Render Free Tier
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Frontend Builder
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Build static bundle
COPY frontend/ ./
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS production
WORKDIR /app

# Install system dependencies (curl for container health checks, libpq-dev for PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and initialize local storage directories
COPY backend/ ./backend/
RUN mkdir -p /app/data/uploads

# Copy built frontend assets from Stage 1 into the location expected by FastAPI
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Render assigns port dynamically via $PORT environment variable (defaults to 8000)
EXPOSE 8000

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Start FastAPI via uvicorn binding to 0.0.0.0 and dynamic $PORT
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
