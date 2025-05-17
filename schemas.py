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


class ROASPredictionRequest(BaseModel):
    """Request model for ROAS prediction"""
    brand_id: int
    partner_id: int
    ad_slot_id: int
    device_type: Optional[int] = 0
    creative_type: Optional[int] = 0
    placement_score: Optional[int] = 50


class ROASPredictionResponse(BaseModel):
    """Response model for ROAS prediction"""
    brand_id: int
    partner_id: int
    ad_slot_id: int
    predicted_vpi: float
    estimated_roas: float
    actual_roas: float
    historical_impressions: int
    historical_revenue: float
    historical_cost: float
    timestamp: str


class PerformanceEventRequest(BaseModel):
    """Request model for performance event ingestion"""
    event_id: str = Field(..., description="Unique identifier for deduplication")
    type: str = Field(..., description="Type of event: impression, click, or conversion")
    brand_id: int
    partner_id: int
    ad_slot_id: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    revenue: Optional[float] = None


class BudgetLedgerEntry(BaseModel):
    """Budget tracking model for portfolio optimization"""
    brand_id: int
    total_budget: float
    spent_budget: float
    target_roas: float
    current_roas: float
    throttle_factor: float


class PortfolioOptimizationConfig(BaseModel):
    """Configuration for portfolio-wide ROAS optimization"""
    enabled: bool = True
    min_target_roas: float = 2.0
    default_lambda: float = 0.5
    update_frequency_minutes: int = 60
    
    
class CreativeResponse(BaseModel):
    """Response model for creative assets"""
    id: int
    brand_id: int
    creative_url: str
    creative_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    status: str  # pending, approved, rejected
    reject_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    
    class Config:
        orm_mode = True


class CreativeUpdateRequest(BaseModel):
    """Request model for updating creative details"""
    creative_url: Optional[str] = None
    creative_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    

class CreativeStatusUpdate(BaseModel):
    """Request model for updating creative status (admin use only)"""
    status: str = Field(..., description="New status (pending, approved, rejected)")
    reject_reason: Optional[str] = None