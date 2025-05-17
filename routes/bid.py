from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from sqlalchemy.orm import Session
import time
import json
import logging

from database import get_db
from bidding_engine import bidding_engine
import models
from schemas import BidRequest, BidResponse, BidHistoryResponse, BrandStrategyRequest, BrandStrategyResult

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/calculate", response_model=BidResponse, status_code=status.HTTP_200_OK)
async def calculate_bid(
    request: Request,
    bid_request: BidRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate bid value based on provided parameters.
    
    Request body contains:
    - brand_id: ID of the brand/advertiser
    - bid_amount: Original bid amount
    - bid_type: Type of bid (CPA, CPC, CPM)
    - ad_slot: Information about the ad placement
    """
    start_time = time.time()
    
    # Simple timing instead of OpenTelemetry tracing
    logger.info(f"Starting bid calculation for brand_id: {bid_request.brand_id}")
        try:
            # Convert Pydantic model to dict for bidding engine
            bid_request_dict = bid_request.dict()
            
            # Get brand strategy from database
            brand_id = bid_request.brand_id
            brand_strategy = db.query(models.BrandStrategy).filter(
                models.BrandStrategy.brand_id == brand_id,
                models.BrandStrategy.is_active == True
            ).first()
            
            # Add strategy to bid_request if available
            if brand_strategy:
                try:
                    strategy_config = {}
                    strategy_config_str = brand_strategy.strategy_config
                    if strategy_config_str and isinstance(strategy_config_str, str):
                        strategy_config = json.loads(strategy_config_str)
                    
                    strategy_config.update({
                        "vpi_multiplier": brand_strategy.vpi_multiplier,
                        "priority": brand_strategy.priority
                    })
                    
                    bid_request_dict["strategy"] = strategy_config
                except Exception as e:
                    logger.error(f"Error parsing strategy config: {e}")
            
            # Process the bid
            result = await bidding_engine.process_bid(bid_request_dict)
            
            # Record bid in history
            try:
                bid_history = models.BidHistory(
                    brand_id=brand_id,
                    ad_slot_id=bid_request.ad_slot.id,
                    bid_amount=bid_request.bid_amount,
                    normalized_value=result.get("normalized_value", 0),
                    quality_factor=result.get("quality_factor", 1.0),
                    ctr=result.get("ctr", 0),
                    cvr=result.get("cvr", 0),
                    bid_type=bid_request.bid_type
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )


@router.get("/history/{brand_id}", response_model=BidHistoryResponse)
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
    logger.info(f"Retrieving bid history for brand_id: {brand_id}")
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )


@router.post("/strategy", status_code=status.HTTP_201_CREATED)
async def update_brand_strategy(
    strategy: BrandStrategyRequest,
    db: Session = Depends(get_db)
):
    """
    Create or update brand bidding strategy.
    
    Request body contains:
    - brand_id: ID of the brand/advertiser
    - vpi_multiplier: Value-per-impression multiplier
    - priority: Priority level for the brand
    - strategy_config: Additional configuration as JSON
    """
    with tracer.start_as_current_span("update_brand_strategy"):
        try:
            brand_id = strategy.brand_id
            
            # Check if strategy exists
            existing = db.query(models.BrandStrategy).filter(
                models.BrandStrategy.brand_id == brand_id,
                models.BrandStrategy.is_active == True
            ).first()
            
            # Convert strategy_config to JSON string if provided
            strategy_config_str = None
            if strategy.strategy_config:
                strategy_config_str = json.dumps(strategy.strategy_config)
            
            if existing:
                # Update existing strategy
                # Access the SQLAlchemy model attributes properly
                setattr(existing, "vpi_multiplier", strategy.vpi_multiplier)
                setattr(existing, "priority", strategy.priority)
                if strategy.strategy_config is not None:
                    setattr(existing, "strategy_config", strategy_config_str)
                db.commit()
                return {"message": "Strategy updated successfully", "id": existing.id}
            else:
                # Create new strategy
                new_strategy = models.BrandStrategy(
                    brand_id=brand_id,
                    vpi_multiplier=strategy.vpi_multiplier,
                    priority=strategy.priority,
                    strategy_config=strategy_config_str
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )


@router.get("/strategy/{brand_id}", response_model=BrandStrategyResult)
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
            strategy_config_str = strategy.strategy_config
            if strategy_config_str and isinstance(strategy_config_str, str):
                try:
                    result["strategy_config"] = json.loads(strategy_config_str)
                except:
                    result["strategy_config"] = strategy_config_str
                    
            return {"strategy": result}
            
        except Exception as e:
            logger.error(f"Error retrieving brand strategy: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )
