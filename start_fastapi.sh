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

# Create required directories
mkdir -p models
mkdir -p migrations/versions

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    if command -v alembic &> /dev/null; then
        # Initialize alembic if not already initialized
        if [ ! -f "alembic.ini" ]; then
            echo "Initializing Alembic..."
            alembic init migrations
        fi
        alembic upgrade head
    else
        echo "Warning: Alembic not found, using SQLAlchemy create_all instead"
        python -c "
from database import Base, engine
import models
Base.metadata.create_all(bind=engine)
print('Created database tables using SQLAlchemy')
"
    fi
}

# Check database connection
check_database() {
    echo "Checking database connection..."
    python -c "
import os
import time
import psycopg2
import sys

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print('DATABASE_URL not set. Please set it to connect to PostgreSQL.')
    sys.exit(1)

for i in range(5):  # Try 5 times
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        print('Database connection successful')
        sys.exit(0)
    except Exception as e:
        print(f'Database connection attempt {i+1} failed: {e}')
        if i < 4:  # Don't sleep on the last attempt
            time.sleep(2)
sys.exit(1)  # Exit with error if all attempts fail
"
    if [ $? -ne 0 ]; then
        echo "Warning: Database connection failed"
    fi
}

# Run migrations if enabled (default in production)
check_database
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
