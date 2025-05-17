#!/bin/bash

# Start FastAPI application with uvicorn
# This script can be used for local development or deployment

# Set default port if not provided
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

# Check if running in development mode
if [ "$ENV" = "development" ] || [ "$ENV" = "dev" ]; then
    echo "Starting FastAPI in development mode (with hot reload)..."
    exec uvicorn main:app --host $HOST --port $PORT --reload
else
    echo "Starting FastAPI in production mode..."
    exec uvicorn main:app --host $HOST --port $PORT --workers 4
fi
