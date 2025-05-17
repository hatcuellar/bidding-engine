"""
Portfolio optimization module for maximizing ROAS across the brand portfolio.

This module handles budget management and bid throttling to ensure
brands meet their target ROAS values.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime, timedelta
import threading
import redis.asyncio as redis_async
from sqlalchemy import func, and_, text
from sqlalchemy.orm import Session

from database import get_db
from models import BidHistory, BrandStrategy

logger = logging.getLogger(__name__)

# In-memory cache for budget ledger
_budget_ledger = {}
_ledger_lock = threading.RLock()

# Lambda adjustment factors for bid scoring
_lambda_factors = {}
_lambda_lock = threading.RLock()

class PortfolioOptimizer:
    """
    Portfolio optimization for maximizing ROAS across all brands.
    
    This class is responsible for tracking budgets, calculating throttle
    factors, and adjusting bid values to meet ROAS targets.
    """
    
    def __init__(self, redis_pool=None):
        """
        Initialize the portfolio optimizer.
        
        Args:
            redis_pool: Optional Redis connection pool for distributed state
        """
        self.redis_pool = redis_pool
        self.min_target_roas = float(os.getenv('MIN_TARGET_ROAS', '2.0'))
        self.default_lambda = float(os.getenv('DEFAULT_LAMBDA', '0.5'))
        self.enabled = os.getenv('ENABLE_PORTFOLIO_OPTIMIZATION', 'true').lower() == 'true'
    
    async def get_brand_ledger(self, brand_id: int) -> Dict[str, Any]:
        """
        Get budget ledger for a specific brand.
        
        Args:
            brand_id: Brand identifier
            
        Returns:
            Dict with budget ledger information
        """
        # Try to get from Redis first if available
        if self.redis_pool:
            try:
                key = f"budget:ledger:{brand_id}"
                data = await self.redis_pool.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Error retrieving budget ledger from Redis: {e}")
        
        # Fall back to in-memory cache
        with _ledger_lock:
            if brand_id in _budget_ledger:
                return _budget_ledger[brand_id]
            
            # Default values if not in cache
            return {
                "brand_id": brand_id,
                "total_budget": 1000.0,  # Default daily budget
                "spent_budget": 0.0,
                "target_roas": self.min_target_roas,
                "current_roas": 0.0,
                "throttle_factor": 1.0,
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def update_brand_ledger(self, brand_id: int, update: Dict[str, Any]) -> None:
        """
        Update budget ledger for a specific brand.
        
        Args:
            brand_id: Brand identifier
            update: New values to update in the ledger
        """
        # Get current ledger
        ledger = await self.get_brand_ledger(brand_id)
        
        # Update with new values
        ledger.update(update)
        ledger["last_updated"] = datetime.utcnow().isoformat()
        
        # Store in Redis if available
        if self.redis_pool:
            try:
                key = f"budget:ledger:{brand_id}"
                await self.redis_pool.set(key, json.dumps(ledger), ex=86400)  # 24 hour TTL
            except Exception as e:
                logger.error(f"Error storing budget ledger in Redis: {e}")
        
        # Always update in-memory cache
        with _ledger_lock:
            _budget_ledger[brand_id] = ledger
    
    async def get_lambda_factor(self, brand_id: int) -> float:
        """
        Get the lambda factor for a brand's bid scoring.
        
        The lambda factor is used in the score calculation:
        Score = predicted_revenue - lambda * predicted_cost
        
        Args:
            brand_id: Brand identifier
            
        Returns:
            Lambda factor value
        """
        # Try to get from Redis first if available
        if self.redis_pool:
            try:
                key = f"lambda:factor:{brand_id}"
                data = await self.redis_pool.get(key)
                if data:
                    return float(data)
            except Exception as e:
                logger.error(f"Error retrieving lambda factor from Redis: {e}")
        
        # Fall back to in-memory cache
        with _lambda_lock:
            if brand_id in _lambda_factors:
                return _lambda_factors[brand_id]
            
            # Default lambda if not in cache
            return self.default_lambda
    
    async def update_lambda_factor(self, brand_id: int, lambda_value: float) -> None:
        """
        Update the lambda factor for a brand's bid scoring.
        
        Args:
            brand_id: Brand identifier
            lambda_value: New lambda value
        """
        # Ensure lambda is in a reasonable range
        lambda_value = max(0.1, min(10.0, lambda_value))
        
        # Store in Redis if available
        if self.redis_pool:
            try:
                key = f"lambda:factor:{brand_id}"
                await self.redis_pool.set(key, str(lambda_value), ex=86400)  # 24 hour TTL
            except Exception as e:
                logger.error(f"Error storing lambda factor in Redis: {e}")
        
        # Always update in-memory cache
        with _lambda_lock:
            _lambda_factors[brand_id] = lambda_value
    
    async def adjust_bid_for_portfolio(
        self,
        brand_id: int,
        predicted_revenue: float,
        predicted_cost: float,
        db: Session
    ) -> Tuple[float, float]:
        """
        Adjust bid value based on portfolio constraints.
        
        Args:
            brand_id: Brand identifier
            predicted_revenue: Expected revenue from this bid
            predicted_cost: Expected cost of this bid
            db: Database session
            
        Returns:
            Tuple of (score, throttle_factor)
        """
        if not self.enabled:
            # If portfolio optimization is disabled, return revenue as score
            # with full throttle
            return predicted_revenue, 1.0
        
        try:
            # Get brand ledger and lambda factor
            ledger = await self.get_brand_ledger(brand_id)
            lambda_factor = await self.get_lambda_factor(brand_id)
            
            # Calculate bid score using lambda factor
            # Score = predicted_revenue - lambda * predicted_cost
            score = predicted_revenue - (lambda_factor * predicted_cost)
            
            # Apply throttle factor based on budget and ROAS constraints
            throttle_factor = ledger["throttle_factor"]
            
            # Check if over budget
            spent = ledger["spent_budget"]
            total = ledger["total_budget"]
            if spent >= total:
                # Over budget, severely reduce throttle
                throttle_factor = 0.1
            elif spent / total > 0.9:
                # Approaching budget limit, reduce throttle
                throttle_factor = 0.5
            
            # Check if ROAS is below target
            current_roas = ledger["current_roas"]
            target_roas = ledger["target_roas"]
            if current_roas < target_roas * 0.8:
                # Significantly below target, reduce throttle
                throttle_factor = min(throttle_factor, 0.3)
            elif current_roas < target_roas:
                # Below target, slightly reduce throttle
                throttle_factor = min(throttle_factor, 0.7)
            
            # If this bid would reduce ROAS further when already below target,
            # adjust score down
            if current_roas < target_roas and predicted_revenue / max(0.01, predicted_cost) < current_roas:
                score = score * 0.5
            
            # Update ledger with predicted spend
            await self.update_brand_ledger(brand_id, {
                "spent_budget": spent + predicted_cost
            })
            
            return score, throttle_factor
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            # In case of errors, return original values
            return predicted_revenue, 1.0
    
    async def update_performance_metrics(self, db: Session) -> None:
        """
        Update ROAS metrics for all brands based on recent performance.
        
        This should be called periodically to refresh the portfolio metrics.
        
        Args:
            db: Database session
        """
        try:
            # Get performance data for the last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            query = text("""
            SELECT 
                brand_id,
                SUM(revenue) as total_revenue,
                SUM(cost) as total_cost
            FROM 
                bid_history
            WHERE 
                bid_timestamp >= :start_date
            GROUP BY 
                brand_id
            """)
            
            result = db.execute(query, {"start_date": yesterday})
            rows = result.fetchall()
            
            for row in rows:
                brand_id = row.brand_id
                revenue = row.total_revenue or 0.0
                cost = row.total_cost or 0.0
                
                # Calculate current ROAS
                current_roas = 0.0
                if cost > 0:
                    current_roas = revenue / cost
                
                # Get strategy for target ROAS
                strategy = db.query(BrandStrategy).filter(
                    BrandStrategy.brand_id == brand_id,
                    BrandStrategy.is_active == True
                ).first()
                
                target_roas = self.min_target_roas
                if strategy and strategy.strategy_config:
                    try:
                        config = json.loads(strategy.strategy_config)
                        if 'target_roas' in config:
                            target_roas = float(config['target_roas'])
                    except:
                        pass
                
                # Update throttle factor based on ROAS performance
                throttle_factor = 1.0
                if current_roas < target_roas * 0.5:
                    # Severely underperforming
                    throttle_factor = 0.2
                elif current_roas < target_roas * 0.8:
                    # Underperforming
                    throttle_factor = 0.5
                elif current_roas < target_roas:
                    # Slightly under target
                    throttle_factor = 0.8
                
                # Update lambda factor
                # If ROAS is below target, increase lambda to reduce bid prices
                current_lambda = await self.get_lambda_factor(brand_id)
                new_lambda = current_lambda
                
                if current_roas < target_roas * 0.8:
                    # Increase lambda to reduce bids
                    new_lambda = min(10.0, current_lambda * 1.2)
                elif current_roas > target_roas * 1.2:
                    # Decrease lambda to increase bids
                    new_lambda = max(0.1, current_lambda * 0.9)
                
                # Update ledger and lambda
                await self.update_brand_ledger(brand_id, {
                    "current_roas": current_roas,
                    "target_roas": target_roas,
                    "throttle_factor": throttle_factor
                })
                
                await self.update_lambda_factor(brand_id, new_lambda)
                
                logger.info(f"Updated metrics for brand {brand_id}: "
                            f"ROAS={current_roas:.2f}/{target_roas:.2f}, "
                            f"throttle={throttle_factor:.2f}, lambda={new_lambda:.2f}")
        
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    async def reset_daily_budgets(self, db: Session) -> None:
        """
        Reset daily budgets for all brands.
        
        This should be called at the start of each day to reset spent amounts.
        
        Args:
            db: Database session
        """
        try:
            # Get all brands with strategies
            brands = db.query(BrandStrategy.brand_id).distinct().all()
            
            for brand_record in brands:
                brand_id = brand_record[0]
                
                # Get current ledger
                ledger = await self.get_brand_ledger(brand_id)
                
                # Reset spent budget
                await self.update_brand_ledger(brand_id, {
                    "spent_budget": 0.0
                })
                
                logger.info(f"Reset daily budget for brand {brand_id}")
        
        except Exception as e:
            logger.error(f"Error resetting daily budgets: {e}")

# Singleton instance
_optimizer = None

def get_portfolio_optimizer(redis_pool=None) -> PortfolioOptimizer:
    """
    Get or create the portfolio optimizer singleton.
    
    Args:
        redis_pool: Optional Redis connection pool
        
    Returns:
        PortfolioOptimizer instance
    """
    global _optimizer
    if _optimizer is None:
        _optimizer = PortfolioOptimizer(redis_pool)
    return _optimizer