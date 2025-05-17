import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from database import engine, Base
from routes import bid, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenTelemetry
resource = Resource(attributes={
    SERVICE_NAME: "ad-bidding-engine"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Set up OTLP exporter if OTLP endpoint is provided
otlp_endpoint = os.getenv("OTLP_ENDPOINT")
if otlp_endpoint:
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    logger.info(f"OpenTelemetry exporter configured with endpoint: {otlp_endpoint}")

# Create FastAPI app
app = FastAPI(
    title="Multi-Model Ad Bidding Engine API",
    description="A high-performance multi-model ad-bidding engine with FastAPI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)

# Include routers
app.include_router(bid.router, prefix="/api/bid", tags=["bid"])
app.include_router(health.router, tags=["health"])

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
