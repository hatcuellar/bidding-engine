from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class AdSlotInfo(BaseModel):
    """Information about an ad placement slot"""
    id: int
    width: Optional[int] = None
    height: Optional[int] = None
    position: Optional[int] = None
    page: Optional[Dict[str, Any]] = None


class BidRequest(BaseModel):
    """Bid request model with all necessary parameters"""
    brand_id: int
    bid_amount: float
    bid_type: str = Field(..., description="Type of bid: CPA, CPC, or CPM")
    ad_slot: AdSlotInfo
    strategy: Optional[Dict[str, Any]] = None
    

class BidResponse(BaseModel):
    """Response model for bid calculations"""
    original_bid: float
    normalized_value: float
    final_bid_value: float
    bid_type: str
    ctr: float
    cvr: float
    brand_id: int
    ad_slot_id: int
    process_time_ms: Optional[float] = None
    quality_factor: Optional[float] = None


class BidHistoryEntry(BaseModel):
    """Single bid history entry"""
    id: int
    ad_slot_id: int
    bid_amount: float
    normalized_value: float
    quality_factor: float
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    bid_type: str
    timestamp: str


class BidHistoryResponse(BaseModel):
    """Response model for bid history"""
    brand_id: int
    history: List[BidHistoryEntry]


class BrandStrategyRequest(BaseModel):
    """Request model for updating brand strategy"""
    brand_id: int
    vpi_multiplier: Optional[float] = 1.0
    priority: Optional[int] = 1
    strategy_config: Optional[Dict[str, Any]] = None


class BrandStrategyResponse(BaseModel):
    """Response model for brand strategy"""
    id: int
    brand_id: int
    vpi_multiplier: float
    priority: int
    created_at: str
    updated_at: str
    strategy_config: Optional[Dict[str, Any]] = None


class BrandStrategyResult(BaseModel):
    """Wrapper for brand strategy response"""
    strategy: Optional[BrandStrategyResponse] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    components: Dict[str, str]