from typing import Optional


def normalize_bid_to_impression_value(
    bid_amount: float,
    bid_type: str,
    ctr: Optional[float] = None,
    cvr: Optional[float] = None
) -> float:
    """
    Normalize bid to an impression value (CPM equivalent) based on bid type.

    Args:
        bid_amount: The original bid amount
        bid_type: The bid type (CPA, CPC, CPM)
        ctr: Click-through rate (for CPC and CPA bids)
        cvr: Conversion rate (for CPA bids)

    Returns:
        Normalized bid value in CPM terms
    """
    # Default values if not provided
    ctr = ctr or 0.01  # 1% default CTR
    cvr = cvr or 0.03  # 3% default CVR

    # Normalize based on bid type
    if bid_type.upper() == "CPM":
        # CPM is already in impression terms
        return bid_amount
    elif bid_type.upper() == "CPC":
        # CPC needs to be multiplied by CTR to get CPM
        # CPC * CTR * 1000 = value per 1000 impressions
        return bid_amount * ctr * 1000
    elif bid_type.upper() == "CPA":
        # CPA needs to be multiplied by CTR and CVR to get CPM
        # CPA * CTR * CVR * 1000 = value per 1000 impressions
        return bid_amount * ctr * cvr * 1000
    else:
        # Unknown bid type, return original amount
        return bid_amount
