"""
API routes for ROAS (Return on Ad Spend) prediction and performance tracking.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import json

from database import get_db
from models import BidHistory, EventLog
from schemas import ROASPredictionRequest, ROASPredictionResponse, PerformanceEventRequest
from utils.roas_predictor import get_roas_predictor

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/roas", response_model=ROASPredictionResponse)
async def get_roas_prediction(
    brand_id: int,
    partner_id: int, 
    ad_slot_id: int,
    device_type: Optional[int] = None,
    creative_type: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get predicted ROAS (Return on Ad Spend) for a specific brand-partner-slot combination.
    
    This endpoint is used for reporting and forecasting purposes.
    
    Parameters:
    - brand_id: ID of the advertiser
    - partner_id: ID of the publisher partner
    - ad_slot_id: ID of the ad placement
    - device_type: Optional device type (0=unknown, 1=desktop, 2=mobile, 3=tablet)
    - creative_type: Optional creative type (0=unknown, 1=image, 2=video, 3=native)
    """
    try:
        # Prepare prediction request
        data = {
            "brand_id": brand_id,
            "partner_id": partner_id,
            "ad_slot_id": ad_slot_id,
            "device_type": device_type or 0,
            "creative_type": creative_type or 0,
            "placement_score": 50  # Default placement score
        }
        
        # Get ROAS predictor and make prediction
        predictor = get_roas_predictor()
        vpi = predictor.predict(data)
        
        # Calculate estimated ROAS
        # ROAS = Revenue / Cost, but since we're predicting VPI (value per impression),
        # we need to convert it to an estimated ROAS ratio
        estimated_roas = vpi * 100.0  # Simple conversion for demo purposes
        
        # Get historical data for this combination if available
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        history = db.query(
            BidHistory
        ).filter(
            BidHistory.brand_id == brand_id,
            BidHistory.partner_id == partner_id,
            BidHistory.ad_slot_id == ad_slot_id,
            BidHistory.bid_timestamp >= seven_days_ago
        ).order_by(
            BidHistory.bid_timestamp.desc()
        ).limit(100).all()
        
        # Calculate actual ROAS from history if we have data
        total_revenue = 0.0
        total_cost = 0.0
        total_impressions = 0
        
        for record in history:
            total_revenue += record.revenue
            total_cost += record.cost
            total_impressions += record.impressions
        
        actual_roas = 0.0
        if total_cost > 0:
            actual_roas = total_revenue / total_cost
        
        # Return combined prediction and history data
        return {
            "brand_id": brand_id,
            "partner_id": partner_id,
            "ad_slot_id": ad_slot_id,
            "predicted_vpi": vpi,
            "estimated_roas": estimated_roas,
            "actual_roas": actual_roas,
            "historical_impressions": total_impressions,
            "historical_revenue": total_revenue,
            "historical_cost": total_cost,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in ROAS prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error making ROAS prediction: {str(e)}"
        )

@router.post("/performance", status_code=status.HTTP_201_CREATED)
async def ingest_performance_event(
    event: PerformanceEventRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest actual click, impression, and conversion events to update the feature store.
    
    This endpoint receives performance data from the Partnerize platform to update
    the historical data used for ROAS predictions. Events are deduplicated based on event_id.
    
    Request body contains:
    - event_id: Unique identifier for deduplication
    - type: Type of event (impression, click, conversion)
    - brand_id: ID of the advertiser
    - partner_id: ID of the publisher partner
    - ad_slot_id: ID of the ad placement
    - timestamp: When the event occurred
    - metadata: Additional information about the event
    - revenue: Optional revenue amount (for conversions)
    """
    try:
        # Check if this event has already been processed (deduplicate)
        existing_event = db.query(EventLog).filter(
            EventLog.event_id == event.event_id
        ).first()
        
        if existing_event:
            logger.info(f"Duplicate event detected, skipping: {event.event_id}")
            return {
                "status": "success", 
                "message": "Event already processed",
                "duplicate": True
            }
        
        # Find the most recent bid for this combination
        recent_bid = db.query(BidHistory).filter(
            BidHistory.brand_id == event.brand_id,
            BidHistory.partner_id == event.partner_id,
            BidHistory.ad_slot_id == event.ad_slot_id,
            BidHistory.bid_timestamp <= event.timestamp
        ).order_by(
            BidHistory.bid_timestamp.desc()
        ).first()
        
        if not recent_bid:
            # Create a new record if no existing bid is found
            recent_bid = BidHistory(
                brand_id=event.brand_id,
                partner_id=event.partner_id,
                ad_slot_id=event.ad_slot_id,
                bid_amount=0.0,
                normalized_value=0.0,
                quality_factor=1.0,
                bid_type="CPM",
                bid_timestamp=event.timestamp
            )
            db.add(recent_bid)
        
        # Update the bid history record based on event type
        if event.type == "impression":
            recent_bid.impressions += 1
            recent_bid.cost += recent_bid.bid_amount / 1000.0  # CPM cost
            
            # Extract device and creative information if available
            if event.metadata and "device_type" in event.metadata:
                recent_bid.device_type = event.metadata["device_type"]
            
            if event.metadata and "creative_type" in event.metadata:
                recent_bid.creative_type = event.metadata["creative_type"]
            
            if event.metadata and "placement_score" in event.metadata:
                recent_bid.placement_score = event.metadata["placement_score"]
                
        elif event.type == "click":
            recent_bid.clicks += 1
            
            # If CPC bid, update cost
            if recent_bid.bid_type == "CPC":
                recent_bid.cost += recent_bid.bid_amount
                
        elif event.type == "conversion":
            recent_bid.conversions += 1
            
            # If CPA bid, update cost
            if recent_bid.bid_type == "CPA":
                recent_bid.cost += recent_bid.bid_amount
            
            # Update revenue if provided
            if event.revenue is not None:
                recent_bid.revenue += event.revenue
        
        # Calculate CTR and CVR
        if recent_bid.impressions > 0:
            recent_bid.ctr = recent_bid.clicks / recent_bid.impressions
            
            if recent_bid.clicks > 0:
                recent_bid.cvr = recent_bid.conversions / recent_bid.clicks
        
        # Log this event to prevent reprocessing (deduplicate future attempts)
        event_log = EventLog(
            event_id=event.event_id,
            event_type=event.type,
            brand_id=event.brand_id,
            partner_id=event.partner_id,
            ad_slot_id=event.ad_slot_id
        )
        db.add(event_log)
        
        # Commit all changes
        db.commit()
        
        return {
            "status": "success", 
            "message": "Performance event processed",
            "duplicate": False
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing performance event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing performance event: {str(e)}"
        )

@router.post("/retrain")
async def retrain_roas_model(db: Session = Depends(get_db)):
    """
    Trigger retraining of the ROAS prediction model using latest performance data.
    
    This endpoint is typically called by a scheduled job but can also be
    manually triggered for immediate retraining.
    """
    try:
        # Get the ROAS predictor and retrain
        predictor = get_roas_predictor()
        success = predictor.train(db)
        
        if success:
            return {
                "status": "success", 
                "message": "ROAS model retrained successfully"
            }
        else:
            return {
                "status": "error", 
                "message": "Failed to retrain ROAS model - see logs for details"
            }
    
    except Exception as e:
        logger.error(f"Error retraining ROAS model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retraining ROAS model: {str(e)}"
        )