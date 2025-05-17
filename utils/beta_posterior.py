def beta_posterior(clicks: int, imps: int, a: int = 3, b: int = 97) -> float:
    """
    Calculate beta-posterior estimate for metrics like CTR/CVR with Bayesian smoothing.
    
    This approach is useful for handling cold-start problems and sparse data.
    The function uses a beta distribution with parameters a and b as priors.
    
    Args:
        clicks: Number of positive events (clicks or conversions)
        imps: Number of total events (impressions or clicks)
        a: Alpha parameter for beta prior (default 3)
        b: Beta parameter for beta prior (default 97)
    
    Returns:
        Smoothed estimate (clicks + a) / (imps + a + b)
    """
    # Ensure positive values
    clicks = max(0, clicks)
    imps = max(1, imps)  # Avoid division by zero
    
    # Calculate posterior mean
    return (clicks + a) / (imps + a + b)
