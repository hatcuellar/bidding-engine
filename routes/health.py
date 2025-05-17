from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db

router = APIRouter()

@router.get("/healthz")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify API and database are operational.
    Returns 200 OK if everything is working.
    """
    try:
        # Check database connection by executing a simple query
        db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "api": "ok",
                "database": "ok"
            }
        }
    except Exception as e:
        # If database connection fails, return unhealthy status
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "api": "ok",
                    "database": "error",
                    "error": str(e)
                }
            }
        )
