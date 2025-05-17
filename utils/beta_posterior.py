"""
Beta-posterior smoothing for CTR/CVR predictions.

This module provides functions for applying Bayesian smoothing to click-through rates
and conversion rates based on the beta-binomial model. This approach helps avoid
overconfidence in rates estimated from small sample sizes.
"""

import numpy as np
from typing import Tuple, Optional

def beta_posterior_mean(
    successes: int, 
    trials: int, 
    alpha_prior: float = 1.0, 
    beta_prior: float = 10.0
) -> float:
    """
    Calculate the mean of the beta posterior distribution.
    
    This implements Bayesian smoothing for rates (like CTR, CVR) using a beta-binomial model.
    The approach helps avoid extreme estimates from small sample sizes.
    
    Args:
        successes: Number of successes (e.g., clicks, conversions)
        trials: Number of trials (e.g., impressions, clicks)
        alpha_prior: Prior alpha parameter (default: 1.0)
        beta_prior: Prior beta parameter (default: 10.0)
        
    Returns:
        Posterior mean estimate of the rate
    """
    # Avoid division by zero
    if trials == 0:
        return alpha_prior / (alpha_prior + beta_prior)
    
    # Calculate posterior parameters
    alpha_posterior = alpha_prior + successes
    beta_posterior = beta_prior + (trials - successes)
    
    # Return posterior mean
    return alpha_posterior / (alpha_posterior + beta_posterior)

def beta_posterior_params(
    successes: int, 
    trials: int, 
    alpha_prior: float = 1.0, 
    beta_prior: float = 10.0
) -> Tuple[float, float]:
    """
    Calculate the parameters of the beta posterior distribution.
    
    Args:
        successes: Number of successes (e.g., clicks, conversions)
        trials: Number of trials (e.g., impressions, clicks)
        alpha_prior: Prior alpha parameter (default: 1.0)
        beta_prior: Prior beta parameter (default: 10.0)
        
    Returns:
        Tuple of (alpha_posterior, beta_posterior)
    """
    alpha_posterior = alpha_prior + successes
    beta_posterior = beta_prior + (trials - successes)
    return alpha_posterior, beta_posterior

def beta_posterior_interval(
    successes: int, 
    trials: int, 
    confidence: float = 0.95, 
    alpha_prior: float = 1.0, 
    beta_prior: float = 10.0
) -> Tuple[float, float]:
    """
    Calculate credible interval for the rate based on beta posterior.
    
    Args:
        successes: Number of successes (e.g., clicks, conversions)
        trials: Number of trials (e.g., impressions, clicks)
        confidence: Confidence level (default: 0.95 for 95% interval)
        alpha_prior: Prior alpha parameter (default: 1.0)
        beta_prior: Prior beta parameter (default: 10.0)
        
    Returns:
        Tuple of (lower_bound, upper_bound) for the credible interval
    """
    from scipy import stats
    
    # Calculate posterior parameters
    alpha_posterior, beta_posterior = beta_posterior_params(
        successes, trials, alpha_prior, beta_prior
    )
    
    # Calculate credible interval
    lower_percentile = (1 - confidence) / 2
    upper_percentile = 1 - lower_percentile
    
    lower_bound = stats.beta.ppf(lower_percentile, alpha_posterior, beta_posterior)
    upper_bound = stats.beta.ppf(upper_percentile, alpha_posterior, beta_posterior)
    
    return lower_bound, upper_bound

def get_smoothed_rates(
    clicks: int,
    impressions: int,
    conversions: int,
    ctr_prior: Optional[Tuple[float, float]] = None,
    cvr_prior: Optional[Tuple[float, float]] = None
) -> Tuple[float, float]:
    """
    Get beta-posterior smoothed estimates for CTR and CVR.
    
    Args:
        clicks: Number of clicks
        impressions: Number of impressions
        conversions: Number of conversions
        ctr_prior: Tuple of (alpha, beta) for CTR prior (default: (1, 10))
        cvr_prior: Tuple of (alpha, beta) for CVR prior (default: (1, 20))
        
    Returns:
        Tuple of (smoothed_ctr, smoothed_cvr)
    """
    # Default priors
    if ctr_prior is None:
        ctr_prior = (1.0, 10.0)  # Expect ~9% CTR as prior
    
    if cvr_prior is None:
        cvr_prior = (1.0, 20.0)  # Expect ~5% CVR as prior
    
    # Apply beta-posterior smoothing
    smoothed_ctr = beta_posterior_mean(
        clicks, impressions, ctr_prior[0], ctr_prior[1]
    )
    
    # For CVR, use clicks as the denominator
    # If no clicks, use the prior mean
    if clicks == 0:
        smoothed_cvr = cvr_prior[0] / (cvr_prior[0] + cvr_prior[1])
    else:
        smoothed_cvr = beta_posterior_mean(
            conversions, clicks, cvr_prior[0], cvr_prior[1]
        )
    
    return smoothed_ctr, smoothed_cvr