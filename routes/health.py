from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import os

from database import get_db
from schemas import HealthResponse
from utils.redis_cache import get_redis_client

router = APIRouter()

@router.get("/healthz", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify API and database are operational.
    Returns 200 OK if everything is working.
    """
    components = {
        "api": "ok",
    }
    
    # Check database connection
    try:
        # Check database connection by executing a simple query
        db.execute(text("SELECT 1"))
        components["database"] = "ok"
    except Exception as e:
        components["database"] = "error"
        
    # Check Redis connection if configured
    if os.getenv("REDIS_URL"):
        try:
            redis = await get_redis_client()
            if redis:
                await redis.ping()
                components["redis"] = "ok"
            else:
                components["redis"] = "error"
        except Exception:
            components["redis"] = "error"
    
    # Determine overall status
    is_healthy = all(v == "ok" for k, v in components.items() if k != "redis")
    
    if not is_healthy:
        # If any critical component fails, return unhealthy status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": components
            }
        )
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": components
    }
