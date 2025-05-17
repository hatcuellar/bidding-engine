from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import time
import logging
from opentelemetry import trace
from opentelemetry.trace import get_tracer

from database import get_db
from bidding_engine import bidding_engine
import models

router = APIRouter()
logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)

@router.post("/calculate")
async def calculate_bid(
    request: Request,
    bid_request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Calculate bid value based on provided parameters.
    
    Body parameters:
    - brand_id: ID of the brand/advertiser
    - bid_amount: Original bid amount
    - bid_type: Type of bid (CPA, CPC, CPM)
    - ad_slot: Information about the ad placement
    """
    start_time = time.time()
    
    with tracer.start_as_current_span("calculate_bid"):
        try:
            # Input validation
            if "brand_id" not in bid_request:
                raise HTTPException(status_code=400, detail="brand_id is required")
            if "bid_amount" not in bid_request:
                raise HTTPException(status_code=400, detail="bid_amount is required")
            if "bid_type" not in bid_request:
                raise HTTPException(status_code=400, detail="bid_type is required")
                
            # Get brand strategy from database
            brand_id = bid_request.get("brand_id")
            brand_strategy = db.query(models.BrandStrategy).filter(
                models.BrandStrategy.brand_id == brand_id,
                models.BrandStrategy.is_active == True
            ).first()
            
            # Add strategy to bid_request if available
            if brand_strategy:
                try:
                    strategy_config = {}
                    if brand_strategy.strategy_config:
                        import json
                        strategy_config = json.loads(brand_strategy.strategy_config)
                    
                    strategy_config.update({
                        "vpi_multiplier": brand_strategy.vpi_multiplier,
                        "priority": brand_strategy.priority
                    })
                    
                    bid_request["strategy"] = strategy_config
                except Exception as e:
                    logger.error(f"Error parsing strategy config: {e}")
            
            # Process the bid
            result = await bidding_engine.process_bid(bid_request)
            
            # Record bid in history
            try:
                bid_history = models.BidHistory(
                    brand_id=brand_id,
                    ad_slot_id=bid_request.get("ad_slot", {}).get("id", 0),
                    bid_amount=bid_request.get("bid_amount", 0),
                    normalized_value=result.get("normalized_value", 0),
                    quality_factor=result.get("quality_factor", 1.0),
                    ctr=result.get("ctr", 0),
                    cvr=result.get("cvr", 0),
                    bid_type=bid_request.get("bid_type", "CPM")
                )
                db.add(bid_history)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to record bid history: {e}")
                db.rollback()
                
            # Add performance metrics
            process_time = time.time() - start_time
            result["process_time_ms"] = round(process_time * 1000, 2)
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing bid: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/history/{brand_id}")
async def get_bid_history(
    brand_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get bid history for a specific brand.
    
    Path parameters:
    - brand_id: ID of the brand/advertiser
    
    Query parameters:
    - limit: Number of records to return (default 10)
    """
    with tracer.start_as_current_span("get_bid_history"):
        try:
            history = db.query(models.BidHistory).filter(
                models.BidHistory.brand_id == brand_id
            ).order_by(
                models.BidHistory.bid_timestamp.desc()
            ).limit(limit).all()
            
            return {
                "brand_id": brand_id,
                "history": [
                    {
                        "id": h.id,
                        "ad_slot_id": h.ad_slot_id,
                        "bid_amount": h.bid_amount,
                        "normalized_value": h.normalized_value,
                        "quality_factor": h.quality_factor,
                        "ctr": h.ctr,
                        "cvr": h.cvr,
                        "bid_type": h.bid_type,
                        "timestamp": h.bid_timestamp.isoformat()
                    }
                    for h in history
                ]
            }
        except Exception as e:
            logger.error(f"Error retrieving bid history: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/strategy")
async def update_brand_strategy(
    strategy: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Create or update brand bidding strategy.
    
    Body parameters:
    - brand_id: ID of the brand/advertiser
    - vpi_multiplier: Value-per-impression multiplier
    - priority: Priority level for the brand
    - strategy_config: Additional configuration as JSON
    """
    with tracer.start_as_current_span("update_brand_strategy"):
        try:
            brand_id = strategy.get("brand_id")
            if not brand_id:
                raise HTTPException(status_code=400, detail="brand_id is required")
                
            # Check if strategy exists
            existing = db.query(models.BrandStrategy).filter(
                models.BrandStrategy.brand_id == brand_id,
                models.BrandStrategy.is_active == True
            ).first()
            
            if existing:
                # Update existing strategy
                existing.vpi_multiplier = strategy.get("vpi_multiplier", existing.vpi_multiplier)
                existing.priority = strategy.get("priority", existing.priority)
                if "strategy_config" in strategy:
                    existing.strategy_config = strategy.get("strategy_config")
                db.commit()
                return {"message": "Strategy updated successfully", "id": existing.id}
            else:
                # Create new strategy
                new_strategy = models.BrandStrategy(
                    brand_id=brand_id,
                    vpi_multiplier=strategy.get("vpi_multiplier", 1.0),
                    priority=strategy.get("priority", 1),
                    strategy_config=strategy.get("strategy_config")
                )
                db.add(new_strategy)
                db.commit()
                db.refresh(new_strategy)
                return {"message": "Strategy created successfully", "id": new_strategy.id}
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating brand strategy: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/strategy/{brand_id}")
async def get_brand_strategy(
    brand_id: int,
    db: Session = Depends(get_db)
):
    """
    Get strategy configuration for a brand.
    
    Path parameters:
    - brand_id: ID of the brand/advertiser
    """
    with tracer.start_as_current_span("get_brand_strategy"):
        try:
            strategy = db.query(models.BrandStrategy).filter(
                models.BrandStrategy.brand_id == brand_id,
                models.BrandStrategy.is_active == True
            ).first()
            
            if not strategy:
                return {"message": "No strategy found", "strategy": None}
                
            result = {
                "id": strategy.id,
                "brand_id": strategy.brand_id,
                "vpi_multiplier": strategy.vpi_multiplier,
                "priority": strategy.priority,
                "created_at": strategy.created_at.isoformat(),
                "updated_at": strategy.updated_at.isoformat()
            }
            
            # Parse strategy_config if available
            if strategy.strategy_config:
                try:
                    import json
                    result["strategy_config"] = json.loads(strategy.strategy_config)
                except:
                    result["strategy_config"] = strategy.strategy_config
                    
            return {"strategy": result}
            
        except Exception as e:
            logger.error(f"Error retrieving brand strategy: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
