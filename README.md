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

### Calculate a Bid

```bash
curl -X POST "http://localhost:8000/api/bid/calculate" \
  -H "Content-Type: application/json" \
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