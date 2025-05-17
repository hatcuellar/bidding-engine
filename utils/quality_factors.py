import os
import logging
import json
from typing import Dict, Any, Optional
import xgboost as xgb
import numpy as np
from .redis_cache import get_cached_feature, set_cached_feature

logger = logging.getLogger(__name__)

# Path to XGBoost model file
MODEL_PATH = os.getenv("QUALITY_MODEL_PATH", "models/quality_model.json")

# Cache for the loaded model
_model_cache = None


async def load_xgboost_model() -> Optional[xgb.Booster]:
    """
    Load XGBoost model for quality factor prediction.
    
    Returns:
        Loaded XGBoost model or None if not found/error
    """
    global _model_cache
    
    # Return cached model if available
    if _model_cache is not None:
        return _model_cache
    
    try:
        # Try to load model from file
        if os.path.exists(MODEL_PATH):
            model = xgb.Booster()
            model.load_model(MODEL_PATH)
            _model_cache = model
            logger.info(f"XGBoost model loaded from {MODEL_PATH}")
            return model
    except Exception as e:
        logger.error(f"Failed to load XGBoost model: {e}")
    
    logger.warning("XGBoost model not available, will use fallback mean quality")
    return None


async def extract_features(ad_slot: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract features from ad slot information for quality prediction.
    
    Args:
        ad_slot: Dictionary with ad slot information
        
    Returns:
        Dictionary of feature name to feature value
    """
    features = {}
    
    # Basic slot features
    features["width"] = ad_slot.get("width", 0)
    features["height"] = ad_slot.get("height", 0)
    features["position"] = ad_slot.get("position", 0)
    
    # Page features
    page = ad_slot.get("page", {})
    features["page_category"] = hash(page.get("category", "")) % 100  # Simple category hashing
    features["is_mobile"] = 1 if page.get("is_mobile", False) else 0
    
    # Calculate derived features
    features["area"] = features["width"] * features["height"]
    features["aspect_ratio"] = features["width"] / max(1, features["height"])
    
    return features


async def get_placement_score(slot_id: int) -> float:
    """
    Get the quality score for a placement from cache or calculate it.
    
    Args:
        slot_id: Ad slot identifier
        
    Returns:
        Quality score for the placement
    """
    # Try to get from cache first
    cache_key = f"placement_score:{slot_id}"
    cached_score = await get_cached_feature(cache_key)
    
    if cached_score:
        try:
            return float(cached_score)
        except (ValueError, TypeError):
            logger.warning(f"Invalid cached placement score for slot {slot_id}")
    
    # Default score if not in cache
    return 1.0


async def apply_quality_factors(base_value: float, ad_slot: Dict[str, Any]) -> float:
    """
    Apply quality factors to the base bid value.
    
    This function will:
    1. Try to use XGBoost model if available
    2. Fall back to simpler calculation if model unavailable
    
    Args:
        base_value: Base bid value to adjust
        ad_slot: Information about the ad placement
        
    Returns:
        Adjusted bid value after applying quality factors
    """
    slot_id = ad_slot.get("id", 0)
    
    # Get placement score from cache
    placement_score = await get_placement_score(slot_id)
    
    # Try to load the model
    model = await load_xgboost_model()
    
    if model is not None:
        try:
            # Extract features from ad slot
            features = await extract_features(ad_slot)
            
            # Convert to DMatrix
            feature_array = np.array([[v for k, v in sorted(features.items())]])
            feature_names = [k for k, v in sorted(features.items())]
            dmatrix = xgb.DMatrix(feature_array, feature_names=feature_names)
            
            # Predict quality factor
            quality_factor = float(model.predict(dmatrix)[0])
            
            # Apply a sigmoid normalization to keep values reasonable
            quality_factor = 1.0 / (1.0 + np.exp(-quality_factor))
            
            # Scale to a reasonable range (0.5 to 2.0)
            quality_factor = 0.5 + quality_factor * 1.5
            
            logger.debug(f"Model-based quality factor: {quality_factor}")
            
        except Exception as e:
            logger.error(f"Error predicting quality factor with model: {e}")
            quality_factor = 1.0  # Default on error
    else:
        # Fallback calculation if model isn't available
        # Simple heuristic based on placement score and position
        position = ad_slot.get("position", 5)
        position_factor = max(0.5, min(1.5, (10 - position) / 5))
        
        quality_factor = placement_score * position_factor
        
        logger.debug(f"Fallback quality factor: {quality_factor}")
    
    # Apply quality factor to base value
    adjusted_value = base_value * quality_factor
    
    return adjusted_value
