"""
Quality factors utilities for the bidding engine.

This module contains functions for applying quality factors to normalized bid values.
Quality factors adjust bids based on ad slot characteristics, page context, or
other quality signals.
"""

import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

async def apply_quality_factors(normalized_value: float, ad_slot: Dict[str, Any], brand_id: int = None) -> float:
    """
    Apply quality factors to adjust the normalized bid value.
    
    Args:
        normalized_value: The normalized bid value per impression
        ad_slot: Dictionary containing ad slot information
        brand_id: Brand identifier (for XGBoost prediction)
        
    Returns:
        Adjusted bid value after applying quality factors
    """
    # Extract slot information
    slot_id = ad_slot.get("id", 0)
    width = ad_slot.get("width", 0)
    height = ad_slot.get("height", 0)
    position = ad_slot.get("position", 0)
    page_info = ad_slot.get("page", {})
    
    # Use XGBoost prediction if brand_id is provided and XGBoost is available
    try:
        if brand_id is not None:
            from utils.xgboost_quality import predict_quality_factor
            quality_factor = await predict_quality_factor(ad_slot, brand_id)
            logger.info(f"Using XGBoost quality prediction: {quality_factor:.4f}")
        else:
            # Fallback to rule-based approach if XGBoost is not available
            raise ImportError("No brand_id provided, using rule-based approach")
    except (ImportError, ModuleNotFoundError):
        # Base quality factor starts at 1.0 (no adjustment)
        quality_factor = 1.0
        
        # Adjust based on ad size/dimensions
        size_factor = get_size_quality_factor(width, height)
        quality_factor *= size_factor
        
        # Adjust based on position (higher positions generally have better quality)
        if position > 0:
            position_factor = get_position_quality_factor(position)
            quality_factor *= position_factor
        
        # Adjust based on page quality (if available)
        if page_info:
            page_factor = get_page_quality_factor(page_info)
            quality_factor *= page_factor
        
        logger.info(f"Using rule-based quality factors: {quality_factor:.4f}")
    
    # Apply the quality factor to the normalized value
    adjusted_value = normalized_value * quality_factor
    
    logger.debug(f"Applied quality factors to slot {slot_id}: {quality_factor:.2f} * {normalized_value:.6f} = {adjusted_value:.6f}")
    
    return adjusted_value

def get_size_quality_factor(width: int, height: int) -> float:
    """
    Calculate quality factor based on ad size.
    
    Larger ads tend to have better viewability and engagement.
    """
    # If dimensions are not provided, return neutral factor
    if not width or not height:
        return 1.0
        
    # Calculate area
    area = width * height
    
    # Common ad sizes and their approximate quality factors
    if area >= 300000:  # Large formats (eg. 970x250)
        return 1.3
    elif area >= 200000:  # Medium-large formats (eg. 728x90)
        return 1.2
    elif area >= 100000:  # Medium formats (eg. 300x250)
        return 1.1
    elif area >= 50000:   # Small-medium formats
        return 1.0
    else:                # Small formats
        return 0.9

def get_position_quality_factor(position: int) -> float:
    """
    Calculate quality factor based on ad position.
    
    Lower position numbers (higher on page) tend to have better viewability.
    """
    # Position 1 (top) gets highest factor, decreasing as we go down
    if position == 1:
        return 1.25
    elif position == 2:
        return 1.15
    elif position == 3:
        return 1.05
    elif position <= 5:
        return 1.0
    else:
        return 0.9  # Positions far down the page

def get_page_quality_factor(page_info: Dict[str, Any]) -> float:
    """
    Calculate quality factor based on page characteristics.
    
    Factors might include page category, content quality, user engagement, etc.
    """
    quality_factor = 1.0
    
    # Page category adjustment
    category = page_info.get("category", "").lower()
    if category in ["news", "finance", "technology"]:
        quality_factor *= 1.1  # Premium categories
    elif category in ["entertainment", "sports"]:
        quality_factor *= 1.05  # High engagement categories
    
    # Traffic source adjustment
    traffic_source = page_info.get("traffic_source", "").lower()
    if traffic_source in ["direct", "search"]:
        quality_factor *= 1.1  # Higher intent traffic
    elif traffic_source in ["social"]:
        quality_factor *= 0.95  # Lower intent traffic
    
    # Page engagement metrics (if available)
    avg_time_on_page = page_info.get("avg_time_on_page", 0)
    if avg_time_on_page > 120:  # More than 2 minutes
        quality_factor *= 1.15  # High engagement
    elif avg_time_on_page > 60:  # More than 1 minute
        quality_factor *= 1.05  # Good engagement
    
    return quality_factor