import os
import json
import logging
from typing import Optional, Any, Dict, List
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Get Redis URL from environment variable with fallback
REDIS_URL = os.getenv("REDIS_URL")
redis_pool = None

async def initialize_redis_pool():
    """
    Initialize the Redis connection pool.
    Should be called during application startup.
    """
    global redis_pool
    
    if redis_pool is not None:
        return  # Already initialized
        
    if REDIS_URL:
        try:
            redis_pool = await aioredis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection pool: {e}")
            redis_pool = None
    else:
        logger.warning("REDIS_URL not set - feature caching disabled")
        redis_pool = None

async def close_redis_pool():
    """
    Close the Redis connection pool.
    Should be called during application shutdown.
    """
    global redis_pool
    
    if redis_pool is not None:
        await redis_pool.close()
        redis_pool = None
        logger.info("Redis connection pool closed")

async def get_redis_client():
    """
    Get Redis client from the connection pool.
    
    Returns:
        Redis client or None if pool is not initialized
    """
    global redis_pool
    
    if redis_pool is None and REDIS_URL:
        # Lazy initialization if not done during startup
        await initialize_redis_pool()
            
    return redis_pool


async def get_cached_feature(key: str) -> Optional[str]:
    """
    Get a cached feature value from Redis.
    
    Args:
        key: Cache key to retrieve
        
    Returns:
        Cached value or None if not found/error
    """
    redis = await get_redis_client()
    if not redis:
        return None
    
    try:
        return await redis.get(key)
    except Exception as e:
        logger.error(f"Redis get error for key {key}: {e}")
        return None


async def set_cached_feature(key: str, value: str, ttl: int = 86400) -> bool:
    """
    Store a feature value in Redis cache.
    
    Args:
        key: Cache key
        value: Value to store
        ttl: Time-to-live in seconds (default 24 hours)
        
    Returns:
        True if successful, False otherwise
    """
    redis = await get_redis_client()
    if not redis:
        return False
    
    try:
        await redis.set(key, value, ex=ttl)
        return True
    except Exception as e:
        logger.error(f"Redis set error for key {key}: {e}")
        return False


async def cache_model_coefficients(model_name: str, coefficients: Dict[str, Any]) -> bool:
    """
    Cache model coefficients in Redis.
    
    Args:
        model_name: Name/identifier of the model
        coefficients: Dictionary of model coefficients
        
    Returns:
        True if successful, False otherwise
    """
    key = f"model:{model_name}:coefficients"
    try:
        value = json.dumps(coefficients)
        return await set_cached_feature(key, value)
    except Exception as e:
        logger.error(f"Error caching model coefficients: {e}")
        return False


async def get_model_coefficients(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Get cached model coefficients from Redis.
    
    Args:
        model_name: Name/identifier of the model
        
    Returns:
        Dictionary of coefficients or None if not found/error
    """
    key = f"model:{model_name}:coefficients"
    try:
        value = await get_cached_feature(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Error retrieving model coefficients: {e}")
        return None


async def cache_performance_metrics(brand_id: int, ad_slot_id: int, metrics: Dict[str, float], ttl: int = 3600) -> bool:
    """
    Cache performance metrics for a brand-slot combination.
    
    Args:
        brand_id: Brand identifier
        ad_slot_id: Ad slot identifier
        metrics: Dictionary of performance metrics (ctr, cvr, etc.)
        ttl: Time-to-live in seconds (default 1 hour)
        
    Returns:
        True if successful, False otherwise
    """
    key = f"perf:{brand_id}:{ad_slot_id}"
    try:
        value = json.dumps(metrics)
        return await set_cached_feature(key, value, ttl=ttl)
    except Exception as e:
        logger.error(f"Error caching performance metrics: {e}")
        return False


async def get_performance_metrics(brand_id: int, ad_slot_id: int) -> Optional[Dict[str, float]]:
    """
    Get cached performance metrics for a brand-slot combination.
    
    Args:
        brand_id: Brand identifier
        ad_slot_id: Ad slot identifier
        
    Returns:
        Dictionary of metrics or None if not found/error
    """
    key = f"perf:{brand_id}:{ad_slot_id}"
    try:
        value = await get_cached_feature(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Error retrieving performance metrics: {e}")
        return None


async def cache_batch_features(keys_values: Dict[str, str], ttl: int = 86400) -> List[bool]:
    """
    Cache multiple features in a batch operation.
    
    Args:
        keys_values: Dictionary mapping keys to values
        ttl: Time-to-live in seconds (default 24 hours)
        
    Returns:
        List of success flags (True/False) for each key
    """
    redis = await get_redis_client()
    if not redis:
        return [False] * len(keys_values)
    
    results = []
    for key, value in keys_values.items():
        try:
            success = await redis.set(key, value, ex=ttl)
            results.append(success)
        except Exception as e:
            logger.error(f"Redis batch set error for key {key}: {e}")
            results.append(False)
    
    return results
