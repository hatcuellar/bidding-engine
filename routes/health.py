from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import os
import logging

from database import get_db
from schemas import HealthResponse

logger = logging.getLogger(__name__)

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
            # Import here to avoid circular imports
            from utils.redis_cache import get_cached_feature, set_cached_feature
            
            # Simple check using SET/GET operations
            test_key = "health:check"
            await set_cached_feature(test_key, "ok", ttl=60)  # 1 minute TTL
            result = await get_cached_feature(test_key)
            if result == "ok":
                components["redis"] = "ok"
            else:
                components["redis"] = "error"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
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
