#!/bin/bash
# Start Multi-Model Predictive Bidding System

echo "Starting Multi-Model Predictive Bidding System..."

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

# Verify required packages
echo "Checking required packages..."
python -c "import flask, sqlalchemy, psycopg2, dotenv" &> /dev/null || {
    echo "Installing required packages..."
    pip install flask flask-sqlalchemy psycopg2-binary python-dotenv
}

# Set environment variables if .env file exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
else
    echo "Warning: .env file not found. Make sure DATABASE_URL is set."
fi

# Start the bidding system
echo "Starting Python Flask server..."
python run_bidding_system.py