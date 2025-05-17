from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from database import Base

class BrandStrategy(Base):
    """
    Stores brand-specific bidding strategies and multipliers
    """
    __tablename__ = "brand_strategies"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, index=True, nullable=False)
    vpi_multiplier = Column(Float, nullable=False, default=1.0)
    priority = Column(Integer, nullable=False, default=1)
    strategy_config = Column(String, nullable=True)  # JSON string with strategy config
    daily_cap = Column(Float, nullable=False, default=1000.0)  # Daily budget cap in dollars
    total_cap = Column(Float, nullable=False, default=50000.0)  # Total budget cap in dollars
    spent_today = Column(Float, nullable=False, default=0.0)  # Amount spent today
    spent_total = Column(Float, nullable=False, default=0.0)  # Total amount spent
    target_roas = Column(Float, nullable=False, default=2.0)  # Target ROAS
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Create an index on brand_id and is_active for faster lookups
    __table_args__ = (
        Index('idx_brand_active', brand_id, is_active),
    )


class BidHistory(Base):
    """
    Stores historical bid data for performance analysis and model training
    """
    __tablename__ = "bid_history"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, index=True, nullable=False)
    ad_slot_id = Column(Integer, index=True, nullable=False)
    partner_id = Column(Integer, index=True, nullable=False, default=0)
    bid_amount = Column(Float, nullable=False)
    normalized_value = Column(Float, nullable=False)
    quality_factor = Column(Float, nullable=False, default=1.0)
    ctr = Column(Float, nullable=True)
    cvr = Column(Float, nullable=True)
    bid_type = Column(String, nullable=False)  # CPA, CPC, CPM
    bid_timestamp = Column(DateTime, default=func.now(), index=True)
    
    # Performance data
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    conversions = Column(Integer, nullable=False, default=0)
    revenue = Column(Float, nullable=False, default=0.0)
    cost = Column(Float, nullable=False, default=0.0)
    
    # Device and creative metadata
    device_type = Column(Integer, nullable=True)  # 0=unknown, 1=desktop, 2=mobile, 3=tablet
    creative_type = Column(Integer, nullable=True)  # 0=unknown, 1=image, 2=video, 3=native
    placement_score = Column(Integer, nullable=True)  # 0-100 quality score
    
    # Create composite indexes for common queries
    __table_args__ = (
        Index('idx_brand_slot_time', brand_id, ad_slot_id, bid_timestamp),
        Index('idx_bid_type_time', bid_type, bid_timestamp),
        Index('idx_partner_time', partner_id, bid_timestamp),
        Index('idx_brand_partner', brand_id, partner_id),
    )


class FeatureCache(Base):
    """
    Metadata about cached features in Redis
    """
    __tablename__ = "feature_cache"

    id = Column(Integer, primary_key=True, index=True)
    feature_key = Column(String, nullable=False, unique=True, index=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    ttl_seconds = Column(Integer, nullable=False, default=86400)  # 24 hours default
    is_active = Column(Boolean, default=True)


class EventLog(Base):
    """
    Log of processed performance events for deduplication
    """
    __tablename__ = "event_log"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), nullable=False, unique=True, index=True)
    event_type = Column(String(50), nullable=False)
    brand_id = Column(Integer, index=True, nullable=False)
    partner_id = Column(Integer, index=True, nullable=False)
    ad_slot_id = Column(Integer, index=True, nullable=False)
    processed_at = Column(DateTime, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_event_id', event_id, unique=True),
    )


class Creative(Base):
    """
    Ad creative assets requiring approval before serving
    """
    __tablename__ = "creatives"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, index=True, nullable=False)
    creative_url = Column(String(1024), nullable=False)
    creative_type = Column(String(50), nullable=False)  # image, video, html
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, approved, rejected
    reject_reason = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_by = Column(String(255), nullable=True)  # Admin who reviewed

    __table_args__ = (
        Index('idx_brand_status', brand_id, status),
    )
