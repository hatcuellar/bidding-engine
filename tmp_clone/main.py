"""
Multi-Model Predictive Bidding System - FastAPI Application

This is the main application file that integrates the bidding engine with FastAPI.
"""

import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional

# Import the bidding router
from bid.routes import router as bid_router

# Create FastAPI application
app = FastAPI(
    title="Multi-Model Predictive Bidding Engine",
    description="An advanced bidding system that supports CPA, CPC, and CPM models",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the bidding router
app.include_router(bid_router, prefix="/api")

# Initialize database
@app.on_event("startup")
async def startup_db_client():
    from flask import Flask
    flask_app = Flask(__name__)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with flask_app.app_context():
        from models import initialize_db, db
        initialize_db(flask_app)
        db.create_all()

# Healthcheck endpoint
@app.get("/healthz", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns a 200 OK response if the service is running.
    """
    return {"status": "healthy", "version": "1.0.0"}

# Mount static files (for the frontend) - will be uncommented once frontend is built
# app.mount("/", StaticFiles(directory="client/dist", html=True), name="static")

# For development, this conditional allows running the server directly
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)