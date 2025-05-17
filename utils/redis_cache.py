"""
Redis caching utilities for the bidding engine.

This module provides functions for caching and retrieving data using Redis,
with connection pooling for better performance and reliability.
"""

import os
import logging
import json
from typing import Optional, Any, Dict

# Import redis with proper error handling
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global Redis connection pool
redis_pool = None

async def initialize_redis_pool() -> bool:
    """
    Initialize the Redis connection pool.
    
    Returns:
        True if successful, False otherwise
    """
    global redis_pool
    
    if not REDIS_AVAILABLE:
        logger.warning("Redis not available. Caching will be disabled.")
        return False
    
    # Get Redis URL from environment or use a default for local development
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    try:
        # Create connection pool
        redis_pool = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"Redis connection pool initialized: {redis_url}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Redis pool: {e}")
        redis_pool = None
        return False

async def close_redis_pool() -> None:
    """
    Close the Redis connection pool.
    """
    global redis_pool
    
    if redis_pool:
        try:
            await redis_pool.close()
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis pool: {e}")
        finally:
            redis_pool = None

async def get_cached_feature(key: str) -> Optional[str]:
    """
    Get a cached feature from Redis.
    
    Args:
        key: The cache key
        
    Returns:
        The cached value, or None if not found or error
    """
    if not redis_pool:
        return None
    
    try:
        # Get value from Redis
        value = await redis_pool.get(key)
        if value:
            logger.debug(f"Cache hit for key: {key}")
        return value
    except Exception as e:
        logger.error(f"Error getting cached feature {key}: {e}")
        return None

async def set_cached_feature(key: str, value: str, ttl: int = 3600) -> bool:
    """
    Set a cached feature in Redis.
    
    Args:
        key: The cache key
        value: The value to cache
        ttl: Time-to-live in seconds (default: 1 hour)
        
    Returns:
        True if successful, False otherwise
    """
    if not redis_pool:
        return False
    
    try:
        # Set value in Redis with TTL
        await redis_pool.set(key, value, ex=ttl)
        logger.debug(f"Cached feature {key} with TTL {ttl}s")
        return True
    except Exception as e:
        logger.error(f"Error caching feature {key}: {e}")
        return False

async def get_cached_dict(key: str) -> Optional[Dict[str, Any]]:
    """
    Get a cached JSON dictionary from Redis.
    
    Args:
        key: The cache key
        
    Returns:
        The cached dictionary, or None if not found or error
    """
    cached_str = await get_cached_feature(key)
    
    if cached_str:
        try:
            return json.loads(cached_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from cache key: {key}")
    
    return None

async def set_cached_dict(key: str, value_dict: Dict[str, Any], ttl: int = 3600) -> bool:
    """
    Set a cached JSON dictionary in Redis.
    
    Args:
        key: The cache key
        value_dict: The dictionary to cache
        ttl: Time-to-live in seconds (default: 1 hour)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        json_str = json.dumps(value_dict)
        return await set_cached_feature(key, json_str, ttl)
    except (TypeError, ValueError):
        logger.error(f"Failed to encode dictionary to JSON for cache key: {key}")
        return False