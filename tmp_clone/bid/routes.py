"""
Bidding Engine API Router

This module defines the FastAPI router for the bidding engine API endpoints.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Callable

# Import bidding engine components
from models import db, initialize_db, Brand, AdSlot, Bid, BidModel, Performance, BrandStrategy
from bidding_engine import evaluate_bids, get_historical_performance

# Create router
router = APIRouter(prefix="/bidding", tags=["bidding"])

# Pydantic models for API
class BidRequest(BaseModel):
    brand_id: int
    ad_slot_id: int
    model_id: int
    amount: float
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None

class EvaluateRequest(BaseModel):
    ad_slot_id: int

class BrandStrategyRequest(BaseModel):
    name: str
    description: Optional[str] = None
    vpi_multiplier: float = 1.0
    priority: int = 0

# Dependency for Flask app context
def get_flask_app():
    from flask import Flask
    
    flask_app = Flask(__name__)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    initialize_db(flask_app)
    return flask_app

# API Routes
@router.get("/brands")
async def get_brands():
    """Get all brands"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        brands = Brand.query.all()
        return [brand.to_dict() for brand in brands]

@router.get("/ad-slots")
async def get_ad_slots():
    """Get all ad slots"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        slots = AdSlot.query.all()
        return [slot.to_dict() for slot in slots]

@router.get("/bid-models")
async def get_bid_models():
    """Get all bid models"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        models = BidModel.query.all()
        return [model.to_dict() for model in models]

@router.post("/bids")
async def place_bid(bid_request: BidRequest):
    """Place a bid with specified parameters"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        # Create bid
        bid = Bid(
            brand_id=bid_request.brand_id,
            ad_slot_id=bid_request.ad_slot_id,
            model_id=bid_request.model_id,
            amount=bid_request.amount,
            min_threshold=bid_request.min_threshold,
            max_threshold=bid_request.max_threshold,
            status="active"
        )
        
        db.session.add(bid)
        db.session.commit()
        
        return {
            "message": "Bid placed successfully", 
            "bid_id": bid.id,
            "bid": bid.to_dict()
        }

@router.post("/evaluate")
async def evaluate_ad_slot_bids(evaluate_request: EvaluateRequest):
    """Evaluate all bids for an ad slot"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        # Get ad slot
        ad_slot = AdSlot.query.get(evaluate_request.ad_slot_id)
        if not ad_slot:
            raise HTTPException(status_code=404, detail=f"Ad slot with ID {evaluate_request.ad_slot_id} not found")
        
        # Get all active bids for this slot
        bids = Bid.query.filter_by(ad_slot_id=evaluate_request.ad_slot_id, status="active").all()
        if not bids:
            return {"message": "No active bids found for this ad slot", "results": []}
        
        # Evaluate bids
        results = evaluate_bids(bids, ad_slot)
        
        # Sort by value_per_impression
        results.sort(key=lambda x: x['value_per_impression'], reverse=True)
        
        return {
            "message": "Bids evaluated successfully",
            "ad_slot": ad_slot.to_dict(),
            "results": results,
            "winner": results[0] if results else None
        }

@router.get("/init-demo-data")
async def init_demo_data():
    """Initialize demo data in the database"""
    from models import create_sample_data
    
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        success = create_sample_data()
        
        if success:
            return {"message": "Demo data initialized successfully"}
        else:
            raise HTTPException(status_code=500, detail="Error initializing demo data")

@router.get("/brand-strategies")
async def get_brand_strategies():
    """Get all brand strategies"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        strategies = BrandStrategy.query.order_by(BrandStrategy.priority).all()
        return [strategy.to_dict() for strategy in strategies]

@router.get("/brand-strategies/{strategy_id}")
async def get_brand_strategy(strategy_id: int):
    """Get a specific brand strategy by ID"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        strategy = BrandStrategy.query.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Brand strategy with ID {strategy_id} not found")
        return strategy.to_dict()

@router.post("/brand-strategies")
async def create_brand_strategy(strategy_request: BrandStrategyRequest):
    """Create a new brand strategy"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        # Create new strategy
        strategy = BrandStrategy(
            name=strategy_request.name,
            description=strategy_request.description,
            vpi_multiplier=strategy_request.vpi_multiplier,
            priority=strategy_request.priority
        )
        
        db.session.add(strategy)
        db.session.commit()
        
        return {
            "message": "Brand strategy created successfully", 
            "strategy_id": strategy.id,
            "strategy": strategy.to_dict()
        }

@router.put("/brand-strategies/{strategy_id}")
async def update_brand_strategy(strategy_id: int, strategy_request: BrandStrategyRequest):
    """Update an existing brand strategy"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        strategy = BrandStrategy.query.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Brand strategy with ID {strategy_id} not found")
        
        # Update strategy fields
        strategy.name = strategy_request.name
        strategy.description = strategy_request.description
        strategy.vpi_multiplier = strategy_request.vpi_multiplier
        strategy.priority = strategy_request.priority
        
        db.session.commit()
        
        return {
            "message": "Brand strategy updated successfully",
            "strategy": strategy.to_dict()
        }

@router.delete("/brand-strategies/{strategy_id}")
async def delete_brand_strategy(strategy_id: int):
    """Delete a brand strategy"""
    flask_app = get_flask_app()
    
    with flask_app.app_context():
        strategy = BrandStrategy.query.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Brand strategy with ID {strategy_id} not found")
        
        # Check if any brands are using this strategy
        brands_using_strategy = Brand.query.filter_by(strategy_id=strategy_id).count()
        if brands_using_strategy > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete strategy as it is being used by {brands_using_strategy} brands"
            )
        
        db.session.delete(strategy)
        db.session.commit()
        
        return {"message": "Brand strategy deleted successfully"}