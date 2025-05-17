"""
Direct Test of Multi-Model Predictive Bidding Engine

This script tests the bidding engine directly without database dependencies.
It demonstrates how different bid models (CPA-Fixed, CPA-Percentage, CPC, CPM) 
are normalized and evaluated against each other.
"""

# Simulated performance metrics
PERFORMANCE_METRICS = {
    'cpa_fixed': {
        'ctr': 0.012,  # 1.2% click-through rate
        'cvr': 0.05,   # 5% conversion rate
        'aov': 150.0   # $150 average order value
    },
    'cpa_percentage': {
        'ctr': 0.014,  # 1.4% click-through rate 
        'cvr': 0.06,   # 6% conversion rate
        'aov': 200.0   # $200 average order value
    },
    'cpc': {
        'ctr': 0.018,  # 1.8% click-through rate
        'cvr': 0.04,   # 4% conversion rate
        'aov': 180.0   # $180 average order value
    },
    'cpm': {
        'ctr': 0.01,   # 1% click-through rate
        'cvr': 0.03,   # 3% conversion rate
        'aov': 120.0   # $120 average order value
    }
}

# Simulated bids
BIDS = [
    {
        'id': 1,
        'brand_name': 'TechGiant Inc.',
        'brand_strategy': 'Maximize ROI',
        'model_name': 'CPA-Fixed',
        'amount': 50.0,  # $50 per acquisition
        'min_threshold': 0.005,
        'max_threshold': 0.1
    },
    {
        'id': 2,
        'brand_name': 'ShopMart',
        'brand_strategy': 'Maximize Reach',
        'model_name': 'CPA-Percentage',
        'amount': 0.08,  # 8% of order value
        'min_threshold': 0.004,
        'max_threshold': 0.12
    },
    {
        'id': 3,
        'brand_name': 'FinSecure',
        'brand_strategy': 'Minimize CPA/CPC',
        'model_name': 'CPC',
        'amount': 1.75,  # $1.75 per click
        'min_threshold': 0.006,
        'max_threshold': 0.09
    },
    {
        'id': 4,
        'brand_name': 'TravelEasy',
        'brand_strategy': 'Even budget pacing',
        'model_name': 'CPM',
        'amount': 12.0,  # $12 per 1000 impressions
        'min_threshold': 0.007,
        'max_threshold': 0.11
    }
]

# Simulated ad slot
AD_SLOT = {
    'name': 'Homepage Banner',
    'placement': 'Header',
    'floor_price': 3.5,
    'placement_score': 0.9,
    'content_category': 'News'
}

def normalize_bid_to_impression_value(bid, metrics):
    """
    Normalize different bid models to a value per impression
    
    Parameters:
    - bid: Bid object with model_name and amount
    - metrics: Performance metrics (CTR, CVR, AOV)
    
    Returns:
    - Value per impression for this bid
    """
    model = bid['model_name']
    amount = bid['amount']
    
    if model == 'CPA-Fixed':
        # CPA-Fixed: Value = Conversion Rate * CPA value
        # From impression -> click -> conversion
        return metrics['ctr'] * metrics['cvr'] * amount
    
    elif model == 'CPA-Percentage':
        # CPA-Percentage: Value = Conversion Rate * % * Average Order Value
        # From impression -> click -> conversion -> % of order
        return metrics['ctr'] * metrics['cvr'] * amount * metrics['aov']
    
    elif model == 'CPC':
        # CPC: Value = Click Rate * CPC value
        # From impression -> click
        return metrics['ctr'] * amount
    
    elif model == 'CPM':
        # CPM: Value = CPM / 1000
        # Already per impression
        return amount / 1000.0
    
    else:
        # Unknown model
        return 0.0

def apply_brand_strategy(brand_strategy, value):
    """
    Apply brand optimization strategy to adjust the bid value
    
    Parameters:
    - brand_strategy: Strategy string
    - value: Base normalized value
    
    Returns:
    - Strategy-adjusted value
    """
    if brand_strategy == 'Maximize ROI':
        # Conservative approach - slightly lower the value
        return value * 0.95
    
    elif brand_strategy == 'Maximize Reach':
        # Aggressive approach - increase value to win more bids
        return value * 1.15
    
    elif brand_strategy == 'Minimize CPA/CPC':
        # Cost-saving approach - lower the value
        return value * 0.85
    
    elif brand_strategy == 'Even budget pacing':
        # Neutral approach - keep value as is
        return value
    
    else:
        # Unknown strategy - no adjustment
        return value

def apply_quality_factors(value, ad_slot):
    """
    Apply ad slot quality factors to adjust the value
    
    Parameters:
    - value: Strategy-adjusted value
    - ad_slot: Ad slot information
    
    Returns:
    - Quality-adjusted value
    """
    # Apply placement score as a quality factor
    placement_score = ad_slot['placement_score']
    
    # Premium placements (high score) reduce the value slightly as they're worth more
    # Lower quality placements (low score) increase the value to compensate
    if placement_score > 0.8:
        return value * 0.875  # High quality placement - reduce value by 12.5%
    else:
        return value * 1.0  # Standard quality - no adjustment
    
