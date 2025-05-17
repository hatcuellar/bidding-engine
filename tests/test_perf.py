import pytest
import json
import asyncio
from pytest_benchmark.fixture import BenchmarkFixture

from bidding_engine import bidding_engine
from utils.normalize import normalize_bid_to_impression_value
from utils.beta_posterior import beta_posterior
from utils.quality_factors import apply_quality_factors


@pytest.fixture
def sample_bid_request():
    """Sample bid request fixture for testing."""
    return {
        "brand_id": 123,
        "bid_amount": 10.0,
        "bid_type": "CPC",
        "ad_slot": {
            "id": 456,
            "width": 300,
            "height": 250,
            "position": 3,
            "page": {
                "url": "https://example.com/article",
                "category": "news",
                "is_mobile": False
            }
        }
    }


@pytest.mark.asyncio
async def test_bid_processing_performance(benchmark: BenchmarkFixture, sample_bid_request):
    """Test the performance of the bid processing pipeline."""
    # Define the async function to benchmark
    async def process_bids():
        results = []
        for _ in range(100):  # Process 100 bids
            result = await bidding_engine.process_bid(sample_bid_request)
            results.append(result)
        return results
    
    # Use benchmark to measure the performance
    result = await benchmark.pedantic(process_bids, iterations=5, rounds=5)
    
    # Verify results are as expected
    assert len(result) == 100
    assert all(isinstance(r, dict) for r in result)
    assert all("final_bid_value" in r for r in result)
    
    # Check performance against threshold (fail if > 25ms per bid)
    # The benchmark measures the total time, so we divide by 100
    max_allowed_time_per_bid_ms = 25
    assert benchmark.stats.stats.mean < (max_allowed_time_per_bid_ms * 100) / 1000


def test_normalization_performance(benchmark: BenchmarkFixture):
    """Test the performance of bid normalization."""
    def normalize_multiple_bids():
        results = []
        # Test different bid types
        bid_types = ["CPM", "CPC", "CPA"]
        for _ in range(1000):
            for bid_type in bid_types:
                result = normalize_bid_to_impression_value(
                    bid_amount=5.0,
                    bid_type=bid_type,
                    ctr=0.02,
                    cvr=0.05
                )
                results.append(result)
        return results
    
    results = benchmark(normalize_multiple_bids)
    assert len(results) == 3000  # 1000 iterations * 3 bid types
    
    # Verify correct normalization for each bid type
    # Take the last 3 results (one of each type)
    cpm_result = normalize_bid_to_impression_value(5.0, "CPM", 0.02, 0.05)
    cpc_result = normalize_bid_to_impression_value(5.0, "CPC", 0.02, 0.05)
    cpa_result = normalize_bid_to_impression_value(5.0, "CPA", 0.02, 0.05)
    
    assert cpm_result == 5.0
    assert cpc_result == 5.0 * 0.02 * 1000
    assert cpa_result == 5.0 * 0.02 * 0.05 * 1000


def test_beta_posterior_performance(benchmark: BenchmarkFixture):
    """Test the performance of beta posterior calculation."""
    def calculate_multiple_posteriors():
        results = []
        for clicks in range(0, 100):
            for imps in range(100, 1100, 100):
                result = beta_posterior(clicks, imps)
                results.append(result)
        return results
    
    results = benchmark(calculate_multiple_posteriors)
    assert len(results) == 1000  # 100 clicks * 10 impression values
    
    # Verify some key calculations
    assert beta_posterior(0, 100) < beta_posterior(10, 100)
    assert beta_posterior(10, 100) > beta_posterior(10, 1000)


@pytest.mark.asyncio
async def test_quality_factors_performance(benchmark: BenchmarkFixture):
    """Test the performance of quality factor application."""
    sample_ad_slot = {
        "id": 789,
        "width": 728,
        "height": 90,
        "position": 1,
        "page": {
            "category": "sports",
            "is_mobile": True
        }
    }
    
    # Define the async function to benchmark
    async def apply_quality_multiple_times():
        results = []
        for base_value in range(1, 101):
            result = await apply_quality_factors(float(base_value), sample_ad_slot)
            results.append(result)
        return results
    
    # Use benchmark to measure the performance
    results = await benchmark.pedantic(apply_quality_multiple_times, iterations=5, rounds=3)
    
    assert len(results) == 100
    # Ensure quality factors are in a reasonable range
    assert all(r > 0 for r in results)
    # Quality factors should modify the original values
    assert not all(abs(results[i] - (i+1)) < 0.001 for i in range(100))
