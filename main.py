import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

from database import engine, Base
from routes import bid, health, metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Multi-Model Ad Bidding Engine API",
    description="A high-performance multi-model ad-bidding engine with FastAPI",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at /docs path
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up OpenTelemetry instrumentation
from utils.observability import setup_opentelemetry, setup_prometheus
setup_opentelemetry(app)

# Set up Prometheus metrics
metrics = setup_prometheus(app)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root route redirects to Swagger UI
@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/docs")
    
# API Guide route
@app.get("/guide", response_class=HTMLResponse)
async def api_guide():
    with open("static/api-guide.html", "r") as f:
        return f.read()

# Include routers
app.include_router(bid.router, prefix="/api/bid", tags=["bid"])
app.include_router(health.router, tags=["health"])
# Metrics router disabled until prometheus package is installed
# from routes import metrics
# app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and connections on startup."""
    try:
        # Create tables if they don't exist (in development)
        # In production, Alembic should handle migrations
        if os.getenv("ENV") == "development":
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully for development")
        
        # Initialize Redis connection pool if available
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            from utils.redis_cache import initialize_redis_pool
            await initialize_redis_pool()
            logger.info("Redis connection pool initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections on shutdown."""
    try:
        # Close Redis connection pool if available
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            from utils.redis_cache import close_redis_pool
            await close_redis_pool()
            logger.info("Redis connection pool closed")
            
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
