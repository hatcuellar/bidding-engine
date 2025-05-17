import os
import json
import logging
from typing import Optional, Any, Dict
import aioredis

logger = logging.getLogger(__name__)

# Get Redis URL from environment variable with fallback
REDIS_URL = os.getenv("REDIS_URL")
redis_client = None

async def get_redis_client():
    """
    Get or initialize Redis client.
    """
    global redis_client
    
    if redis_client is None:
        if REDIS_URL:
            try:
                redis_client = await aioredis.from_url(
                    REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Redis client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Redis client: {e}")
                return None
        else:
            logger.warning("REDIS_URL not set - feature caching disabled")
            return None
            
    return redis_client


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
