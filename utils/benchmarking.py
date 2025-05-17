"""
Performance benchmarking utilities for the bidding engine.

This module provides functions for measuring and recording performance metrics
of various components of the bidding engine.
"""

import time
import logging
import json
import asyncio
import statistics
from typing import Dict, Any, List, Callable, Awaitable, Optional, Tuple
from datetime import datetime

from utils.redis_cache import set_cached_dict, get_cached_dict

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Utility class for tracking performance metrics"""
    
    def __init__(self):
        """Initialize the performance tracker"""
        self.metrics = {}
        
    async def record_timing(self, operation: str, duration_ms: float, 
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record timing for an operation.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            metadata: Additional contextual information
        """
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        # Add the timing with timestamp and metadata
        self.metrics[operation].append({
            'timestamp': datetime.utcnow().isoformat(),
            'duration_ms': duration_ms,
            'metadata': metadata or {}
        })
        
        # Keep only the last 1000 entries per operation
        if len(self.metrics[operation]) > 1000:
            self.metrics[operation] = self.metrics[operation][-1000:]
        
        # Async write to Redis cache
        await self._update_cache(operation)
    
    async def _update_cache(self, operation: str) -> None:
        """Update Redis cache with the latest metrics for an operation"""
        try:
            cache_key = f"perf_metrics:{operation}"
            summary = self.get_summary(operation)
            
            if summary:
                await set_cached_dict(cache_key, summary, ttl=3600)  # 1 hour TTL
        except Exception as e:
            logger.error(f"Failed to update performance cache: {e}")
    
    def get_summary(self, operation: str) -> Dict[str, Any]:
        """
        Get summary statistics for an operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Dictionary with summary statistics
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return {}
        
        durations = [entry['duration_ms'] for entry in self.metrics[operation]]
        
        return {
            'operation': operation,
            'count': len(durations),
            'min_ms': min(durations),
            'max_ms': max(durations),
            'avg_ms': statistics.mean(durations),
            'median_ms': statistics.median(durations),
            'p95_ms': self._percentile(durations, 95),
            'p99_ms': self._percentile(durations, 99),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """
        Calculate percentile of a list of values.
        
        Args:
            data: List of values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not data:
            return 0
        
        sorted_data = sorted(data)
        idx = max(0, int(len(sorted_data) * percentile / 100) - 1)
        return sorted_data[idx]
    
    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary statistics for all operations.
        
        Returns:
            Dictionary mapping operation names to their summary statistics
        """
        return {op: self.get_summary(op) for op in self.metrics.keys()}
    
    async def load_from_cache(self) -> None:
        """Load metrics from Redis cache"""
        try:
            operations = await get_cached_dict("perf_metrics:operations")
            if not operations or not isinstance(operations, dict):
                return
            
            for operation in operations.get('names', []):
                cache_key = f"perf_metrics:{operation}"
                cached_data = await get_cached_dict(cache_key)
                
                if cached_data and 'raw_metrics' in cached_data:
                    self.metrics[operation] = cached_data['raw_metrics']
        except Exception as e:
            logger.error(f"Failed to load performance metrics from cache: {e}")

# Singleton instance
performance_tracker = PerformanceTracker()

async def timed_execution(operation: str, func: Callable[..., Awaitable], 
                         *args, **kwargs) -> Tuple[Any, float]:
    """
    Measure execution time of an async function.
    
    Args:
        operation: Name of the operation
        func: Async function to time
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Tuple of (function result, duration in milliseconds)
    """
    start_time = time.time()
    result = await func(*args, **kwargs)
    duration_ms = (time.time() - start_time) * 1000
    
    # Record the timing asynchronously
    metadata = kwargs.get('metadata', {})
    asyncio.create_task(performance_tracker.record_timing(operation, duration_ms, metadata))
    
    return result, duration_ms

def sync_timed_execution(operation: str, func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """
    Measure execution time of a synchronous function.
    
    Args:
        operation: Name of the operation
        func: Synchronous function to time
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Tuple of (function result, duration in milliseconds)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    duration_ms = (time.time() - start_time) * 1000
    
    # Create an async task to record the timing
    metadata = kwargs.get('metadata', {})
    
    async def record():
        await performance_tracker.record_timing(operation, duration_ms, metadata)
    
    asyncio.create_task(record())
    
    return result, duration_ms

async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get all performance metrics.
    
    Returns:
        Dictionary with all performance metrics
    """
    return {
        'metrics': performance_tracker.get_all_summaries(),
        'timestamp': datetime.utcnow().isoformat()
    }