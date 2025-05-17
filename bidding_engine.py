import logging
import json
from typing import Dict, Any, Optional, List, Tuple

from utils.normalize import normalize_bid_to_impression_value
from utils.beta_posterior import get_smoothed_rates
from utils.quality_factors import apply_quality_factors
from utils.redis_cache import get_cached_feature, set_cached_feature

logger = logging.getLogger(__name__)

class BiddingEngine:
    """
    Core bidding engine that processes bid requests and applies various
    strategies and transformations.
    """

    def __init__(self):
        self.default_quality = 1.0
        self.default_ctr = 0.01  # 1% default CTR
        self.default_cvr = 0.03  # 3% default CVR

    async def process_bid(self, bid_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a bid request and return the calculated bid response.

        Args:
            bid_request: Dict containing bid request parameters
                - brand_id: Identifier for the advertiser
                - bid_amount: Original bid amount
                - bid_type: Type of bid (CPA, CPC, CPM)
                - ad_slot: Information about the ad placement
                - strategy: Optional strategy configuration

        Returns:
            Dict with processed bid information
        """
        brand_id = bid_request.get("brand_id")
        bid_amount = float(bid_request.get("bid_amount", 0))
        bid_type = bid_request.get("bid_type", "CPM")
        ad_slot = bid_request.get("ad_slot", {})
        strategy = bid_request.get("strategy")

        logger.info(f"Processing bid request for brand {brand_id}, type {bid_type}, amount {bid_amount}")

        # Apply brand strategy if available
        if strategy:
            bid_amount = self.apply_brand_strategy(bid_amount, strategy)
        
        # Get historical performance metrics (with beta smoothing)
        ctr, cvr = await self.get_historical_performance(brand_id, ad_slot.get("id"))
        
        # Normalize bid to impression value (CPM equivalent)
        normalized_value = normalize_bid_to_impression_value(
            bid_amount=bid_amount,
            bid_type=bid_type,
            ctr=ctr,
            cvr=cvr
        )
        
        # Apply quality factors
        final_bid_value = await apply_quality_factors(normalized_value, ad_slot)
        
        # Construct response
        response = {
            "original_bid": bid_amount,
            "normalized_value": normalized_value,
            "final_bid_value": final_bid_value,
            "bid_type": bid_type,
            "ctr": ctr,
            "cvr": cvr,
            "brand_id": brand_id,
            "ad_slot_id": ad_slot.get("id")
        }
        
        logger.debug(f"Bid response: {response}")
        return response

    def apply_brand_strategy(self, bid_amount: float, strategy_config: Dict[str, Any]) -> float:
        """
        Apply brand-specific bidding strategy to modify the original bid.
        
        Args:
            bid_amount: Original bid amount
            strategy_config: Configuration for brand strategy
        
        Returns:
            Modified bid amount
        """
        if not strategy_config:
            return bid_amount
            
        # Extract strategy parameters
        vpi_multiplier = float(strategy_config.get("vpi_multiplier", 1.0))
        priority = int(strategy_config.get("priority", 1))
        
        # Apply multiplier
        adjusted_bid = bid_amount * vpi_multiplier
        
        # Apply priority-based boost (higher priority gets bigger boost)
        if priority > 1:
            priority_boost = 1.0 + (priority - 1) * 0.05  # 5% boost per priority level
            adjusted_bid *= priority_boost
            
        logger.debug(f"Applied brand strategy: original={bid_amount}, adjusted={adjusted_bid}")
        return adjusted_bid

    async def get_historical_performance(self, brand_id: int, slot_id: int) -> Tuple[float, float]:
        """
        Retrieve historical CTR and CVR with beta-posterior smoothing.
        
        Args:
            brand_id: Brand identifier
            slot_id: Ad slot identifier
            
        Returns:
            Tuple of (ctr, cvr) with beta smoothing applied
        """
        # Try to get from cache first
        cache_key = f"perf:{brand_id}:{slot_id}"
        cached_data = await get_cached_feature(cache_key)
        
        if cached_data:
            try:
                data = json.loads(cached_data)
                return data.get("ctr", self.default_ctr), data.get("cvr", self.default_cvr)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse cached performance data for {cache_key}")
        
        # In production, these values would be retrieved from the database
        # based on historical performance for this brand/slot combination
        # The following would query your BidHistory table
        
        # For demonstration purposes, adjust these values based on brand_id and slot_id
        # to simulate variability in performance across different advertisers and slots
        base_impressions = 100 + (brand_id % 10) * 50  # Example value
        base_clicks = 2 + (brand_id % 5)  # Example value
        base_conversions = max(1, brand_id % 3)  # Example value
        
        # Adjust based on slot_id to simulate slot performance variations
        slot_multiplier = 1.0 + (slot_id % 5) * 0.2  # 1.0 to 1.8
        
        impressions = int(base_impressions * slot_multiplier)
        clicks = min(impressions, int(base_clicks * slot_multiplier))
        conversions = min(clicks, int(base_conversions * slot_multiplier))
        
        # Apply beta posterior smoothing using our implementation
        smoothed_ctr, smoothed_cvr = get_smoothed_rates(
            clicks=clicks,
            impressions=impressions,
            conversions=conversions,
            # Customizable priors for different advertisers or categories
            ctr_prior=(1.0, 10.0),  # Expect ~9% CTR
            cvr_prior=(1.0, 20.0)   # Expect ~5% CVR
        )
        
        # Ensure values are within reasonable bounds
        smoothed_ctr = max(0.001, min(0.5, smoothed_ctr))  # Limit to 0.1% to 50%
        smoothed_cvr = max(0.001, min(0.3, smoothed_cvr))  # Limit to 0.1% to 30%
        
        # Cache the results
        await set_cached_feature(cache_key, json.dumps({
            "ctr": smoothed_ctr,
            "cvr": smoothed_cvr
        }), ttl=3600)  # Cache for 1 hour
        
        return smoothed_ctr, smoothed_cvr

# Create a singleton instance
bidding_engine = BiddingEngine()
