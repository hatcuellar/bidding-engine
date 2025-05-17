import numpy as np
from models import Performance, Bid, db

def get_historical_performance(brand_id, ad_slot_id):
    """Get historical performance metrics for a brand-slot combination"""
    performance = Performance.query.filter_by(
        brand_id=brand_id, 
        ad_slot_id=ad_slot_id
    ).first()
    
    if performance:
        return performance
    
    # If no specific performance data exists, get average for this ad slot
    slot_performances = Performance.query.filter_by(ad_slot_id=ad_slot_id).all()
    if not slot_performances:
        # Default values if no performance data is available
        return {
            'ctr': 0.01,  # 1% CTR
            'cvr': 0.03,  # 3% CVR 
            'aov': 100.0  # $100 AOV
        }
    
    # Calculate averages
    avg_ctr = sum(p.ctr for p in slot_performances) / len(slot_performances)
    avg_cvr = sum(p.cvr for p in slot_performances) / len(slot_performances)
    avg_aov = sum(p.aov for p in slot_performances) / len(slot_performances)
    
    return {
        'ctr': avg_ctr,
        'cvr': avg_cvr,
        'aov': avg_aov
    }

def normalize_bid_to_impression_value(bid, performance):
    """
    Normalize different bid models to value per impression
    
    Parameters:
    - bid: Bid object with model_id and amount
    - performance: Performance metrics (CTR, CVR, AOV)
    
    Returns:
    - Value per impression for this bid
    """
    model_id = bid.model_id
    amount = bid.amount
    
    # Get performance metrics
    ctr = performance.get('ctr', 0.01) if isinstance(performance, dict) else performance.ctr
    cvr = performance.get('cvr', 0.03) if isinstance(performance, dict) else performance.cvr
    aov = performance.get('aov', 100.0) if isinstance(performance, dict) else performance.aov
    
    # Calculate value per impression based on model type
    if model_id == 1:  # CPA-Fixed
        # Value = Probability of conversion per impression × CPA price
        return ctr * cvr * amount
    
    elif model_id == 2:  # CPA-Percentage
        # Value = Probability of conversion per impression × (AOV × CPA percentage)
        return ctr * cvr * (aov * amount)
    
    elif model_id == 3:  # CPC
        # Value = Probability of click per impression × CPC price
        return ctr * amount
    
    elif model_id == 4:  # CPM
        # Value = CPM price / 1000 (direct price per impression)
        return amount / 1000
    
    return 0  # Default return for unknown model types

def apply_brand_strategy(brand, normalized_value):
    """Apply brand's optimization strategy to adjust the bid value"""
    
    # Get the brand's strategy configuration
    strategy_config = brand.strategy_config
    
    if strategy_config:
        # Use the multiplier from the strategy configuration
        return normalized_value * strategy_config.vpi_multiplier
    
    # Default - no adjustment if no strategy is configured
    return normalized_value

def apply_quality_factors(bid, ad_slot):
    """Apply quality factors to adjust the normalized value"""
    
    # Get placement verification score from ad slot
    placement_score = ad_slot.placement_score
    
    # Get partner quality score
    partner_quality = ad_slot.partner.quality_score
    
    # Apply quality multipliers
    quality_factor = (placement_score + partner_quality) / 2
    
    # Return adjusted value - higher quality means willing to pay more
    return bid * quality_factor

def evaluate_bids(bids, ad_slot):
    """
    Evaluate all bids for an ad slot and return their normalized values
    
    Parameters:
    - bids: List of Bid objects
    - ad_slot: The AdSlot object
    
    Returns:
    - List of dicts with bid details and normalized values
    """
    results = []
    
    for bid in bids:
        # Get historical performance data
        performance = get_historical_performance(bid.brand_id, ad_slot.id)
        
        # Step 1: Normalize to value per impression based on model
        base_value = normalize_bid_to_impression_value(bid, performance)
        
        # Step 2: Apply brand strategy adjustments
        strategy_adjusted_value = apply_brand_strategy(bid.brand, base_value)
        
        # Step 3: Apply quality factors (placement verification, partner quality)
        final_value = apply_quality_factors(strategy_adjusted_value, ad_slot)
        
        # Step 4: Apply thresholds
        if bid.min_threshold and final_value < bid.min_threshold:
            final_value = 0  # Below minimum threshold, don't participate
        
        if bid.max_threshold and final_value > bid.max_threshold:
            final_value = bid.max_threshold  # Cap at maximum threshold
        
        # Update the normalized value in the database
        bid.normalized_value = final_value
        db.session.commit()
        
        # Add to results
        results.append({
            'bid_id': bid.id,
            'brand_id': bid.brand_id,
            'brand_name': bid.brand.name,
            'model_id': bid.model_id,
            'model_name': bid.model.name,
            'original_amount': bid.amount,
            'value_per_impression': final_value
        })
    
    return results