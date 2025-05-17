"""
XGBoost model for quality factor predictions.

This module provides functions for training and using XGBoost models
to predict quality factors based on ad slot characteristics, brand information,
and historical performance data.
"""

import os
import pickle
import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import xgboost as xgb

from utils.redis_cache import get_cached_feature, set_cached_feature

logger = logging.getLogger(__name__)

# Model path for persisting trained models
MODEL_PATH = "models/quality_factors_model.pkl"
FEATURE_NAMES = [
    # Ad slot features
    'ad_width', 'ad_height', 'ad_position', 'ad_area',
    # Page context features
    'is_mobile', 'is_app', 'page_category_news', 'page_category_finance',
    'page_category_entertainment', 'page_category_tech', 'page_category_other',
    # Brand features
    'brand_priority', 'brand_historical_ctr', 'brand_historical_cvr',
    # Time features
    'hour_of_day', 'day_of_week', 'is_weekend'
]

class QualityFactorModel:
    """XGBoost model for quality factor predictions"""
    
    def __init__(self, load_existing: bool = True):
        """
        Initialize the quality factor model.
        
        Args:
            load_existing: Whether to load an existing model if available
        """
        self.model = None
        
        if load_existing and os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info(f"Loaded existing quality factor model from {MODEL_PATH}")
            except Exception as e:
                logger.error(f"Failed to load existing model: {e}")
                self.model = None
        
        if self.model is None:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            
            # Initialize a new model with sensible defaults for online bidding
            self.model = xgb.XGBRegressor(
                n_estimators=100,      # Number of trees
                max_depth=5,           # Maximum tree depth
                learning_rate=0.1,     # Learning rate
                objective='reg:squarederror',  # Regression objective
                n_jobs=-1,             # Use all available cores
                random_state=42,       # For reproducibility
                tree_method='hist',    # Fast histogram-based algorithm
                early_stopping_rounds=10,  # For training
                subsample=0.8,         # Subsample ratio of training instances
                colsample_bytree=0.8   # Subsample ratio of columns
            )
            logger.info("Initialized new quality factor model")
            
            # Pre-train with some reasonable data if no trained model exists
            self._pretrain_model()
    
    def _pretrain_model(self):
        """
        Pre-train the model with synthetic data to have reasonable predictions
        even before real training data is available.
        """
        try:
            # Generate synthetic training data
            n_samples = 1000
            X, y = self._generate_synthetic_data(n_samples)
            
            # Train the model
            self.model.fit(X, y)
            
            # Save the pre-trained model
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump(self.model, f)
                
            logger.info(f"Pre-trained quality factor model with {n_samples} synthetic samples")
        except Exception as e:
            logger.error(f"Failed to pre-train model: {e}")
    
    def _generate_synthetic_data(self, n_samples: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic data for pre-training the model.
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            Tuple of (X, y) with features and target values
        """
        np.random.seed(42)  # For reproducibility
        
        # Generate feature matrix
        X = np.zeros((n_samples, len(FEATURE_NAMES)))
        
        # Ad dimensions (width, height)
        common_sizes = [
            (300, 250),  # Medium Rectangle
            (728, 90),   # Leaderboard
            (160, 600),  # Wide Skyscraper
            (320, 50),   # Mobile Banner
            (970, 250)   # Billboard
        ]
        
        for i in range(n_samples):
            # Random ad size
            size_idx = np.random.randint(0, len(common_sizes))
            width, height = common_sizes[size_idx]
            X[i, 0] = width
            X[i, 1] = height
            X[i, 3] = width * height  # Area
            
            # Random position (1-10, higher is further down the page)
            X[i, 2] = np.random.randint(1, 11)
            
            # Device type
            X[i, 4] = np.random.choice([0, 1], p=[0.6, 0.4])  # is_mobile
            X[i, 5] = np.random.choice([0, 1], p=[0.8, 0.2])  # is_app
            
            # Page category (one-hot encoded)
            category = np.random.choice([0, 1, 2, 3, 4], p=[0.2, 0.2, 0.2, 0.2, 0.2])
            for j in range(6, 11):
                X[i, j] = 1 if j - 6 == category else 0
            
            # Brand features
            X[i, 11] = np.random.randint(1, 6)  # brand_priority (1-5)
            X[i, 12] = np.random.beta(2, 20)    # brand_historical_ctr
            X[i, 13] = np.random.beta(1, 30)    # brand_historical_cvr
            
            # Time features
            X[i, 14] = np.random.randint(0, 24)  # hour_of_day
            day = np.random.randint(0, 7)        # day_of_week
            X[i, 15] = day
            X[i, 16] = 1 if day >= 5 else 0     # is_weekend
        
        # Generate target values (quality factors) based on feature relationships
        y = np.ones(n_samples)
        
        # Larger ads tend to have higher quality
        area_norm = (X[:, 3] - X[:, 3].min()) / (X[:, 3].max() - X[:, 3].min())
        y *= (0.8 + 0.4 * area_norm)
        
        # Higher positions (lower position numbers) have higher quality
        position_effect = 1.25 - 0.05 * X[:, 2]  # 1.25 for position 1, 0.75 for position 10
        y *= position_effect
        
        # Premium categories have higher quality
        category_effect = np.ones(n_samples)
        category_effect += 0.1 * X[:, 6]  # News
        category_effect += 0.1 * X[:, 7]  # Finance
        category_effect += 0.05 * X[:, 8] # Entertainment
        category_effect += 0.1 * X[:, 9]  # Tech
        y *= category_effect
        
        # Higher CTR/CVR leads to higher quality
        perf_effect = 1.0 + X[:, 12] * 2 + X[:, 13] * 3
        y *= perf_effect
        
        # Add random noise
        y *= np.random.normal(1.0, 0.1, n_samples)
        
        # Ensure reasonable range (0.5 to 2.0)
        y = np.clip(y, 0.5, 2.0)
        
        return X, y
    
    def predict_quality_factor(self, ad_slot: Dict[str, Any], brand_data: Dict[str, Any]) -> float:
        """
        Predict quality factor for a given ad slot and brand.
        
        Args:
            ad_slot: Ad slot information
            brand_data: Brand information
            
        Returns:
            Predicted quality factor
        """
        if self.model is None:
            # Default to 1.0 if no model is available
            return 1.0
        
        try:
            # Extract features from input data
            features = self._extract_features(ad_slot, brand_data)
            
            # Make prediction
            X = np.array([features])
            prediction = self.model.predict(X)[0]
            
            # Ensure prediction is within reasonable bounds
            prediction = max(0.5, min(2.0, prediction))
            
            logger.debug(f"Predicted quality factor: {prediction:.4f}")
            return float(prediction)
            
        except Exception as e:
            logger.error(f"Error predicting quality factor: {e}")
            return 1.0  # Default to neutral factor on error
    
    def _extract_features(self, ad_slot: Dict[str, Any], brand_data: Dict[str, Any]) -> List[float]:
        """
        Extract features from ad slot and brand data.
        
        Args:
            ad_slot: Ad slot information
            brand_data: Brand information
            
        Returns:
            List of features matching FEATURE_NAMES
        """
        from datetime import datetime
        
        # Initialize features with zeros
        features = [0.0] * len(FEATURE_NAMES)
        
        # Extract ad slot features
        features[0] = float(ad_slot.get("width", 0))
        features[1] = float(ad_slot.get("height", 0))
        features[2] = float(ad_slot.get("position", 0))
        features[3] = features[0] * features[1]  # Area
        
        # Extract page context features
        page_info = ad_slot.get("page", {})
        features[4] = 1.0 if page_info.get("is_mobile") else 0.0
        features[5] = 1.0 if page_info.get("is_app") else 0.0
        
        # Category one-hot encoding
        category = page_info.get("category", "").lower()
        features[6] = 1.0 if category == "news" else 0.0
        features[7] = 1.0 if category == "finance" else 0.0
        features[8] = 1.0 if category == "entertainment" else 0.0
        features[9] = 1.0 if category == "technology" else 0.0
        features[10] = 1.0 if category not in ["news", "finance", "entertainment", "technology"] else 0.0
        
        # Brand features
        features[11] = float(brand_data.get("priority", 1))
        features[12] = float(brand_data.get("historical_ctr", 0.01))
        features[13] = float(brand_data.get("historical_cvr", 0.03))
        
        # Time features
        now = datetime.now()
        features[14] = float(now.hour)
        features[15] = float(now.weekday())
        features[16] = 1.0 if now.weekday() >= 5 else 0.0
        
        return features
    
    def update_model(self, X: np.ndarray, y: np.ndarray) -> bool:
        """
        Update the model with new training data.
        
        Args:
            X: Feature matrix
            y: Target values
            
        Returns:
            True if successful, False otherwise
        """
        if X.shape[0] == 0 or X.shape[1] != len(FEATURE_NAMES):
            logger.error(f"Invalid training data shape: {X.shape}")
            return False
        
        try:
            # Update model with new data
            if self.model is None:
                # Initialize a new model
                self.model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    objective='reg:squarederror',
                    n_jobs=-1,
                    random_state=42,
                    tree_method='hist'
                )
                self.model.fit(X, y)
            else:
                # Incrementally update existing model
                self.model.fit(X, y, xgb_model=self.model)
            
            # Save updated model
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump(self.model, f)
                
            logger.info(f"Updated quality factor model with {X.shape[0]} samples")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update model: {e}")
            return False

# Singleton instance
quality_model = QualityFactorModel()

async def predict_quality_factor(ad_slot: Dict[str, Any], brand_id: int) -> float:
    """
    Predict quality factor for a given ad slot and brand.
    
    This function adds caching layer on top of the model.
    
    Args:
        ad_slot: Ad slot information
        brand_id: Brand identifier
        
    Returns:
        Predicted quality factor
    """
    # Create cache key using ad slot id and brand id
    slot_id = ad_slot.get("id", 0)
    cache_key = f"quality:{brand_id}:{slot_id}"
    
    # Try to get from cache
    cached = await get_cached_feature(cache_key)
    if cached:
        try:
            return float(cached)
        except (ValueError, TypeError):
            pass
    
    # Get brand data (in production, this would come from database)
    # For now, use some reasonable defaults with slight randomization
    import random
    priority = 1 + (brand_id % 5)  # 1-5 priority levels
    historical_ctr = 0.01 + (brand_id % 10) * 0.005  # 1% to 5.5% CTR
    historical_cvr = 0.02 + (brand_id % 8) * 0.005   # 2% to 5.5% CVR
    
    brand_data = {
        "id": brand_id,
        "priority": priority,
        "historical_ctr": historical_ctr,
        "historical_cvr": historical_cvr
    }
    
    # Predict using model
    quality_factor = quality_model.predict_quality_factor(ad_slot, brand_data)
    
    # Cache result
    await set_cached_feature(cache_key, str(quality_factor), ttl=3600)  # 1 hour TTL
    
    return quality_factor