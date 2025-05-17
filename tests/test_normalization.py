import pytest
from hypothesis import given, strategies as st

from utils.normalize import normalize_bid_to_impression_value
from utils.beta_posterior import beta_posterior


def test_normalize_bid_cpm():
    """Test normalization of CPM bids (should pass through unchanged)."""
    bid_amount = 5.0
    result = normalize_bid_to_impression_value(bid_amount, "CPM")
    assert result == bid_amount


def test_normalize_bid_cpc():
    """Test normalization of CPC bids."""
    bid_amount = 1.0
    ctr = 0.02  # 2% CTR
    result = normalize_bid_to_impression_value(bid_amount, "CPC", ctr)
    expected = bid_amount * ctr * 1000  # $1 CPC * 0.02 CTR * 1000 = $20 CPM
    assert result == expected


def test_normalize_bid_cpa():
    """Test normalization of CPA bids."""
    bid_amount = 50.0
    ctr = 0.01  # 1% CTR
    cvr = 0.05  # 5% CVR
    result = normalize_bid_to_impression_value(bid_amount, "CPA", ctr, cvr)
    expected = bid_amount * ctr * cvr * 1000  # $50 CPA * 0.01 CTR * 0.05 CVR * 1000 = $25 CPM
    assert result == expected


def test_normalize_default_values():
    """Test normalization with default CTR/CVR values."""
    bid_amount = 2.0
    # Using default values (0.01 CTR, 0.03 CVR)
    cpc_result = normalize_bid_to_impression_value(bid_amount, "CPC")
    cpa_result = normalize_bid_to_impression_value(bid_amount, "CPA")
    
    assert cpc_result == bid_amount * 0.01 * 1000
    assert cpa_result == bid_amount * 0.01 * 0.03 * 1000


def test_normalize_unknown_type():
    """Test handling of unknown bid types."""
    bid_amount = 3.0
    result = normalize_bid_to_impression_value(bid_amount, "UNKNOWN_TYPE")
    assert result == bid_amount  # Should return original amount unchanged


@given(
    bid_amount=st.floats(min_value=0.01, max_value=1000.0),
    ctr=st.floats(min_value=0.001, max_value=0.5),
    cvr=st.floats(min_value=0.001, max_value=0.5)
)
def test_normalize_property_based(bid_amount, ctr, cvr):
    """Property-based test for normalization functions."""
    # CPM normalization should be identity
    cpm_result = normalize_bid_to_impression_value(bid_amount, "CPM", ctr, cvr)
    assert cpm_result == bid_amount
    
    # CPC normalization should scale by CTR * 1000
    cpc_result = normalize_bid_to_impression_value(bid_amount, "CPC", ctr, cvr)
    assert cpc_result == pytest.approx(bid_amount * ctr * 1000)
    
    # CPA normalization should scale by CTR * CVR * 1000
    cpa_result = normalize_bid_to_impression_value(bid_amount, "CPA", ctr, cvr)
    assert cpa_result == pytest.approx(bid_amount * ctr * cvr * 1000)
    
    # Verify relative magnitudes: CPA <= CPC <= CPM (after normalization)
    # This holds when CVR <= 1.0, which is always true
    assert cpa_result <= cpc_result or pytest.approx(cpa_result) == cpc_result
    assert cpc_result <= cpm_result * 1000 or pytest.approx(cpc_result) == cpm_result * 1000


def test_beta_posterior_basic():
    """Test basic beta posterior calculation."""
    # Zero clicks should yield low probability
    assert beta_posterior(0, 100) < 0.1
    
    # Many clicks should yield high probability
    assert beta_posterior(90, 100) > 0.8
    
    # Default prior should be respected (a=3, b=97)
    expected = (5 + 3) / (100 + 3 + 97)
    assert beta_posterior(5, 100) == expected


@given(
    clicks=st.integers(min_value=0, max_value=10000),
    imps=st.integers(min_value=1, max_value=10000),
    a=st.integers(min_value=1, max_value=100),
    b=st.integers(min_value=1, max_value=100)
)
def test_beta_posterior_properties(clicks, imps, a, b):
    """Property-based test for beta posterior function."""
    # Result should always be between 0 and 1
    result = beta_posterior(clicks, imps, a, b)
    assert 0 <= result <= 1
    
    # More clicks with same impressions should increase the result
    if imps > 0 and clicks < imps:
        more_clicks = min(clicks + 1, imps)
        higher_result = beta_posterior(more_clicks, imps, a, b)
        assert result < higher_result
    
    # More impressions with same clicks should decrease the result
    if clicks < imps:
        more_imps = imps + 1
        lower_result = beta_posterior(clicks, more_imps, a, b)
        assert result > lower_result
