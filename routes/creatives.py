"""
Routes for managing creative assets in the ad bidding system.
Includes functionality for approving creatives via admin routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from typing import Dict, Any, List, Optional
from datetime import datetime

from database import get_db
from models import Creative
from schemas import (
    CreativeResponse, 
    CreativeUpdateRequest,
    CreativeStatusUpdate
)

router = APIRouter(
    prefix="/api/creatives",
    tags=["creatives"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()

# JWT verification functions
def verify_admin_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Verify admin JWT token and return payload if valid.
    
    Args:
        credentials: JWT credentials from Authorization header
        
    Returns:
        Dict containing JWT payload
        
    Raises:
        HTTPException: If JWT is invalid or user doesn't have admin scope
    """
    try:
        # Get token from authorization header
        token = credentials.credentials
        # Verify and decode token
        payload = jwt.decode(
            token, 
            "YOUR_SECRET_KEY",  # Use environment variable in production
            algorithms=["HS256"]
        )
        
        # Check if user has admin scope
        if "scope" not in payload or payload["scope"] != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin access required for this endpoint"
            )
            
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )


@router.get("/{creative_id}", response_model=CreativeResponse)
async def get_creative(
    creative_id: int = Path(..., description="The ID of the creative to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific creative.
    
    Path parameters:
    - creative_id: ID of the creative
    """
    creative = db.query(Creative).filter(Creative.id == creative_id).first()
    
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")
        
    return creative


@router.get("/", response_model=List[CreativeResponse])
async def list_creatives(
    brand_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List creatives with optional filtering.
    
    Query parameters:
    - brand_id: Filter by brand ID
    - status: Filter by status (pending, approved, rejected)
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    """
    query = db.query(Creative)
    
    if brand_id is not None:
        query = query.filter(Creative.brand_id == brand_id)
        
    if status is not None:
        query = query.filter(Creative.status == status)
        
    creatives = query.offset(skip).limit(limit).all()
    return creatives


@router.patch("/{creative_id}", response_model=CreativeResponse)
async def update_creative_status(
    creative_status: CreativeStatusUpdate,
    creative_id: int = Path(..., description="The ID of the creative to update"),
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(verify_admin_jwt)
):
    """
    Admin endpoint to approve or reject creatives.
    
    Path parameters:
    - creative_id: ID of the creative to update
    
    Request body:
    - status: New status ("pending", "approved", or "rejected")
    - reject_reason: Optional reason for rejection
    """
    creative = db.query(Creative).filter(Creative.id == creative_id).first()
    
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")
    
    # Update the creative status
    creative.status = creative_status.status
    
    if creative_status.status == "rejected" and creative_status.reject_reason:
        creative.reject_reason = creative_status.reject_reason
        
    creative.updated_at = datetime.utcnow()
    
    # Record who approved/rejected
    if "sub" in admin:
        creative.reviewed_by = admin["sub"]
    
    db.commit()
    db.refresh(creative)
    
    return creative