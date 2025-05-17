#!/bin/bash
# Start Multi-Model Predictive Bidding System with FastAPI

echo "Starting Multi-Model Predictive Bidding System with FastAPI..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Python not found. Please install Python 3.x"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set default port if not provided
export PORT=${PORT:-8000}

# Start the FastAPI application
echo "Starting FastAPI server on port $PORT..."
python -m uvicorn main:app --host 0.0.0.0 --port $PORT --reload