"""
Performance metrics API routes for the bidding engine.

This module provides endpoints for retrieving and analyzing performance metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.benchmarking import get_performance_metrics

router = APIRouter()

@router.get("/performance")
async def get_bidding_performance():
    """
    Get performance metrics for the bidding engine.
    
    Returns summary statistics and timing information for various
    components of the bidding engine.
    """
    try:
        metrics = await get_performance_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )

@router.get("/performance/{operation}")
async def get_operation_performance(operation: str):
    """
    Get performance metrics for a specific operation.
    
    Path parameters:
    - operation: Name of the operation (e.g., total_bid_processing, quality_factors)
    """
    try:
        metrics = await get_performance_metrics()
        if operation not in metrics['metrics']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No metrics found for operation: {operation}"
            )
        return {
            'operation': operation,
            'metrics': metrics['metrics'][operation],
            'timestamp': metrics['timestamp']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )