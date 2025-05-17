"""
Normalization utilities for the bidding engine.

This module contains functions for normalizing different bid types (CPA, CPC, CPM)
to a common value-per-impression (VPI) metric, which allows fair comparison
between different bidding models.
"""

from typing import Optional

def normalize_bid_to_impression_value(
    bid_amount: float,
    bid_type: str,
    ctr: float,
    cvr: Optional[float] = None
) -> float:
    """
    Normalize different bid types to a common value-per-impression (VPI) metric.
    
    Args:
        bid_amount: The original bid amount
        bid_type: Type of bid (CPA, CPC, CPM)
        ctr: Click-through rate (clicks / impressions)
        cvr: Conversion rate (conversions / clicks), required for CPA bids
        
    Returns:
        Normalized value per impression (VPI)
    """
    # Ensure we have valid inputs
    bid_amount = float(bid_amount)
    ctr = max(0.001, float(ctr))  # Minimum CTR to avoid division by zero
    
    # Normalize based on bid type
    bid_type = bid_type.upper()
    
    if bid_type == "CPM":
        # CPM is already per thousand impressions, convert to per impression
        return bid_amount / 1000
        
    elif bid_type == "CPC":
        # CPC × CTR = value per impression
        return bid_amount * ctr
        
    elif bid_type == "CPA":
        # For CPA bids, we need the conversion rate
        # If not provided, use a reasonable default
        if cvr is None:
            cvr = 0.03  # 3% default CVR
        else:
            cvr = max(0.001, float(cvr))  # Minimum CVR to avoid division by zero
            
        # CPA × CVR × CTR = value per impression
        return bid_amount * ctr * cvr
        
    else:
        # Unknown bid type, return CPM-equivalent value
        return bid_amount / 1000