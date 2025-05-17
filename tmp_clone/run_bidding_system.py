"""
Multi-Model Predictive Bidding System Runner

This script starts the Flask application for the multi-model predictive bidding system.
It initializes the database and serves the application on port 8080.

Usage:
  python run_bidding_system.py
"""

import os
import sys
import socket
from flask import Flask
from models import db, initialize_db, create_sample_data
from run import app  # Import the Flask app from run.py

def check_port(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    """Main entry point for running the bidding system"""
    print("Starting Multi-Model Predictive Bidding System...")
    
    # Initialize database if needed
    with app.app_context():
        initialize_db(app)
        db.create_all()  # Create tables if they don't exist
        
        # Check if we have sample data
        from models import Brand
        if Brand.query.count() == 0:
            print("Initializing sample data...")
            create_sample_data()
            print("Sample data created successfully.")
    
    # Configure port
    port = int(os.environ.get('BIDDING_PORT', 8080))
    
    # Check if port is in use
    if check_port(port):
        print(f"Warning: Port {port} is already in use. Trying another port.")
        port = 8081
        if check_port(port):
            print(f"Error: Port {port} is also in use. Please specify an available port.")
            sys.exit(1)
    
    # Start the Flask application
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    main()