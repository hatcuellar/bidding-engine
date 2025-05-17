"""
ROAS (Return on Ad Spend) prediction module using LightGBM.

This module handles loading, training, and prediction of ROAS models
to optimize bidding decisions based on historical performance data.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
import numpy as np
from datetime import datetime, timedelta
import xgboost as xgb
from sqlalchemy import func, and_, text
from sqlalchemy.orm import Session

from models import BidHistory

logger = logging.getLogger(__name__)

# Feature column names for the model
FEATURE_COLUMNS = [
    'brand_id',
    'ad_slot_id',
    'device_type',
    'day_of_week',
    'hour_bucket',
    'creative_type',
    'placement_score',
    'partner_id'
]

class ROASPredictor:
    """
    Handles ROAS prediction using LightGBM model.
    
    This class is responsible for training and prediction of ROAS for
    bidding decisions, using historical performance data.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the ROAS predictor.
        
        Args:
            model_path: Path to a saved model file (optional)
        """
        self.model = None
        self.model_path = model_path or os.getenv('ROAS_MODEL_PATH', 'models/roas_model.json')
        self.load_model()
    
    def load_model(self) -> bool:
        """
        Load the model from disk if available.
        
        Returns:
            bool: True if model was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.model_path):
                self.model = xgb.Booster()
                self.model.load_model(self.model_path)
                logger.info(f"ROAS model loaded from {self.model_path}")
                return True
            else:
                logger.warning(f"ROAS model file not found at {self.model_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading ROAS model: {e}")
            return False
    
    def prepare_features(self, data: Dict[str, Any]) -> np.ndarray:
        """
        Prepare features for prediction.
        
        Args:
            data: Dictionary containing bid request data
            
        Returns:
            np.ndarray: Feature array for model input
        """
        # Extract or default all required features
        features = []
        
        # Primary keys
        features.append(data.get('brand_id', 0))
        features.append(data.get('ad_slot_id', 0))
        
        # Get device type (default to 0 for unknown)
        features.append(data.get('device_type', 0))
        
        # Time features
        now = datetime.now()
        features.append(now.weekday())  # day of week (0-6)
        features.append(now.hour // 3)  # 3-hour buckets (0-7)
        
        # Creative type (default to 0 for unknown)
        features.append(data.get('creative_type', 0))
        
        # Placement score (quality score 0-100)
        features.append(data.get('placement_score', 50))
        
        # Partner ID
        features.append(data.get('partner_id', 0))
        
        return np.array([features], dtype=np.float32)
    
    def predict(self, data: Dict[str, Any]) -> float:
        """
        Predict expected ROAS for a bid request.
        
        Args:
            data: Dictionary containing bid request data
            
        Returns:
            float: Predicted value per impression
        """
        # Default fallback value if model not available
        default_vpi = 0.01  # 1 cent per impression as baseline
        
        if self.model is None:
            logger.warning("Model not loaded, using default VPI")
            return default_vpi
        
        try:
            # Prepare features
            features = self.prepare_features(data)
            
            # Make prediction
            dmatrix = xgb.DMatrix(features)
            prediction = self.model.predict(dmatrix)
            
            # Return the predicted value (first element in array)
            vpi = float(prediction[0])
            
            # Apply reasonability constraints
            vpi = max(0.001, min(10.0, vpi))  # Between 0.1 cent and $10
            
            logger.debug(f"Predicted VPI for brand_id={data.get('brand_id')}, "
                         f"ad_slot_id={data.get('ad_slot_id')}: {vpi:.4f}")
            
            return vpi
        except Exception as e:
            logger.error(f"Error in ROAS prediction: {e}")
            return default_vpi
    
    def train(self, db: Session) -> bool:
        """
        Train a new ROAS model using historical performance data.
        
        Args:
            db: Database session
            
        Returns:
            bool: True if training was successful, False otherwise
        """
        try:
            # Get training data from the past 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # Query historical data
            query = text("""
            SELECT 
                b.brand_id, 
                b.ad_slot_id, 
                COALESCE(b.device_type, 0) as device_type,
                DAYOFWEEK(b.bid_timestamp) as day_of_week,
                FLOOR(HOUR(b.bid_timestamp) / 3) as hour_bucket,
                COALESCE(b.creative_type, 0) as creative_type,
                COALESCE(b.placement_score, 50) as placement_score,
                COALESCE(b.partner_id, 0) as partner_id,
                COALESCE(SUM(b.revenue), 0) as total_revenue,
                COALESCE(SUM(b.cost), 0) as total_cost,
                COUNT(*) as impression_count
            FROM 
                bid_history b
            WHERE 
                b.bid_timestamp >= :start_date
            GROUP BY 
                b.brand_id, 
                b.ad_slot_id, 
                b.device_type,
                day_of_week,
                hour_bucket,
                b.creative_type,
                b.placement_score,
                b.partner_id
            HAVING
                impression_count >= 10  -- Minimum sample size
            """)
            
            result = db.execute(query, {"start_date": thirty_days_ago})
            rows = result.fetchall()
            
            if not rows:
                logger.warning("No training data available")
                return False
            
            # Prepare features and target
            X = []
            y = []
            weights = []
            
            for row in rows:
                features = [
                    row.brand_id,
                    row.ad_slot_id,
                    row.device_type,
                    row.day_of_week,
                    row.hour_bucket,
                    row.creative_type,
                    row.placement_score,
                    row.partner_id
                ]
                
                # Target is revenue per impression
                revenue_per_impression = row.total_revenue / row.impression_count
                
                X.append(features)
                y.append(revenue_per_impression)
                
                # Weight by impressions to favor higher-volume data points
                weights.append(min(row.impression_count, 1000))  # Cap at 1000 to avoid extreme weights
            
            # Convert to numpy arrays
            X_np = np.array(X, dtype=np.float32)
            y_np = np.array(y, dtype=np.float32)
            w_np = np.array(weights, dtype=np.float32)
            
            # Create DMatrix for XGBoost
            dtrain = xgb.DMatrix(X_np, label=y_np, weight=w_np, feature_names=FEATURE_COLUMNS)
            
            # Set parameters
            params = {
                'objective': 'reg:squarederror',
                'eval_metric': 'rmse',
                'eta': 0.1,
                'max_depth': 6,
                'min_child_weight': 1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'tree_method': 'hist',  # Faster training
            }
            
            # Train model
            logger.info(f"Training ROAS model with {len(X)} samples")
            self.model = xgb.train(
                params,
                dtrain,
                num_boost_round=100,
                verbose_eval=False
            )
            
            # Save model
            self.model.save_model(self.model_path)
            logger.info(f"ROAS model saved to {self.model_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training ROAS model: {e}")
            return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from the trained model.
        
        Returns:
            Dict mapping feature names to importance scores
        """
        if self.model is None:
            return {}
        
        try:
            importance = self.model.get_score(importance_type='gain')
            return importance
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}

# Singleton instance
_predictor = None

def get_roas_predictor() -> ROASPredictor:
    """
    Get or create the ROAS predictor singleton.
    
    Returns:
        ROASPredictor instance
    """
    global _predictor
    if _predictor is None:
        _predictor = ROASPredictor()
    return _predictor