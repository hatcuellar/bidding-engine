# Multi-stage build for the ad-bidding engine

# Stage 1: Build frontend assets (if needed)
FROM node:20-alpine AS frontend-build
WORKDIR /app
# Only copy what's needed for the frontend build
COPY package*.json ./
COPY tsconfig.json ./
COPY vite.config.ts ./
COPY tailwind.config.ts ./
COPY postcss.config.js ./
COPY ./client ./client

# Install dependencies and build frontend
RUN npm ci
RUN npm run build

# Stage 2: Python application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    python3-dev \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create required directories
RUN mkdir -p /app/models /app/logs

# Copy Python requirements file
COPY pyproject.toml .
COPY uv.lock .

# Install Python dependencies
RUN pip install --no-cache-dir -U pip uv
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Copy frontend build from stage 1
COPY --from=frontend-build /app/dist ./static

# Apply migrations at build time (optional - can be done at runtime)
# RUN alembic upgrade head

# Create and use non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Command to run when container starts
CMD ["bash", "start_fastapi.sh"]