def evaluate_bid(bid, ad_slot):
    """
    Evaluate a single bid and return its normalized value
    
    Parameters:
    - bid: Bid object
    - ad_slot: Ad slot information
    
    Returns:
    - Dictionary with bid details and normalized value
    """
    # Get performance metrics based on bid model
    if bid['model_name'] == 'CPA-Fixed':
        metrics = PERFORMANCE_METRICS['cpa_fixed']
    elif bid['model_name'] == 'CPA-Percentage':
        metrics = PERFORMANCE_METRICS['cpa_percentage']
    elif bid['model_name'] == 'CPC':
        metrics = PERFORMANCE_METRICS['cpc']
    else:  # CPM
        metrics = PERFORMANCE_METRICS['cpm']
    
    # Step 1: Normalize bid to impression value
    base_value = normalize_bid_to_impression_value(bid, metrics)
    
    # Step 2: Apply brand strategy
    strategy_adjusted = apply_brand_strategy(bid['brand_strategy'], base_value)
    
    # Step 3: Apply quality factors
    quality_adjusted = apply_quality_factors(strategy_adjusted, ad_slot)
    
    # Step 4: Apply thresholds
    final_value = quality_adjusted
    if bid['min_threshold'] and final_value < bid['min_threshold']:
        final_value = 0  # Below min threshold, not eligible
    elif bid['max_threshold'] and final_value > bid['max_threshold']:
        final_value = bid['max_threshold']  # Cap at max threshold
    
    return {
        'id': bid['id'],
        'brand_name': bid['brand_name'],
        'brand_strategy': bid['brand_strategy'],
        'model_name': bid['model_name'],
        'original_amount': bid['amount'],
        'base_value': base_value,
        'strategy_adjusted': strategy_adjusted,
        'quality_adjusted': quality_adjusted,
        'value_per_impression': final_value,
        'performance_metrics': metrics
    }

def run_bidding_test():
    """Run the multi-model predictive bidding test"""
    print("\n" + "="*80)
    print(" MULTI-MODEL PREDICTIVE BIDDING ENGINE TEST ".center(80, "="))
    print("="*80)
    
    print(f"\nAd Slot: {AD_SLOT['name']} ({AD_SLOT['placement']})")
    print(f"Floor Price: ${AD_SLOT['floor_price']}, Quality Score: {AD_SLOT['placement_score']}")
    
    print("\n" + "-"*80)
    print(" EVALUATING INDIVIDUAL BIDS ".center(80, "-"))
    print("-"*80)
    
    # Evaluate each bid
    evaluated_bids = []
    for bid in BIDS:
        result = evaluate_bid(bid, AD_SLOT)
        evaluated_bids.append(result)
        
        print(f"\nBid #{result['id']}: {result['brand_name']} - {result['model_name']}")
        print(f"Original amount: ${result['original_amount']:.2f}")
        
        if result['model_name'] == 'CPA-Fixed':
            print(f"Bid is: ${result['original_amount']:.2f} per acquisition")
        elif result['model_name'] == 'CPA-Percentage':
            print(f"Bid is: {result['original_amount']*100:.1f}% of order value")
        elif result['model_name'] == 'CPC':
            print(f"Bid is: ${result['original_amount']:.2f} per click")
        else:  # CPM
            print(f"Bid is: ${result['original_amount']:.2f} per 1000 impressions")
        
        # Get metrics
        metrics = result['performance_metrics']
        print(f"Performance: CTR: {metrics['ctr']*100:.2f}%, CVR: {metrics['cvr']*100:.2f}%, AOV: ${metrics['aov']:.2f}")
        
        # Show normalization steps
        print("Normalization process:")
        print(f"1. Base value per impression: ${result['base_value']:.6f}")
        print(f"2. After brand strategy ({result['brand_strategy']}): ${result['strategy_adjusted']:.6f}")
        print(f"3. After quality factors: ${result['quality_adjusted']:.6f}")
        print(f"Final normalized value: ${result['value_per_impression']:.6f}")
    
    print("\n" + "-"*80)
    print(" FINAL BID RANKING ".center(80, "-"))
    print("-"*80)
    
    # Sort by value per impression (highest first)
    ranked_bids = sorted(evaluated_bids, key=lambda x: x['value_per_impression'], reverse=True)
    
    print("\nBids ranked by normalized value per impression:")
    for i, bid in enumerate(ranked_bids):
        winner = " (WINNER)" if i == 0 else ""
        print(f"{i+1}. {bid['brand_name']} - {bid['model_name']} - ${bid['original_amount']:.2f} -> ${bid['value_per_impression']:.6f}{winner}")
    
    print("\n" + "="*80)
    print(" KEY INSIGHTS ".center(80, "="))
    print("="*80)
    
    print("\n1. Different bid models (CPA, CPC, CPM) can be directly compared through normalization")
    print("2. Brand strategies and ad slot quality factors significantly impact the final bid ranking")
    print("3. Higher original bids don't always win - performance metrics matter more")
    print("4. Min/max thresholds provide guardrails against over/under-bidding")
    
    return ranked_bids

if __name__ == "__main__":
    run_bidding_test()