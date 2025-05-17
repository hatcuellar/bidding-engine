#!/bin/bash

# Enhanced startup script for the ad-bidding engine FastAPI application
# Handles migrations, environment setup, and different deployment scenarios

# Set default values for configuration
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
WORKERS=${WORKERS:-4}
LOG_LEVEL=${LOG_LEVEL:-info}
ENV=${ENV:-production}

echo "Starting Ad-Bidding Engine API..."
echo "Environment: $ENV"
echo "Host: $HOST"
echo "Port: $PORT"

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    if command -v alembic &> /dev/null; then
        alembic upgrade head
    else
        echo "Warning: Alembic not found, skipping migrations"
    fi
}

# Run migrations if enabled (default in production)
if [ "$RUN_MIGRATIONS" = "true" ] || [ "$ENV" = "production" ]; then
    run_migrations
fi

# Start application based on environment
if [ "$ENV" = "development" ] || [ "$ENV" = "dev" ]; then
    echo "Starting FastAPI in development mode (with hot reload)..."
    exec uvicorn main:app --host $HOST --port $PORT --reload --log-level $LOG_LEVEL
else
    echo "Starting FastAPI in production mode with $WORKERS workers..."
    exec uvicorn main:app --host $HOST --port $PORT --workers $WORKERS --log-level $LOG_LEVEL
fi
