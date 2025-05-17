# Multi-Model Ad Bidding Engine

A high-performance FastAPI implementation of a multi-model ad bidding engine with advanced features.

## Features

- **Multi-Model Bid Normalization**: Supports CPA, CPC, and CPM bid models with normalization to common value-per-impression (VPI)
- **Beta-Posterior Smoothing**: Statistical approach for more accurate CTR/CVR predictions
- **ML-Powered Quality Factors**: XGBoost integration for predicting quality factors
- **Brand Strategy Management**: Custom bidding strategies per advertiser
- **Performance Monitoring**: Detailed performance metrics and benchmarking
- **Redis Caching**: Optimized performance with connection pooling
- **Database Migration**: Alembic-based schema versioning
- **API Documentation**: Interactive Swagger UI and detailed custom documentation

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Redis (optional, but recommended for production)

### Environment Setup

1. Copy the example environment file and configure:
   ```
   cp .env.example .env
   ```

2. Update the `.env` file with your database and Redis connection information.

### Installation

```bash
# Install dependencies
pip install -e .

# Run database migrations
alembic upgrade head
```

### Running the Application

```bash
# Development mode
bash start_fastapi.sh

# Or with explicit environment variables
ENV=development bash start_fastapi.sh
```

## API Documentation

- Interactive API docs: `/docs` 
- Detailed API guide: `/guide`
- OpenAPI schema: `/openapi.json`

## Usage Examples

### Authentication with JWT

Both partners (publishers) and brands (advertisers) use JWT for authentication.

#### Generate JWT Token for Partners

```python
import jwt
import datetime

# Generate a partner token (publisher)
partner_payload = {
    "sub": "partner_123",
    "partner_id": 123,
    "scope": "partner",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
}

partner_token = jwt.encode(
    partner_payload,
    "YOUR_SECRET_KEY",  # Use environment secret in production
    algorithm="HS256"
)

print(f"Partner JWT: {partner_token}")
```

#### Generate JWT Token for Brands

```python
import jwt
import datetime

# Generate a brand token (advertiser)
brand_payload = {
    "sub": "brand_456",
    "brand_id": 456,
    "scope": "brand",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
}

brand_token = jwt.encode(
    brand_payload,
    "YOUR_SECRET_KEY",  # Use environment secret in production
    algorithm="HS256"
)

print(f"Brand JWT: {brand_token}")
```

### Calculate a Bid

```bash
curl -X POST "http://localhost:8000/api/bid/calculate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "brand_id": 123,
    "bid_amount": 2.50,
    "bid_type": "CPC",
    "ad_slot": {
      "id": 456,
      "width": 300,
      "height": 250,
      "position": 1,
      "page": {
        "category": "news",
        "traffic_source": "direct"
      }
    }
  }'
```

### Update Brand Strategy

```bash
curl -X POST "http://localhost:8000/api/bid/strategy" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "brand_id": 123,
    "vpi_multiplier": 1.2,
    "priority": 2,
    "strategy_config": {
      "max_bid": 5.0,
      "min_bid": 0.5
    }
  }'
```

## Monitoring

- Health check: `/api/health/healthz`
- Performance metrics: `/api/metrics/performance`
- Prometheus metrics: `/metrics`

### Prometheus Metrics Reference

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `bids_by_type_total` | Counter | `bid_type` | Total number of bids processed by type (CPA, CPC, CPM) |
| `bid_values` | Histogram | `bid_type` | Distribution of bid values in $ units |
| `brand_lambda_values` | Histogram | `brand_id` | Distribution of λ values by brand (used in bid scoring) |
| `lambda_statistics` | Gauge | `stat_type` | Global λ statistics: mean, median, stddev, count |
| `roas_performance` | Histogram | `brand_id` | Distribution of ROAS values by brand |
| `http_requests_total` | Counter | `status`, `method`, `endpoint` | HTTP request count by status code, method, and endpoint |
| `http_request_duration_seconds` | Histogram | `status`, `method`, `endpoint` | HTTP request duration by status code, method, and endpoint |
| `requests_in_progress` | Gauge | `method`, `endpoint` | Current number of HTTP requests in progress |

For alerting, consider setting thresholds on the following metrics:
- `lambda_statistics{stat_type="stddev"}` > 1.0 (detecting high variance in λ values)
- `roas_performance{brand_id="X"}` < target (detecting underperforming brands)

## Docker Deployment

```bash
# Build the Docker image
docker build -t bidding-engine .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:password@host:port/db \
  -e REDIS_URL=redis://host:port/0 \
  bidding-engine
```

## Testing

```bash
# Run unit tests
pytest

# Run benchmarks
pytest tests/test_perf.py -v
```

## Contributing

1. Create a feature branch
2. Add tests for new features
3. Ensure all tests pass
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.