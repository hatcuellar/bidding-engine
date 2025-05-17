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
            
    async def compute_optimal_lambda(self, brand_id: int, target_roas: float, db: Session) -> float:
        """
        Compute the optimal lambda factor for a brand based on target ROAS.
        
        Lambda is computed using the Lagrangian formula:
        λ = (target_roas * cost_sum - rev_sum) / cost_sum
        
        Args:
            brand_id: Brand identifier
            target_roas: Target ROAS for the brand
            db: Database session
            
        Returns:
            Computed lambda value
        """
        try:
            # Get revenue and cost data for the past 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            query = text("""
            SELECT 
                SUM(revenue) as total_revenue,
                SUM(cost) as total_cost
            FROM 
                bid_history
            WHERE 
                brand_id = :brand_id AND
                bid_timestamp >= :start_date
            """)
            
            result = db.execute(query, {
                "brand_id": brand_id,
                "start_date": seven_days_ago
            })
            row = result.fetchone()
            
            if not row or not row.total_cost or row.total_cost < 1.0:
                # Not enough data, use default lambda
                logger.warning(f"Insufficient data to compute lambda for brand {brand_id}")
                return self.default_lambda
            
            total_revenue = row.total_revenue or 0.0
            total_cost = row.total_cost or 1.0  # Avoid division by zero
            
            # Compute lambda using Lagrangian formula
            # λ = (target_roas * cost_sum - rev_sum) / cost_sum
            lambda_value = (target_roas * total_cost - total_revenue) / total_cost
            
            # Ensure lambda is non-negative and within reasonable bounds
            lambda_value = max(0.1, min(10.0, lambda_value))
            
            logger.info(f"Computed optimal lambda for brand {brand_id}: {lambda_value:.4f} "
                       f"(target ROAS: {target_roas:.2f}, actual: {total_revenue / total_cost:.2f})")
            
            return lambda_value
            
        except Exception as e:
            logger.error(f"Error computing optimal lambda: {e}")
            return self.default_lambda
    
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
            # Get brand strategy from database to check budget caps
            strategy = None
            if db is not None:
                try:
                    from models import BrandStrategy
                    strategy = db.query(BrandStrategy).filter(
                        BrandStrategy.brand_id == brand_id,
                        BrandStrategy.is_active == True
                    ).first()
                except Exception as e:
                    logger.error(f"Error fetching brand strategy from DB: {e}")
                    
            # Check budget caps if we have strategy data
            if strategy:
                # Check if over total budget cap
                if strategy.spent_total + predicted_cost > strategy.total_cap:
                    logger.warning(f"Brand {brand_id} exceeded total budget cap - skipping bid")
                    return 0.0, 0.0  # No score, no throttle = skip bid
                
                # Check if over daily budget cap
                if strategy.spent_today + predicted_cost > strategy.daily_cap:
                    logger.warning(f"Brand {brand_id} exceeded daily budget cap - skipping bid")
                    return 0.0, 0.0  # No score, no throttle = skip bid
                
                # Update daily spend (in-memory update only, will be saved to DB later)
                strategy.spent_today += predicted_cost
                strategy.spent_total += predicted_cost
            
            # Get brand ledger and lambda factor
            ledger = await self.get_brand_ledger(brand_id)
            lambda_factor = await self.get_lambda_factor(brand_id)
            
            # Calculate bid score using lambda factor
            # Score = predicted_revenue - lambda * predicted_cost
            score = predicted_revenue - (lambda_factor * predicted_cost)
            
            # Apply throttle factor based on budget and ROAS constraints
            throttle_factor = ledger["throttle_factor"]
            
            # Check if over budget in Redis/memory ledger (fallback)
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
            
            # If we have the strategy with DB target_roas, use that instead
            if strategy and strategy.target_roas:
                target_roas = strategy.target_roas
            
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
            
            # Commit database updates for budget tracking if needed
            if db is not None and strategy is not None:
                try:
                    # Only update in the DB if the change is significant enough (>= $0.01)
                    # to avoid too many small updates
                    if predicted_cost >= 0.01:
                        db.commit()
                except Exception as e:
                    logger.error(f"Error updating budget in database: {e}")
                    db.rollback()
            
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
                
                # Compute optimal lambda using Lagrangian method
                optimal_lambda = await self.compute_optimal_lambda(brand_id, target_roas, db)
                
                # Update ledger and lambda
                await self.update_brand_ledger(brand_id, {
                    "current_roas": current_roas,
                    "target_roas": target_roas,
                    "throttle_factor": throttle_factor
                })
                
                await self.update_lambda_factor(brand_id, optimal_lambda)
                
                logger.info(f"Updated metrics for brand {brand_id}: "
                            f"ROAS={current_roas:.2f}/{target_roas:.2f}, "
                            f"throttle={throttle_factor:.2f}, lambda={optimal_lambda:.2f}")
        
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
            # Query database for all active brands
            brands = db.query(BrandStrategy).filter(BrandStrategy.is_active == True).all()
            
            now = datetime.utcnow()
            today = now.strftime("%Y-%m-%d")
            
            logger.info(f"Resetting daily budgets for {len(brands)} brands on {today}")
            
            for brand in brands:
                try:
                    # Track previous day's spending in logs for reporting
                    logger.info(f"Brand {brand.brand_id} spent ${brand.spent_today:.2f} yesterday " 
                               f"(total spent: ${brand.spent_total:.2f}, target: ${brand.total_cap:.2f})")
                    
                    # Reset daily spending
                    brand.spent_today = 0.0
                    
                    # Get yesterday's actual spending for reconciliation
                    yesterday_start = datetime.combine(now.date() - timedelta(days=1), time.min)
                    yesterday_end = datetime.combine(now.date(), time.min)
                    
                    query = text("""
                    SELECT SUM(cost) as actual_cost
                    FROM bid_history
                    WHERE brand_id = :brand_id
                      AND bid_timestamp >= :start_time
                      AND bid_timestamp < :end_time
                    """)
                    
                    result = db.execute(query, {
                        "brand_id": brand.brand_id,
                        "start_time": yesterday_start,
                        "end_time": yesterday_end
                    })
                    
                    row = result.fetchone()
                    
                    # Reconcile total spending with actual costs if available
                    if row and row.actual_cost is not None:
                        # Ensure accurate total spend tracking
                        actual_daily_spend = float(row.actual_cost)
                        logger.info(f"Brand {brand.brand_id} actual spend reconciliation: ${actual_daily_spend:.2f}")
                        
                        # Adjust the total spent to match actual spend if significantly different
                        if abs(brand.spent_total - actual_daily_spend) > 1.0:  # If more than $1 different
                            logger.warning(f"Budget reconciliation: Brand {brand.brand_id} "
                                          f"spent_total adjusted by ${actual_daily_spend - brand.spent_total:.2f}")
                            brand.spent_total = actual_daily_spend
                    
                    # Also reset spent budget in Redis/memory ledger
                    ledger = await self.get_brand_ledger(brand.brand_id)
                    await self.update_brand_ledger(brand.brand_id, {
                        "spent_budget": 0.0
                    })
                
                except Exception as e:
                    logger.error(f"Error resetting budget for brand {brand.brand_id}: {e}")
                    # Continue with other brands even if one fails
            
            # Commit all changes
            db.commit()
            logger.info(f"Successfully reset daily budgets for all brands")
            
        except Exception as e:
            logger.error(f"Error in daily budget reset: {e}")
            db.rollback()

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